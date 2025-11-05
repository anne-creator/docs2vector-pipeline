"""ClickHouse client for vector and document storage."""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None

from ..base import BaseIntegrationClient, retry_on_failure
from config.settings import Settings

logger = logging.getLogger(__name__)


class ClickHouseClient(BaseIntegrationClient):
    """Client for interacting with ClickHouse database."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        Initialize ClickHouse client.

        Args:
            host: ClickHouse host (from Settings if not provided)
            port: ClickHouse port (from Settings if not provided)
            username: ClickHouse username (from Settings if not provided)
            password: ClickHouse password (from Settings if not provided)
            database: ClickHouse database name (from Settings if not provided)
        """
        super().__init__()

        if clickhouse_connect is None:
            raise ImportError(
                "clickhouse-connect is not installed. "
                "Install it with: pip install clickhouse-connect"
            )

        self.host = host or Settings.CLICKHOUSE_HOST
        self.port = port or Settings.CLICKHOUSE_PORT
        self.username = username or Settings.CLICKHOUSE_USERNAME
        self.password = password or Settings.CLICKHOUSE_PASSWORD
        self.database = database or Settings.CLICKHOUSE_DATABASE

        self.client = None

    def connect(self) -> bool:
        """
        Establish connection to ClickHouse.

        Returns:
            True if connection successful
        """
        try:
            self.logger.info(f"Connecting to ClickHouse at {self.host}:{self.port}...")

            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )

            # Test connection
            if self.health_check():
                self._connected = True
                self.logger.info("✅ Connected to ClickHouse")
                return True
            else:
                self.logger.error("❌ ClickHouse health check failed")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to ClickHouse: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close connection to ClickHouse.

        Returns:
            True if disconnection successful
        """
        try:
            if self.client:
                self.client.close()
                self.client = None
            self._connected = False
            self.logger.info("Disconnected from ClickHouse")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from ClickHouse: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=1.0)
    def health_check(self) -> bool:
        """
        Check if ClickHouse is reachable.

        Returns:
            True if service is healthy
        """
        try:
            if not self.client:
                return False

            result = self.client.command("SELECT 1")
            return result == 1

        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a query on ClickHouse.

        Args:
            query: SQL query to execute
            parameters: Optional query parameters

        Returns:
            Query result

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected to ClickHouse. Call connect() first.")

        try:
            if parameters:
                return self.client.query(query, parameters=parameters)
            return self.client.command(query)

        except Exception as e:
            self.logger.error(f"❌ Query execution failed: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def insert_embeddings(
        self,
        embeddings: List[Dict[str, Any]],
        table_name: str = "embeddings"
    ) -> int:
        """
        Insert embeddings into ClickHouse.

        Args:
            embeddings: List of embedding dictionaries
            table_name: Name of the table

        Returns:
            Number of rows inserted

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected to ClickHouse. Call connect() first.")

        if not embeddings:
            self.logger.warning("No embeddings to insert")
            return 0

        try:
            self.logger.info(f"Inserting {len(embeddings)} embeddings into '{table_name}'...")

            # Prepare data for insertion
            rows = []
            for record in embeddings:
                metadata = record.get('metadata', {})

                row = {
                    'id': record.get('id', ''),
                    'content': record.get('content', ''),
                    'embedding': record.get('embedding', []),
                    'source_url': metadata.get('source_url', ''),
                    'document_title': metadata.get('document_title', ''),
                    'last_updated': metadata.get('last_updated', ''),
                    'breadcrumbs': json.dumps(metadata.get('breadcrumbs', [])),
                    'related_links': json.dumps(metadata.get('related_links', [])),
                    'scraped_at': metadata.get('scraped_at', ''),
                    'category': json.dumps(metadata.get('category', [])),
                    'article_id': metadata.get('article_id', ''),
                    'locale': metadata.get('locale', ''),
                    'page_hash': metadata.get('page_hash', ''),
                    'change_status': metadata.get('change_status', ''),
                    'chunk_index': metadata.get('chunk_index', 0),
                    'sub_chunk_index': metadata.get('sub_chunk_index', 0),
                    'chunk_id': metadata.get('chunk_id', ''),
                    'doc_id': metadata.get('doc_id', ''),
                }
                rows.append(row)

            # Insert data
            column_names = list(rows[0].keys())
            data = [[row[col] for col in column_names] for row in rows]

            self.client.insert(table_name, data, column_names=column_names)

            self.logger.info(f"✅ Successfully inserted {len(embeddings)} embeddings")
            return len(embeddings)

        except Exception as e:
            self.logger.error(f"❌ Failed to insert embeddings: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def batch_insert_from_file(
        self,
        file_path: Path,
        table_name: str = "embeddings",
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Insert embeddings from a JSON file in batches.

        Args:
            file_path: Path to JSON file with embeddings
            table_name: Name of the table
            batch_size: Number of records per batch

        Returns:
            Summary of insert operation
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                embeddings = json.load(f)

            if not isinstance(embeddings, list):
                raise ValueError("Expected a list of embeddings")

            self.logger.info(f"Loaded {len(embeddings)} embeddings from {file_path}")

            # Insert in batches
            total_inserted = 0
            errors = []

            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]
                try:
                    inserted = self.insert_embeddings(batch, table_name)
                    total_inserted += inserted
                except Exception as e:
                    errors.append(f"Batch {i//batch_size + 1}: {e}")

            return {
                "total_records": len(embeddings),
                "inserted": total_inserted,
                "errors": errors
            }

        except Exception as e:
            self.logger.error(f"❌ Batch insert failed: {e}")
            raise

    def query_similar_vectors(
        self,
        query_vector: List[float],
        table_name: str = "embeddings",
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar vectors using cosine similarity.

        Args:
            query_vector: Query embedding vector
            table_name: Name of the table
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of similar documents with scores
        """
        if not self._connected:
            raise RuntimeError("Not connected to ClickHouse. Call connect() first.")

        try:
            self.logger.debug(f"Querying for {top_k} similar vectors...")

            # Build WHERE clause from filters
            where_clause = ""
            if filters:
                conditions = [f"{key} = '{value}'" for key, value in filters.items()]
                where_clause = "WHERE " + " AND ".join(conditions)

            # Note: This is a simplified cosine similarity calculation
            # For production, consider using ClickHouse's vector search features
            query = f"""
            SELECT
                id,
                content,
                source_url,
                document_title,
                arraySum(arrayMap((x, y) -> x * y, embedding, {query_vector})) /
                (sqrt(arraySum(arrayMap(x -> x * x, embedding))) *
                 sqrt(arraySum(arrayMap(x -> x * x, {query_vector})))) AS similarity
            FROM {table_name}
            {where_clause}
            ORDER BY similarity DESC
            LIMIT {top_k}
            """

            result = self.client.query(query)

            documents = []
            for row in result.result_rows:
                documents.append({
                    "id": row[0],
                    "content": row[1],
                    "source_url": row[2],
                    "document_title": row[3],
                    "similarity": row[4]
                })

            self.logger.debug(f"Found {len(documents)} similar documents")
            return documents

        except Exception as e:
            self.logger.error(f"❌ Vector query failed: {e}")
            raise

    def get_statistics(self, table_name: str = "embeddings") -> Dict[str, Any]:
        """
        Get statistics about the embeddings table.

        Args:
            table_name: Name of the table

        Returns:
            Statistics dictionary
        """
        if not self._connected:
            raise RuntimeError("Not connected to ClickHouse. Call connect() first.")

        try:
            # Get row count
            count_query = f"SELECT count() FROM {table_name}"
            total_rows = self.client.command(count_query)

            # Get unique documents
            unique_docs_query = f"SELECT count(DISTINCT doc_id) FROM {table_name}"
            unique_docs = self.client.command(unique_docs_query)

            # Get latest update
            latest_query = f"SELECT max(created_at) FROM {table_name}"
            latest_update = self.client.command(latest_query)

            return {
                "total_embeddings": total_rows,
                "unique_documents": unique_docs,
                "latest_update": latest_update,
                "table_name": table_name
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get statistics: {e}")
            raise

    def delete_by_doc_id(self, doc_id: str, table_name: str = "embeddings") -> int:
        """
        Delete all embeddings for a specific document.

        Args:
            doc_id: Document ID
            table_name: Name of the table

        Returns:
            Number of rows deleted
        """
        if not self._connected:
            raise RuntimeError("Not connected to ClickHouse. Call connect() first.")

        try:
            self.logger.info(f"Deleting embeddings for doc_id: {doc_id}")

            query = f"ALTER TABLE {table_name} DELETE WHERE doc_id = '{doc_id}'"
            self.execute(query)

            self.logger.info(f"✅ Deleted embeddings for doc_id: {doc_id}")
            return 1  # ClickHouse doesn't return affected rows for ALTER TABLE DELETE

        except Exception as e:
            self.logger.error(f"❌ Failed to delete embeddings: {e}")
            raise
