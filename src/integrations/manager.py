"""Unified integration manager providing singleton client instances."""

import logging
from typing import Optional

from .llamaindex.client import LlamaIndexClient
from .n8n.client import N8nClient
from .clickhouse.client import ClickHouseClient
from .s3.client import S3Client

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Provides singleton instances of integration clients."""

    _llamaindex_client: Optional[LlamaIndexClient] = None
    _n8n_client: Optional[N8nClient] = None
    _clickhouse_client: Optional[ClickHouseClient] = None
    _s3_client: Optional[S3Client] = None

    @classmethod
    def get_llamaindex_client(cls) -> LlamaIndexClient:
        """
        Get or create LlamaIndex client instance.

        Returns:
            LlamaIndex client instance
        """
        if cls._llamaindex_client is None:
            cls._llamaindex_client = LlamaIndexClient()
            logger.debug("Created LlamaIndex client instance")
        return cls._llamaindex_client

    @classmethod
    def get_n8n_client(cls) -> N8nClient:
        """
        Get or create n8n client instance.

        Returns:
            n8n client instance
        """
        if cls._n8n_client is None:
            cls._n8n_client = N8nClient()
            logger.debug("Created n8n client instance")
        return cls._n8n_client

    @classmethod
    def get_clickhouse_client(cls) -> ClickHouseClient:
        """
        Get or create ClickHouse client instance.

        Returns:
            ClickHouse client instance
        """
        if cls._clickhouse_client is None:
            cls._clickhouse_client = ClickHouseClient()
            logger.debug("Created ClickHouse client instance")
        return cls._clickhouse_client

    @classmethod
    def get_s3_client(cls) -> S3Client:
        """
        Get or create S3 client instance.

        Returns:
            S3 client instance
        """
        if cls._s3_client is None:
            cls._s3_client = S3Client()
            logger.debug("Created S3 client instance")
        return cls._s3_client

    @classmethod
    def reset(cls) -> None:
        """Reset all client instances (mainly for testing)."""
        if cls._llamaindex_client:
            cls._llamaindex_client.disconnect()
        if cls._n8n_client:
            cls._n8n_client.disconnect()
        if cls._clickhouse_client:
            cls._clickhouse_client.disconnect()
        if cls._s3_client:
            cls._s3_client.disconnect()

        cls._llamaindex_client = None
        cls._n8n_client = None
        cls._clickhouse_client = None
        cls._s3_client = None
        logger.debug("Reset all client instances")
