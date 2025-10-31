"""Neo4j Aura connection and operations."""

import logging
from typing import List, Dict, Any, Optional

from neo4j import GraphDatabase

from ..utils.exceptions import StorageError
from config.settings import Settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Client for Neo4j Aura database operations."""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j URI (defaults to Settings.NEO4J_URI)
            username: Neo4j username (defaults to Settings.NEO4J_USERNAME)
            password: Neo4j password (defaults to Settings.NEO4J_PASSWORD)
            database: Database name (defaults to Settings.NEO4J_DATABASE)
        """
        self.uri = uri or Settings.NEO4J_URI
        self.username = username or Settings.NEO4J_USERNAME
        self.password = password or Settings.NEO4J_PASSWORD
        self.database = database or Settings.NEO4J_DATABASE

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise StorageError(f"Failed to connect to Neo4j: {e}") from e

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if hasattr(self, "driver"):
            self.driver.close()
            logger.info("Neo4j connection closed")

    def initialize_schema(self) -> None:
        """Initialize database schema with constraints and indexes."""
        with self.driver.session(database=self.database) as session:
            try:
                # Create constraints for unique IDs
                session.run(
                    "CREATE CONSTRAINT document_url IF NOT EXISTS FOR (d:Document) REQUIRE d.url IS UNIQUE"
                )
                session.run(
                    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE"
                )

                logger.info("Database schema initialized")
            except Exception as e:
                # Some constraints might already exist
                logger.warning(f"Schema initialization warning: {e}")

    def create_vector_index(self, dimension: int = 384, similarity_function: str = "cosine") -> None:
        """
        Create vector index for chunk embeddings.

        Args:
            dimension: Embedding dimension
            similarity_function: Similarity function (cosine, euclidean)
        """
        with self.driver.session(database=self.database) as session:
            try:
                # This requires Neo4j 5.0+ with vector index support
                query = f"""
                CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
                FOR (c:Chunk)
                ON c.embedding
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {dimension},
                        `vector.similarity_function`: '{similarity_function}'
                    }}
                }}
                """
                session.run(query)
                logger.info(f"Vector index created with dimension {dimension}")
            except Exception as e:
                logger.warning(f"Vector index creation failed (may require Neo4j 5.0+): {e}")

    def upsert_document(self, url: str, title: str) -> None:
        """
        Create or update a document node.

        Args:
            url: Document URL
            title: Document title
        """
        with self.driver.session(database=self.database) as session:
            query = """
            MERGE (d:Document {url: $url})
            ON CREATE SET
                d.title = $title,
                d.created_at = datetime()
            ON MATCH SET
                d.title = $title,
                d.updated_at = datetime()
            """
            session.run(query, url=url, title=title)
            logger.debug(f"Upserted document: {url}")

    def upsert_chunk(
        self, chunk_id: str, doc_url: str, content: str, embedding: List[float], chunk_index: int
    ) -> None:
        """
        Create or update a chunk node.

        Args:
            chunk_id: Unique chunk ID
            doc_url: Source document URL
            content: Chunk content
            embedding: Vector embedding
            chunk_index: Index of chunk within document
        """
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (d:Document {url: $doc_url})
            MERGE (c:Chunk {id: $id})
            ON CREATE SET
                c.content = $content,
                c.embedding = $embedding,
                c.chunk_index = $chunk_index,
                c.created_at = datetime()
            ON MATCH SET
                c.content = $content,
                c.embedding = $embedding,
                c.chunk_index = $chunk_index,
                c.updated_at = datetime()
            MERGE (d)-[:CONTAINS]->(c)
            """
            session.run(
                query,
                id=chunk_id,
                doc_url=doc_url,
                content=content,
                embedding=embedding,
                chunk_index=chunk_index,
            )
            logger.debug(f"Upserted chunk: {chunk_id}")

    def batch_upsert_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """
        Batch upsert chunks into Neo4j.

        Args:
            chunks: List of chunk dictionaries with required fields
            batch_size: Number of chunks to process per batch
        """
        logger.info(f"Batch upserting {len(chunks)} chunks in batches of {batch_size}")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            with self.driver.session(database=self.database) as session:
                tx = session.begin_transaction()
                try:
                    for chunk in batch:
                        # Ensure document exists
                        doc_url = chunk["metadata"]["source_url"]
                        doc_title = chunk["metadata"].get("document_title", "Untitled")
                        self.upsert_document(doc_url, doc_title)

                        # Upsert chunk
                        self.upsert_chunk(
                            chunk_id=chunk["id"],
                            doc_url=doc_url,
                            content=chunk["content"],
                            embedding=chunk["embedding"],
                            chunk_index=chunk["metadata"].get("chunk_index", 0),
                        )
                    tx.commit()
                    logger.info(f"Processed batch {i // batch_size + 1}: {len(batch)} chunks")
                except Exception as e:
                    tx.rollback()
                    logger.error(f"Error processing batch: {e}")
                    raise StorageError(f"Failed to batch upsert chunks: {e}") from e

    def query_chunks(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query chunks using vector similarity (requires vector index).

        Args:
            query_text: Query text (would need to be embedded separately)
            top_k: Number of results to return

        Returns:
            List of matching chunks with metadata
        """
        # Note: This is a placeholder. In production, you'd embed the query first
        # and use vector similarity search
        with self.driver.session(database=self.database) as session:
            query = """
            MATCH (d:Document)-[:CONTAINS]->(c:Chunk)
            WHERE c.embedding IS NOT NULL
            RETURN c.id AS id, c.content AS content, d.url AS url,
                   d.title AS document_title, c.chunk_index AS chunk_index
            LIMIT $top_k
            """
            result = session.run(query, top_k=top_k)
            return [dict(record) for record in result]

