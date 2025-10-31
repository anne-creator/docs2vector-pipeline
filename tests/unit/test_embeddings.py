"""Unit tests for embedding generator."""

import pytest
from unittest.mock import Mock, patch
from src.embeddings.generator import EmbeddingGenerator
from src.utils.exceptions import EmbeddingError


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class."""

    @patch("src.embeddings.generator.SentenceTransformer")
    def test_init(self, mock_sentence_transformer):
        """Test embedding generator initialization."""
        mock_model = Mock()
        mock_model.encode.return_value = [0.1] * 384
        mock_sentence_transformer.return_value = mock_model

        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        assert generator.model is not None

    @patch("src.embeddings.generator.SentenceTransformer")
    def test_generate_embedding(self, mock_sentence_transformer):
        """Test single embedding generation."""
        mock_model = Mock()
        import numpy as np

        mock_model.encode.return_value = np.array([0.1] * 384)
        mock_sentence_transformer.return_value = mock_model

        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        embedding = generator.generate_embedding("test text")

        assert len(embedding) == 384
        assert all(isinstance(x, (int, float)) for x in embedding)

    @patch("src.embeddings.generator.SentenceTransformer")
    def test_generate_embeddings_batch(self, mock_sentence_transformer):
        """Test batch embedding generation."""
        mock_model = Mock()
        import numpy as np

        mock_model.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
        mock_sentence_transformer.return_value = mock_model

        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        embeddings = generator.generate_embeddings_batch(["text1", "text2"])

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384

    @patch("src.embeddings.generator.SentenceTransformer")
    def test_process_chunks(self, mock_sentence_transformer):
        """Test processing chunks with embeddings."""
        mock_model = Mock()
        import numpy as np

        mock_model.encode.return_value = np.array([[0.1] * 384])
        mock_sentence_transformer.return_value = mock_model

        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        chunks = [{"id": "chunk1", "content": "Test content"}]
        processed = generator.process_chunks(chunks)

        assert len(processed) == 1
        assert "embedding" in processed[0]
        assert len(processed[0]["embedding"]) == 384

    @patch("src.embeddings.generator.SentenceTransformer")
    def test_process_empty_chunks(self, mock_sentence_transformer):
        """Test processing empty chunks list."""
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model

        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        processed = generator.process_chunks([])

        assert len(processed) == 0

