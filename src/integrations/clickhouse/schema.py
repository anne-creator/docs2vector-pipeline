"""ClickHouse table schemas for embeddings storage."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Table schema for embeddings
EMBEDDINGS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS embeddings (
    id String,
    content String,
    embedding Array(Float32),

    -- Metadata fields
    source_url String,
    document_title String,
    last_updated String,
    breadcrumbs String,
    related_links String,
    scraped_at String,
    category String,
    article_id String,
    locale String,
    page_hash String,
    change_status String,

    -- Chunk information
    chunk_index Int32,
    sub_chunk_index Int32,
    chunk_id String,
    doc_id String,

    -- System fields
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (doc_id, chunk_index, sub_chunk_index)
SETTINGS index_granularity = 8192;
"""


# Index for vector similarity search (if using ClickHouse vector search capabilities)
VECTOR_INDEX_SCHEMA = """
ALTER TABLE embeddings
ADD INDEX embedding_index embedding TYPE vector('cosine', 384)
GRANULARITY 100;
"""


def create_embeddings_table(client, table_name: str = "embeddings") -> bool:
    """
    Create embeddings table in ClickHouse.

    Args:
        client: ClickHouse client instance
        table_name: Name of the table to create

    Returns:
        True if table created successfully

    Raises:
        Exception: If table creation fails
    """
    try:
        # Replace table name in schema if custom name provided
        schema = EMBEDDINGS_TABLE_SCHEMA.replace("embeddings", table_name)

        logger.info(f"Creating table '{table_name}'...")
        client.execute(schema)
        logger.info(f"✅ Table '{table_name}' created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create table '{table_name}': {e}")
        raise


def create_documents_table(client, table_name: str = "documents") -> bool:
    """
    Create documents table for raw document storage.

    Args:
        client: ClickHouse client instance
        table_name: Name of the table to create

    Returns:
        True if table created successfully
    """
    schema = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        doc_id String,
        source_url String,
        title String,
        content String,
        raw_html String,

        -- Metadata
        metadata String,
        page_hash String,
        scraped_at DateTime,
        last_updated String,

        -- System fields
        created_at DateTime DEFAULT now(),
        updated_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (doc_id, scraped_at)
    SETTINGS index_granularity = 8192;
    """

    try:
        logger.info(f"Creating table '{table_name}'...")
        client.execute(schema)
        logger.info(f"✅ Table '{table_name}' created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create table '{table_name}': {e}")
        raise


def create_chunks_table(client, table_name: str = "chunks") -> bool:
    """
    Create chunks table for document chunks.

    Args:
        client: ClickHouse client instance
        table_name: Name of the table to create

    Returns:
        True if table created successfully
    """
    schema = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        chunk_id String,
        doc_id String,
        content String,
        chunk_index Int32,
        sub_chunk_index Int32,

        -- Section information
        section_title String,
        section_number String,

        -- Metadata
        metadata String,

        -- System fields
        created_at DateTime DEFAULT now(),
        updated_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (doc_id, chunk_index, sub_chunk_index)
    SETTINGS index_granularity = 8192;
    """

    try:
        logger.info(f"Creating table '{table_name}'...")
        client.execute(schema)
        logger.info(f"✅ Table '{table_name}' created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create table '{table_name}': {e}")
        raise


def initialize_database(client) -> bool:
    """
    Initialize all required tables in ClickHouse.

    Args:
        client: ClickHouse client instance

    Returns:
        True if all tables created successfully
    """
    try:
        logger.info("Initializing ClickHouse database schema...")

        create_documents_table(client)
        create_chunks_table(client)
        create_embeddings_table(client)

        logger.info("✅ Database schema initialized successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize database schema: {e}")
        raise
