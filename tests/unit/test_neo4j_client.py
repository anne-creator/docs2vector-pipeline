"""Unit tests for Neo4j client (with mocks)."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.storage.neo4j_client import Neo4jClient
from src.utils.exceptions import StorageError


class TestNeo4jClient:
    """Test Neo4jClient class with mocked connections."""

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_init_connection(self, mock_graph_db):
        """Test Neo4j client initialization."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(
            uri="neo4j://test", username="test", password="test", database="test"
        )

        assert client.driver is not None
        mock_graph_db.driver.assert_called_once()

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_init_connection_failure(self, mock_graph_db):
        """Test Neo4j client initialization failure."""
        mock_graph_db.driver.side_effect = Exception("Connection failed")

        with pytest.raises(StorageError):
            Neo4jClient(uri="neo4j://test", username="test", password="test")

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_initialize_schema(self, mock_graph_db):
        """Test schema initialization."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(uri="neo4j://test", username="test", password="test")
        client.initialize_schema()

        assert mock_session.run.called

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_upsert_document(self, mock_graph_db):
        """Test document upsert."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(uri="neo4j://test", username="test", password="test")
        client.upsert_document("http://test.com", "Test Title")

        assert mock_session.run.called

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_upsert_chunk(self, mock_graph_db):
        """Test chunk upsert."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(uri="neo4j://test", username="test", password="test")
        client.upsert_chunk(
            chunk_id="chunk1",
            doc_url="http://test.com",
            content="Test content",
            embedding=[0.1] * 384,
            chunk_index=0,
        )

        assert mock_session.run.called

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_batch_upsert_chunks(self, mock_graph_db):
        """Test batch chunk upsert."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_session.begin_transaction.return_value.__enter__.return_value = mock_tx
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver

        chunks = [
            {
                "id": "chunk1",
                "content": "Content 1",
                "embedding": [0.1] * 384,
                "metadata": {
                    "source_url": "http://test.com",
                    "document_title": "Test",
                    "chunk_index": 0,
                },
            }
        ]

        client = Neo4jClient(uri="neo4j://test", username="test", password="test")
        client.batch_upsert_chunks(chunks, batch_size=100)

        assert mock_session.run.called

    @patch("src.storage.neo4j_client.GraphDatabase")
    def test_close(self, mock_graph_db):
        """Test closing Neo4j connection."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        client = Neo4jClient(uri="neo4j://test", username="test", password="test")
        client.close()

        mock_driver.close.assert_called_once()

