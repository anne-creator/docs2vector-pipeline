"""LlamaIndex Cloud client for vector storage and retrieval."""

import logging
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path

from ..base import BaseIntegrationClient, retry_on_failure
from config.settings import Settings

logger = logging.getLogger(__name__)


class LlamaIndexClient(BaseIntegrationClient):
    """Client for interacting with LlamaIndex Cloud."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LlamaIndex Cloud client.

        Args:
            api_key: LlamaIndex Cloud API key (from Settings if not provided)
            base_url: API base URL (from Settings if not provided)
        """
        super().__init__()
        self.api_key = api_key or Settings.LLAMAINDEX_API_KEY
        self.base_url = base_url or Settings.LLAMAINDEX_BASE_URL
        self.pipeline_id = Settings.LLAMAINDEX_PIPELINE_ID

        if not self.api_key:
            raise ValueError("LlamaIndex API key is required")

        self.session = None

    def connect(self) -> bool:
        """
        Establish connection to LlamaIndex Cloud.

        Returns:
            True if connection successful
        """
        try:
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
        Check if LlamaIndex Cloud is reachable.

        Returns:
            True if service is healthy
        """
        try:
            if not self.session:
                return False

            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200

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
        Upload documents to LlamaIndex Cloud.

        Args:
            documents: List of documents with 'content', 'metadata', 'embedding'
            index_name: Optional index name (uses default if not provided)

        Returns:
            Response from LlamaIndex Cloud API

        Raises:
            Exception: If upload fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to LlamaIndex Cloud. Call connect() first.")

        try:
            self.logger.info(f"Uploading {len(documents)} documents to LlamaIndex Cloud...")

            payload = {
                "documents": documents,
                "pipeline_id": self.pipeline_id
            }

            if index_name:
                payload["index_name"] = index_name

            response = self.session.post(
                f"{self.base_url}/v1/documents",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            self.logger.info(f"✅ Successfully uploaded {len(documents)} documents")
            return result

        except requests.exceptions.RequestException as e:
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
        Query documents in LlamaIndex Cloud.

        Args:
            query_text: Query text
            index_name: Optional index name
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            Query results
        """
        if not self._connected:
            raise RuntimeError("Not connected to LlamaIndex Cloud. Call connect() first.")

        try:
            self.logger.debug(f"Querying: '{query_text[:50]}...'")

            payload = {
                "query": query_text,
                "pipeline_id": self.pipeline_id,
                "top_k": top_k
            }

            if index_name:
                payload["index_name"] = index_name
            if filters:
                payload["filters"] = filters

            response = self.session.post(
                f"{self.base_url}/v1/query",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            self.logger.debug(f"Query returned {len(result.get('results', []))} results")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Query failed: {e}")
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
