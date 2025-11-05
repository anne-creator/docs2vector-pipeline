"""n8n workflow automation client."""

import logging
from typing import Dict, Any, Optional, List
import requests

from ..base import BaseIntegrationClient, retry_on_failure
from config.settings import Settings

logger = logging.getLogger(__name__)


class N8nClient(BaseIntegrationClient):
    """Client for interacting with n8n workflow automation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        """
        Initialize n8n client.

        Args:
            base_url: n8n API base URL (from Settings if not provided)
            api_key: n8n API key (from Settings if not provided)
            webhook_url: Webhook URL for triggering workflows (from Settings if not provided)
        """
        super().__init__()
        self.base_url = base_url or Settings.N8N_BASE_URL
        self.api_key = api_key or Settings.N8N_API_KEY
        self.webhook_url = webhook_url or Settings.N8N_WEBHOOK_URL

        self.session = None

    def connect(self) -> bool:
        """
        Establish connection to n8n.

        Returns:
            True if connection successful
        """
        try:
            self.session = requests.Session()

            # Add API key to headers if provided
            if self.api_key:
                self.session.headers.update({
                    "X-N8N-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                })

            # Test connection with health check
            if self.health_check():
                self._connected = True
                self.logger.info("✅ Connected to n8n")
                return True
            else:
                self.logger.warning("⚠️  n8n health check failed, but connection established")
                self._connected = True  # Allow connection even if health check fails
                return True

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to n8n: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close connection to n8n.

        Returns:
            True if disconnection successful
        """
        try:
            if self.session:
                self.session.close()
                self.session = None
            self._connected = False
            self.logger.info("Disconnected from n8n")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from n8n: {e}")
            return False

    @retry_on_failure(max_retries=2, delay=1.0)
    def health_check(self) -> bool:
        """
        Check if n8n is reachable.

        Returns:
            True if service is healthy
        """
        try:
            if not self.session or not self.base_url:
                return False

            # Try to reach the base URL or health endpoint
            response = self.session.get(f"{self.base_url}/healthz", timeout=5)
            return response.status_code in [200, 404]  # 404 is ok, means server is up

        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    def trigger_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger an n8n workflow via webhook.

        Args:
            event_type: Type of event (e.g., 'scrape_completed', 'embeddings_ready')
            payload: Event payload data
            webhook_url: Optional webhook URL (uses default if not provided)

        Returns:
            Response from n8n webhook

        Raises:
            Exception: If webhook trigger fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to n8n. Call connect() first.")

        webhook = webhook_url or self.webhook_url
        if not webhook:
            raise ValueError("No webhook URL configured")

        try:
            self.logger.info(f"Triggering n8n webhook for event: {event_type}")

            # Prepare webhook payload
            webhook_payload = {
                "event_type": event_type,
                "timestamp": payload.get("timestamp"),
                "data": payload
            }

            response = requests.post(webhook, json=webhook_payload, timeout=30)
            response.raise_for_status()

            result = response.json() if response.content else {"status": "success"}
            self.logger.info(f"✅ Webhook triggered successfully for {event_type}")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to trigger webhook: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Get list of workflows from n8n.

        Returns:
            List of workflows

        Raises:
            Exception: If request fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to n8n. Call connect() first.")

        if not self.base_url or not self.api_key:
            raise ValueError("API base URL and key required for this operation")

        try:
            self.logger.debug("Fetching workflows from n8n...")

            response = self.session.get(f"{self.base_url}/api/v1/workflows")
            response.raise_for_status()

            workflows = response.json().get("data", [])
            self.logger.info(f"Retrieved {len(workflows)} workflows")
            return workflows

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to get workflows: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=2.0)
    def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific workflow by ID.

        Args:
            workflow_id: The workflow ID
            data: Optional input data for the workflow

        Returns:
            Execution result

        Raises:
            Exception: If execution fails
        """
        if not self._connected:
            raise RuntimeError("Not connected to n8n. Call connect() first.")

        if not self.base_url or not self.api_key:
            raise ValueError("API base URL and key required for this operation")

        try:
            self.logger.info(f"Executing workflow: {workflow_id}")

            payload = {"data": data} if data else {}

            response = self.session.post(
                f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            self.logger.info(f"✅ Workflow {workflow_id} executed successfully")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to execute workflow: {e}")
            raise

    def notify_scrape_completed(
        self,
        source_url: str,
        num_pages: int,
        output_file: str
    ) -> Dict[str, Any]:
        """
        Notify n8n that scraping is completed.

        Args:
            source_url: The scraped URL
            num_pages: Number of pages scraped
            output_file: Path to output file

        Returns:
            Webhook response
        """
        from datetime import datetime

        payload = {
            "timestamp": datetime.now().isoformat(),
            "source_url": source_url,
            "num_pages": num_pages,
            "output_file": str(output_file),
            "stage": "scraping"
        }

        return self.trigger_webhook("scrape_completed", payload)

    def notify_embeddings_ready(
        self,
        num_embeddings: int,
        output_file: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Notify n8n that embeddings are ready.

        Args:
            num_embeddings: Number of embeddings generated
            output_file: Path to embeddings file
            model: Embedding model used

        Returns:
            Webhook response
        """
        from datetime import datetime

        payload = {
            "timestamp": datetime.now().isoformat(),
            "num_embeddings": num_embeddings,
            "output_file": str(output_file),
            "model": model,
            "stage": "embeddings"
        }

        return self.trigger_webhook("embeddings_ready", payload)

    def notify_data_uploaded(
        self,
        destination: str,
        num_records: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Notify n8n that data has been uploaded to external service.

        Args:
            destination: Destination service (e.g., 'clickhouse', 'llamaindex')
            num_records: Number of records uploaded
            metadata: Optional additional metadata

        Returns:
            Webhook response
        """
        from datetime import datetime

        payload = {
            "timestamp": datetime.now().isoformat(),
            "destination": destination,
            "num_records": num_records,
            "metadata": metadata or {},
            "stage": "upload"
        }

        return self.trigger_webhook("data_uploaded", payload)
