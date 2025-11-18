"""Pinecone vector database client for storing embeddings."""

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

from ..base import BaseIntegrationClient, retry_on_failure
from config.settings import Settings

logger = logging.getLogger(__name__)


class PineconeClient(BaseIntegrationClient):
    """Client for interacting with Pinecone vector database."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None
    ):
        """
        Initialize Pinecone client.

        Args:
            api_key: Pinecone API key (from Settings if not provided)
            environment: Pinecone environment (from Settings if not provided)
            index_name: Index name (from Settings if not provided)
            namespace: Optional namespace for organizing vectors (from Settings if not provided)
        """
        super().__init__()
        self.api_key = api_key or Settings.PINECONE_API_KEY
        self.environment = environment or Settings.PINECONE_ENVIRONMENT
        self.index_name = index_name or Settings.PINECONE_INDEX_NAME
        self.namespace = namespace or Settings.PINECONE_NAMESPACE

        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        if not self.index_name:
            raise ValueError("Pinecone index name is required")

        self.pc = None  # Pinecone client instance
        self.index = None  # Pinecone index instance

    def connect(self) -> bool:
        """
        Establish connection to Pinecone.

        Returns:
            True if connection successful
        """
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.api_key)
            
            # Connect to the index
            if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
                self.logger.error(f"❌ Index '{self.index_name}' does not exist")
                self.logger.info("Available indexes: " + ", ".join([idx.name for idx in self.pc.list_indexes()]))
                return False
            
            self.index = self.pc.Index(self.index_name)
            
            # Test connection with health check
            if self.health_check():
                self._connected = True
                self.logger.info(f"✅ Connected to Pinecone index '{self.index_name}'")
                return True
            else:
                self.logger.error("❌ Pinecone health check failed")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Pinecone: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close connection to Pinecone.

        Returns:
            True if disconnection successful
        """
        try:
            # Pinecone doesn't require explicit disconnection
            self.index = None
            self.pc = None
            self._connected = False
            self.logger.info("Disconnected from Pinecone")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from Pinecone: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    def health_check(self) -> bool:
        """
        Check if Pinecone index is reachable and healthy.

        Returns:
            True if service is healthy
        """
        try:
            if not self.index:
                return False

            # Get index stats as health check
            stats = self.index.describe_index_stats()
            self.logger.debug(f"Index stats: {stats}")
            return True

        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone index.

        Args:
            vectors: List of vectors with 'id', 'values', and 'metadata'
            namespace: Optional namespace (uses default if not provided)
            batch_size: Number of vectors per batch

        Returns:
            Summary of upsert operation

        Raises:
            Exception: If upsert fails
        """
        if not self._connected or not self.index:
            raise RuntimeError("Not connected to Pinecone. Call connect() first.")

        target_namespace = namespace or self.namespace or ""

        try:
            self.logger.info(f"Upserting {len(vectors)} vectors to Pinecone index '{self.index_name}'...")
            if target_namespace:
                self.logger.info(f"   Using namespace: '{target_namespace}'")

            # Upsert in batches
            total_upserted = 0
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                # Format vectors for Pinecone
                formatted_vectors = []
                for vec in batch:
                    formatted_vectors.append({
                        "id": vec["id"],
                        "values": vec["values"],
                        "metadata": vec.get("metadata", {})
                    })
                
                # Upsert batch
                self.index.upsert(
                    vectors=formatted_vectors,
                    namespace=target_namespace
                )
                total_upserted += len(batch)
                self.logger.debug(f"   Upserted batch {i//batch_size + 1}: {len(batch)} vectors")

            self.logger.info(f"✅ Successfully upserted {total_upserted} vectors")
            return {
                "status": "success",
                "upserted_count": total_upserted,
                "namespace": target_namespace
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to upsert vectors: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def delete_vectors(
        self,
        vector_ids: Optional[List[str]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        delete_all: bool = False
    ) -> Dict[str, Any]:
        """
        Delete vectors from Pinecone index.

        Args:
            vector_ids: Optional list of vector IDs to delete
            filter_dict: Optional metadata filter for bulk deletion
            namespace: Optional namespace
            delete_all: If True, delete all vectors in namespace (use with caution!)

        Returns:
            Summary of delete operation

        Raises:
            Exception: If deletion fails
        """
        if not self._connected or not self.index:
            raise RuntimeError("Not connected to Pinecone. Call connect() first.")

        target_namespace = namespace or self.namespace or ""

        if not vector_ids and not filter_dict and not delete_all:
            raise ValueError("Must provide vector_ids, filter_dict, or delete_all=True")

        try:
            if delete_all:
                self.logger.warning(f"⚠️  Deleting ALL vectors from namespace '{target_namespace}'...")
                self.index.delete(delete_all=True, namespace=target_namespace)
                self.logger.info("✅ All vectors deleted")
                return {"status": "success", "operation": "delete_all"}
            
            elif vector_ids:
                self.logger.info(f"Deleting {len(vector_ids)} vectors by ID...")
                self.index.delete(ids=vector_ids, namespace=target_namespace)
                self.logger.info(f"✅ Successfully deleted {len(vector_ids)} vectors")
                return {"status": "success", "deleted_count": len(vector_ids)}
            
            elif filter_dict:
                self.logger.info(f"Deleting vectors matching filter...")
                self.index.delete(filter=filter_dict, namespace=target_namespace)
                self.logger.info("✅ Vectors deleted by filter")
                return {"status": "success", "operation": "delete_by_filter"}

        except Exception as e:
            self.logger.error(f"❌ Failed to delete vectors: {e}")
            raise

    def sync_documents(
        self,
        local_chunks: List[Dict[str, Any]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Synchronize local chunks with Pinecone index.
        Handles additions, updates, and deletions based on change_status.

        Args:
            local_chunks: List of chunks with 'id', 'embedding', 'content', 'metadata'
            namespace: Optional namespace
            batch_size: Number of vectors per batch

        Returns:
            Summary of sync operation with counts for added, updated, deleted
        """
        if not self._connected:
            raise RuntimeError("Not connected to Pinecone. Call connect() first.")

        target_namespace = namespace or self.namespace or ""
        
        self.logger.info(f"🔄 Starting document sync to Pinecone index '{self.index_name}'...")
        if target_namespace:
            self.logger.info(f"   Using namespace: '{target_namespace}'")
        self.logger.info(f"   Total local chunks: {len(local_chunks)}")

        # Categorize chunks by change status
        new_chunks = []
        updated_chunks = []
        unchanged_chunks = []
        
        for chunk in local_chunks:
            change_status = chunk.get("metadata", {}).get("change_status", "new")
            if change_status == "new":
                new_chunks.append(chunk)
            elif change_status == "updated":
                updated_chunks.append(chunk)
            else:
                unchanged_chunks.append(chunk)

        self.logger.info(f"   New chunks: {len(new_chunks)}")
        self.logger.info(f"   Updated chunks: {len(updated_chunks)}")
        self.logger.info(f"   Unchanged chunks: {len(unchanged_chunks)} (will be skipped)")

        results = {
            "total_chunks": len(local_chunks),
            "new_count": 0,
            "updated_count": 0,
            "unchanged_count": len(unchanged_chunks),
            "deleted_count": 0,
            "errors": []
        }

        try:
            # Upload new chunks
            if new_chunks:
                self.logger.info(f"📤 Uploading {len(new_chunks)} new chunks...")
                vectors = self._format_chunks_for_pinecone(new_chunks)
                try:
                    result = self.upsert_vectors(vectors, target_namespace, batch_size)
                    results["new_count"] = result["upserted_count"]
                except Exception as e:
                    error_msg = f"Failed to upload new chunks: {e}"
                    results["errors"].append(error_msg)
                    self.logger.error(f"   ❌ {error_msg}")

            # Handle updated chunks: delete old versions and upload new
            if updated_chunks:
                self.logger.info(f"🔄 Updating {len(updated_chunks)} chunks...")
                
                # Delete old versions by ID
                chunk_ids_to_delete = [chunk.get("id") for chunk in updated_chunks if chunk.get("id")]
                if chunk_ids_to_delete:
                    try:
                        self.delete_vectors(vector_ids=chunk_ids_to_delete, namespace=target_namespace)
                    except Exception as e:
                        error_msg = f"Failed to delete old versions: {e}"
                        results["errors"].append(error_msg)
                        self.logger.warning(f"   ⚠️  {error_msg}")

                # Upload new versions
                vectors = self._format_chunks_for_pinecone(updated_chunks)
                try:
                    result = self.upsert_vectors(vectors, target_namespace, batch_size)
                    results["updated_count"] = result["upserted_count"]
                except Exception as e:
                    error_msg = f"Failed to upload updated chunks: {e}"
                    results["errors"].append(error_msg)
                    self.logger.error(f"   ❌ {error_msg}")

            # Summary
            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info("✅ SYNC COMPLETED")
            self.logger.info(f"   📝 New chunks uploaded: {results['new_count']}")
            self.logger.info(f"   🔄 Chunks updated: {results['updated_count']}")
            self.logger.info(f"   ⏭️  Unchanged chunks skipped: {results['unchanged_count']}")
            if results["errors"]:
                self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
            self.logger.info("=" * 70)

            return results

        except Exception as e:
            self.logger.error(f"❌ Sync failed: {e}")
            raise

    def _format_chunks_for_pinecone(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format chunks for Pinecone upsert.
        Sanitizes metadata to only include Pinecone-compatible types.

        Args:
            chunks: List of chunks with 'id', 'embedding', 'content', 'metadata'

        Returns:
            List of formatted vectors for Pinecone
        """
        vectors = []
        for chunk in chunks:
            # Get embedding (might be under 'embedding' or 'embeddings' key)
            embedding = chunk.get("embedding") or chunk.get("embeddings")
            if not embedding:
                self.logger.warning(f"Chunk {chunk.get('id', 'unknown')} has no embedding, skipping")
                continue

            # Prepare metadata (exclude embedding from metadata to save space)
            metadata = chunk.get("metadata", {}).copy() if chunk.get("metadata") else {}
            
            # Sanitize metadata - convert complex types to Pinecone-compatible formats
            sanitized_metadata = self._sanitize_metadata(metadata)
            
            # Add essential fields to metadata
            if "content" in chunk:
                # Truncate content if too long (Pinecone metadata limit)
                content = chunk["content"]
                sanitized_metadata["content"] = content[:1000] if len(content) > 1000 else content
            
            # Add other useful fields
            for key in ["chunk_title", "document_title", "source_url", "chunk_index"]:
                if key in chunk:
                    sanitized_metadata[key] = chunk[key]

            vectors.append({
                "id": chunk.get("id", ""),
                "values": embedding,
                "metadata": sanitized_metadata
            })

        return vectors
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata to only include Pinecone-compatible types.
        Pinecone accepts: string, number, boolean, or list of strings.
        
        Args:
            metadata: Original metadata dict
            
        Returns:
            Sanitized metadata dict
        """
        import json
        
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                continue  # Skip None values
                
            # Check type and convert if needed
            if isinstance(value, (str, int, float, bool)):
                # Simple types - OK as-is
                sanitized[key] = value
                
            elif isinstance(value, list):
                # List - check if it's a list of simple types
                if len(value) == 0:
                    # Empty list - skip or convert to empty string
                    sanitized[key] = "[]"
                elif all(isinstance(item, str) for item in value):
                    # List of strings - OK as-is
                    sanitized[key] = value
                elif all(isinstance(item, (int, float, bool)) for item in value):
                    # List of numbers/bools - convert to strings
                    sanitized[key] = [str(item) for item in value]
                else:
                    # Complex list (list of dicts, mixed types) - convert to JSON string
                    try:
                        sanitized[key] = json.dumps(value)
                    except Exception:
                        sanitized[key] = str(value)
                        
            elif isinstance(value, dict):
                # Dict - convert to JSON string
                try:
                    sanitized[key] = json.dumps(value)
                except Exception:
                    sanitized[key] = str(value)
                    
            else:
                # Other types - convert to string
                sanitized[key] = str(value)
        
        return sanitized

    @retry_on_failure(max_retries=3, delay=2.0)
    def query(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Query similar vectors in Pinecone index.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            namespace: Optional namespace
            include_metadata: Include metadata in results

        Returns:
            Query results with matches
        """
        if not self._connected or not self.index:
            raise RuntimeError("Not connected to Pinecone. Call connect() first.")

        target_namespace = namespace or self.namespace or ""

        try:
            self.logger.debug(f"Querying Pinecone for top {top_k} results...")

            result = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                namespace=target_namespace,
                include_metadata=include_metadata
            )

            self.logger.debug(f"Query returned {len(result.matches)} results")
            return result

        except Exception as e:
            self.logger.error(f"❌ Query failed: {e}")
            raise

    def get_index_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.

        Args:
            namespace: Optional namespace to get stats for

        Returns:
            Index statistics
        """
        if not self._connected or not self.index:
            raise RuntimeError("Not connected to Pinecone. Call connect() first.")

        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            self.logger.error(f"❌ Failed to get index stats: {e}")
            raise

