"""LlamaIndex Cloud client for vector storage and retrieval."""

import logging
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path

from llama_cloud.client import LlamaCloud
from llama_cloud.types import CloudDocumentCreate
from ..base import BaseIntegrationClient, retry_on_failure
from config.settings import Settings

logger = logging.getLogger(__name__)


class LlamaIndexClient(BaseIntegrationClient):
    """Client for interacting with LlamaIndex Cloud."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        index_name: Optional[str] = None,
        project_name: Optional[str] = None,
        organization_id: Optional[str] = None
    ):
        """
        Initialize LlamaIndex Cloud client.

        Args:
            api_key: LlamaCloud API key (from Settings if not provided)
            base_url: API base URL (from Settings if not provided)
            index_name: Index name (from Settings if not provided)
            project_name: Project name (from Settings if not provided)
            organization_id: Organization ID (from Settings if not provided)
        """
        super().__init__()
        self.api_key = api_key or Settings.LLAMACLOUD_API_KEY
        self.base_url = base_url or Settings.LLAMACLOUD_BASE_URL
        self.index_name = index_name or Settings.LLAMACLOUD_INDEX_NAME
        self.project_name = project_name or Settings.LLAMACLOUD_PROJECT_NAME
        self.organization_id = organization_id or Settings.LLAMACLOUD_ORGANIZATION_ID

        if not self.api_key:
            raise ValueError("LlamaCloud API key is required")

        self.session = None
        self.sdk_client = None

    def connect(self) -> bool:
        """
        Establish connection to LlamaIndex Cloud.

        Returns:
            True if connection successful
        """
        try:
            # Initialize both SDK client and requests session
            self.sdk_client = LlamaCloud(token=self.api_key)
            
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })

            # Test connection with health check
            if self.health_check():
                self._connected = True
                self.logger.info("✅ Connected to LlamaIndex Cloud")
                return True
            else:
                self.logger.error("❌ LlamaIndex Cloud health check failed")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to LlamaIndex Cloud: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close connection to LlamaIndex Cloud.

        Returns:
            True if disconnection successful
        """
        try:
            if self.session:
                self.session.close()
                self.session = None
            self._connected = False
            self.logger.info("Disconnected from LlamaIndex Cloud")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from LlamaIndex Cloud: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    def health_check(self) -> bool:
        """
        Check if LlamaCloud is reachable by listing pipelines.

        Returns:
            True if service is healthy
        """
        try:
            if not self.session:
                return False

            # Try to list pipelines as health check
            response = self.session.get(
                f"{self.base_url}/api/v1/pipelines",
                params={"project_name": self.project_name}
            )
            return response.status_code in [200, 401, 403]  # 401/403 means API is reachable but needs auth

        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    def upload_documents(
        self,
        documents: List[Dict[str, Any]],
        index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload documents to LlamaCloud pipeline using create_batch_pipeline_documents().

        Args:
            documents: List of documents with 'content', 'metadata', 'id'
            index_name: Optional pipeline name (uses default if not provided)

        Returns:
            Response from LlamaCloud API

        Raises:
            Exception: If upload fails
        """
        if not self._connected or not self.sdk_client:
            raise RuntimeError("Not connected to LlamaCloud. Call connect() first.")

        target_pipeline = index_name or self.index_name
        if not target_pipeline:
            raise ValueError("Pipeline name is required")

        try:
            self.logger.info(f"Uploading {len(documents)} documents to LlamaCloud pipeline '{target_pipeline}'...")

            # Format documents for create_batch_pipeline_documents API
            # Create CloudDocumentCreate objects
            formatted_docs = []
            for doc in documents:
                # Get metadata and add doc_id if available
                metadata = doc.get("metadata", {}).copy() if doc.get("metadata") else {}
                if "id" in doc:
                    metadata["doc_id"] = doc["id"]
                
                # Create CloudDocumentCreate object
                cloud_doc = CloudDocumentCreate(
                    text=doc.get("content") or doc.get("text", ""),
                    metadata=metadata if metadata else None
                )
                formatted_docs.append(cloud_doc)

            # Use the SDK method with correct parameter name (pipeline_id, not pipeline_name)
            result = self.sdk_client.pipelines.create_batch_pipeline_documents(
                pipeline_id=target_pipeline,
                request=formatted_docs
            )
            
            self.logger.info(f"✅ Successfully uploaded {len(documents)} documents")
            return {"status": "success", "count": len(documents), "result": result}

        except Exception as e:
            self.logger.error(f"❌ Failed to upload documents: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def create_index(
        self,
        index_name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new index in LlamaIndex Cloud.

        Args:
            index_name: Name of the index
            description: Optional description
            metadata: Optional metadata

        Returns:
            Response from LlamaIndex Cloud API
        """
        if not self._connected:
            raise RuntimeError("Not connected to LlamaIndex Cloud. Call connect() first.")

        try:
            self.logger.info(f"Creating index '{index_name}'...")

            payload = {
                "name": index_name,
                "pipeline_id": self.pipeline_id
            }

            if description:
                payload["description"] = description
            if metadata:
                payload["metadata"] = metadata

            response = self.session.post(
                f"{self.base_url}/v1/indices",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            self.logger.info(f"✅ Successfully created index '{index_name}'")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to create index: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def query(
        self,
        query_text: str,
        index_name: Optional[str] = None,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query documents in LlamaCloud index.

        Args:
            query_text: Query text
            index_name: Optional index name
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            Query results
        """
        if not self._connected:
            raise RuntimeError("Not connected to LlamaCloud. Call connect() first.")

        target_index = index_name or self.index_name
        if not target_index:
            raise ValueError("Index name is required")

        try:
            self.logger.debug(f"Querying: '{query_text[:50]}...'")

            payload = {
                "query": query_text,
                "similarity_top_k": top_k
            }

            if filters:
                payload["filters"] = filters

            response = self.session.post(
                f"{self.base_url}/api/v1/pipelines/{target_index}/search",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            num_results = len(result.get("retrieval_nodes", []))
            self.logger.debug(f"Query returned {num_results} results")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Query failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response: {e.response.text}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def delete_documents(
        self,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete documents from LlamaCloud index.

        Args:
            document_ids: Optional list of document IDs to delete
            metadata_filter: Optional metadata filter for bulk deletion
            index_name: Optional index name

        Returns:
            Response from LlamaCloud API

        Raises:
            Exception: If deletion fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to LlamaCloud. Call connect() first.")

        target_index = index_name or self.index_name
        if not target_index:
            raise ValueError("Index name is required")

        if not document_ids and not metadata_filter:
            raise ValueError("Either document_ids or metadata_filter is required")

        try:
            payload = {}
            if document_ids:
                payload["ids"] = document_ids
                self.logger.info(f"Deleting {len(document_ids)} documents from LlamaCloud index '{target_index}'...")
            if metadata_filter:
                payload["metadata_filter"] = metadata_filter
                self.logger.info(f"Deleting documents matching filter from LlamaCloud index '{target_index}'...")

            response = self.session.post(
                f"{self.base_url}/api/v1/pipelines/{target_index}/documents/delete",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            deleted_count = result.get("deleted_count", 0)
            self.logger.info(f"✅ Successfully deleted {deleted_count} documents")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to delete documents: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response: {e.response.text}")
            raise

    def sync_documents(
        self,
        local_documents: List[Dict[str, Any]],
        index_name: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Synchronize local documents with LlamaCloud index.
        Handles additions, updates, and deletions based on change_status.

        Args:
            local_documents: List of documents with 'content', 'metadata', 'id'
            index_name: Optional index name
            batch_size: Number of documents per batch

        Returns:
            Summary of sync operation with counts for added, updated, deleted
        """
        if not self._connected:
            raise RuntimeError("Not connected to LlamaCloud. Call connect() first.")

        target_index = index_name or self.index_name
        
        self.logger.info(f"🔄 Starting document sync to LlamaCloud index '{target_index}'...")
        self.logger.info(f"   Total local documents: {len(local_documents)}")

        # Categorize documents by change status
        new_docs = []
        updated_docs = []
        unchanged_docs = []
        
        for doc in local_documents:
            change_status = doc.get("metadata", {}).get("change_status", "new")
            if change_status == "new":
                new_docs.append(doc)
            elif change_status == "updated":
                updated_docs.append(doc)
            else:
                unchanged_docs.append(doc)

        self.logger.info(f"   New documents: {len(new_docs)}")
        self.logger.info(f"   Updated documents: {len(updated_docs)}")
        self.logger.info(f"   Unchanged documents: {len(unchanged_docs)} (will be skipped)")

        results = {
            "total_documents": len(local_documents),
            "new_count": 0,
            "updated_count": 0,
            "unchanged_count": len(unchanged_docs),
            "deleted_count": 0,
            "errors": []
        }

        try:
            # Upload new documents in batches
            if new_docs:
                self.logger.info(f"📤 Uploading {len(new_docs)} new documents...")
                for i in range(0, len(new_docs), batch_size):
                    batch = new_docs[i:i + batch_size]
                    try:
                        self.upload_documents(batch, target_index)
                        results["new_count"] += len(batch)
                    except Exception as e:
                        error_msg = f"Batch {i//batch_size + 1} (new): {e}"
                        results["errors"].append(error_msg)
                        self.logger.error(f"   ❌ {error_msg}")

            # Handle updated documents: delete old versions and upload new
            if updated_docs:
                self.logger.info(f"🔄 Updating {len(updated_docs)} documents...")
                # Delete old versions by doc_id
                doc_ids_to_delete = [doc.get("id") for doc in updated_docs if doc.get("id")]
                if doc_ids_to_delete:
                    try:
                        # Delete in batches
                        for i in range(0, len(doc_ids_to_delete), batch_size):
                            batch_ids = doc_ids_to_delete[i:i + batch_size]
                            self.delete_documents(document_ids=batch_ids, index_name=target_index)
                    except Exception as e:
                        error_msg = f"Failed to delete old versions: {e}"
                        results["errors"].append(error_msg)
                        self.logger.warning(f"   ⚠️  {error_msg}")

                # Upload new versions
                for i in range(0, len(updated_docs), batch_size):
                    batch = updated_docs[i:i + batch_size]
                    try:
                        self.upload_documents(batch, target_index)
                        results["updated_count"] += len(batch)
                    except Exception as e:
                        error_msg = f"Batch {i//batch_size + 1} (updated): {e}"
                        results["errors"].append(error_msg)
                        self.logger.error(f"   ❌ {error_msg}")

            # Summary
            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info("✅ SYNC COMPLETED")
            self.logger.info(f"   📝 New documents uploaded: {results['new_count']}")
            self.logger.info(f"   🔄 Documents updated: {results['updated_count']}")
            self.logger.info(f"   ⏭️  Unchanged documents skipped: {results['unchanged_count']}")
            if results["errors"]:
                self.logger.warning(f"   ⚠️  Errors: {len(results['errors'])}")
            self.logger.info("=" * 70)

            return results

        except Exception as e:
            self.logger.error(f"❌ Sync failed: {e}")
            raise

    def batch_upload_from_file(
        self,
        file_path: Path,
        batch_size: int = 100,
        index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload documents from a JSON file in batches.

        Args:
            file_path: Path to JSON file with documents
            batch_size: Number of documents per batch
            index_name: Optional index name

        Returns:
            Summary of upload operation
        """
        import json

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)

            if not isinstance(documents, list):
                raise ValueError("Expected a list of documents")

            self.logger.info(f"Loaded {len(documents)} documents from {file_path}")

            # Upload in batches
            total_uploaded = 0
            errors = []

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                try:
                    self.upload_documents(batch, index_name)
                    total_uploaded += len(batch)
                except Exception as e:
                    errors.append(f"Batch {i//batch_size + 1}: {e}")

            return {
                "total_documents": len(documents),
                "uploaded": total_uploaded,
                "errors": errors
            }

        except Exception as e:
            self.logger.error(f"❌ Batch upload failed: {e}")
            raise
