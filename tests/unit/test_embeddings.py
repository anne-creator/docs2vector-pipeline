"""Unit tests for embedding generator.

Testing Strategy:
- Core functionality tests use REAL scraped data from tests/.test_data/
- Edge case tests use FAKE/minimal data with mocks for fast testing
- Run scripts/test_scraper_10pages.py first to generate real test data
"""

import pytest
from unittest.mock import Mock, patch
from src.embeddings.generator import EmbeddingGenerator
from src.processor.preprocessor import Preprocessor
from src.processor.chunker import SemanticChunker
from src.utils.exceptions import EmbeddingError


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class with real data and mocks."""

    # ========================================================================
    # CORE FUNCTIONALITY TESTS - Using Real Scraped Data
    # ========================================================================
    # These tests validate embeddings work with real chunks from Amazon Seller
    # Central documents. Uses actual model (slower but validates end-to-end).

    def test_generate_embeddings_real_chunks(self, single_scraped_item):
        """Test embedding generation with real document chunks."""
        # Preprocess and chunk a real document
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        
        markdown = preprocessor.process(
            single_scraped_item["html_content"],
            single_scraped_item.get("text_content")
        )
        
        document = {
            "url": single_scraped_item["url"],
            "title": single_scraped_item["title"],
            "markdown_content": markdown,
            "metadata": {"source_url": single_scraped_item["url"]}
        }
        
        chunks = chunker.chunk_document(document)
        
        # Generate embeddings for real chunks
        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        processed_chunks = generator.process_chunks(chunks)
        
        # Verify embeddings were created
        assert len(processed_chunks) == len(chunks)
        for chunk in processed_chunks:
            assert "embedding" in chunk
            assert len(chunk["embedding"]) == 384
            assert all(isinstance(x, (int, float)) for x in chunk["embedding"])

    def test_batch_embeddings_multiple_real_documents(self, multiple_scraped_items):
        """Test batch embedding generation with multiple real documents."""
        preprocessor = Preprocessor()
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        generator = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        
        # Process multiple documents
        all_chunks = []
        for item in multiple_scraped_items[:3]:  # Use first 3 to keep test fast
            markdown = preprocessor.process(
                item["html_content"],
                item.get("text_content")
            )
            document = {
                "url": item["url"],
                "title": item["title"],
                "markdown_content": markdown,
                "metadata": {"source_url": item["url"]}
            }
            chunks = chunker.chunk_document(document)
            all_chunks.extend(chunks)
        
        # Generate embeddings for all chunks
        processed_chunks = generator.process_chunks(all_chunks)
        
        # Verify all chunks have embeddings
        assert len(processed_chunks) == len(all_chunks)
        assert all("embedding" in chunk for chunk in processed_chunks)
        
        # Embeddings should be different for different content
        if len(processed_chunks) >= 2:
            embedding1 = processed_chunks[0]["embedding"]
            embedding2 = processed_chunks[1]["embedding"]
            assert embedding1 != embedding2, "Different chunks should have different embeddings"

    # ========================================================================
    # EDGE CASE TESTS - Using Mocks for Fast Testing
    # ========================================================================
    # These tests validate the logic and error handling without loading models.
    # Note: We use real models but limit data size for speed

    def test_init(self):
        """Test embedding generator initialization."""
        generator = EmbeddingGenerator(provider="sentence-transformers", model_name="BAAI/bge-small-en-v1.5")
        assert generator.provider is not None
        assert generator.provider_name == "sentence-transformers"
        assert generator.model_name == "BAAI/bge-small-en-v1.5"

    def test_generate_embedding(self):
        """Test single embedding generation."""
        generator = EmbeddingGenerator(provider="sentence-transformers", model_name="BAAI/bge-small-en-v1.5")
        embedding = generator.generate_embedding("test text")

        assert len(embedding) == 384
        assert all(isinstance(x, (int, float)) for x in embedding)

    def test_generate_embeddings_batch(self):
        """Test batch embedding generation."""
        generator = EmbeddingGenerator(provider="sentence-transformers", model_name="BAAI/bge-small-en-v1.5")
        embeddings = generator.generate_embeddings_batch(["text1", "text2"])

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384

    def test_process_chunks(self):
        """Test processing chunks with embeddings."""
        generator = EmbeddingGenerator(provider="sentence-transformers", model_name="BAAI/bge-small-en-v1.5")
        chunks = [{"id": "chunk1", "content": "Test content"}]
        processed = generator.process_chunks(chunks)

        assert len(processed) == 1
        assert "embedding" in processed[0]
        assert len(processed[0]["embedding"]) == 384

    def test_process_empty_chunks(self):
        """Test processing empty chunks list."""
        generator = EmbeddingGenerator(provider="sentence-transformers", model_name="BAAI/bge-small-en-v1.5")
        processed = generator.process_chunks([])

        assert len(processed) == 0

