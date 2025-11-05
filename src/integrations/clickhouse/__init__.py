"""ClickHouse database integration."""

from .client import ClickHouseClient
from .schema import EMBEDDINGS_TABLE_SCHEMA, create_embeddings_table

__all__ = ["ClickHouseClient", "EMBEDDINGS_TABLE_SCHEMA", "create_embeddings_table"]
