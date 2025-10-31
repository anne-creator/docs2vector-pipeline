"""Unit tests for chunker.

Testing Strategy:
- Core functionality tests use REAL scraped data from tests/.test_data/
- Edge case tests use FAKE/minimal data for boundary conditions
- Run scripts/test_scraper_10pages.py first to generate real test data
"""

import pytest
from src.processor.chunker import SemanticChunker
from src.processor.preprocessor import Preprocessor
from src.utils.exceptions import ProcessorError


class TestSemanticChunker:
    """Test SemanticChunker class with real data and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
        self.preprocessor = Preprocessor()

    # ========================================================================
    # CORE FUNCTIONALITY TESTS - Using Real Scraped Data
    # ========================================================================
    # These tests validate chunking with realistic Amazon Seller Central
    # documents to ensure chunks are properly created and metadata preserved.

    def test_chunk_real_document(self, single_scraped_item):
        """Test chunking a real preprocessed document."""
        # First preprocess the real HTML
        markdown_content = self.preprocessor.process(
            single_scraped_item["html_content"],
            single_scraped_item.get("text_content")
        )
        
        # Create document structure
        document = {
            "url": single_scraped_item["url"],
            "title": single_scraped_item["title"],
            "markdown_content": markdown_content,
            "metadata": {
                "source_url": single_scraped_item["url"],
                "document_title": single_scraped_item["title"],
            }
        }
        
        # Chunk the document
        chunks = self.chunker.chunk_document(document)
        
        # Verify chunks were created
        assert len(chunks) > 0, "Should create at least one chunk from real document"
        
        # Verify chunk structure
        for chunk in chunks:
            assert "content" in chunk
            assert "metadata" in chunk
            assert "id" in chunk
            assert len(chunk["content"]) > 0
            assert chunk["metadata"]["source_url"] == single_scraped_item["url"]
            assert chunk["metadata"]["document_title"] == single_scraped_item["title"]

    def test_chunk_size_limits_real_data(self, single_scraped_item):
        """Test that chunks respect size limits with real content."""
        # Use smaller chunk size to test splitting
        small_chunker = SemanticChunker(chunk_size=300, chunk_overlap=30)
        
        markdown_content = self.preprocessor.process(
            single_scraped_item["html_content"],
            single_scraped_item.get("text_content")
        )
        
        document = {
            "url": single_scraped_item["url"],
            "title": single_scraped_item["title"],
            "markdown_content": markdown_content,
            "metadata": {"source_url": single_scraped_item["url"]}
        }
        
        chunks = small_chunker.chunk_document(document)
        
        # Most chunks should be within reasonable size limits
        # (some variation is OK due to sentence boundaries)
        for chunk in chunks:
            assert len(chunk["content"]) <= 500, \
                "Chunks should not drastically exceed chunk_size"

    def test_process_multiple_real_documents(self, multiple_scraped_items):
        """Test batch chunking of multiple real documents."""
        # Preprocess all documents first
        documents = []
        for item in multiple_scraped_items:
            markdown_content = self.preprocessor.process(
                item["html_content"],
                item.get("text_content")
            )
            documents.append({
                "url": item["url"],
                "title": item["title"],
                "markdown_content": markdown_content,
                "metadata": {
                    "source_url": item["url"],
                    "document_title": item["title"],
                }
            })
        
        # Process all documents
        all_chunks = self.chunker.process_documents(documents)
        
        # Verify chunks were created
        assert len(all_chunks) > 0
        assert len(all_chunks) >= len(documents), \
            "Should have at least one chunk per document"
        
        # Verify all source URLs are represented
        source_urls = {chunk["metadata"]["source_url"] for chunk in all_chunks}
        expected_urls = {doc["url"] for doc in documents}
        assert source_urls == expected_urls, "All documents should be represented in chunks"
        
        # Verify chunk IDs are unique
        chunk_ids = [chunk["id"] for chunk in all_chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "All chunk IDs should be unique"

    def test_metadata_preservation_real_data(self, single_scraped_item):
        """Test that document metadata is preserved in chunks."""
        markdown_content = self.preprocessor.process(
            single_scraped_item["html_content"]
        )
        
        # Add custom metadata
        document = {
            "url": single_scraped_item["url"],
            "title": single_scraped_item["title"],
            "markdown_content": markdown_content,
            "metadata": {
                "source_url": single_scraped_item["url"],
                "document_title": single_scraped_item["title"],
                "custom_field": "test_value",
                "breadcrumbs": single_scraped_item.get("breadcrumbs", []),
            }
        }
        
        chunks = self.chunker.chunk_document(document)
        
        # All chunks should preserve the metadata
        for chunk in chunks:
            assert chunk["metadata"]["source_url"] == single_scraped_item["url"]
            assert chunk["metadata"]["document_title"] == single_scraped_item["title"]
            assert chunk["metadata"]["custom_field"] == "test_value"
            assert "breadcrumbs" in chunk["metadata"]

    # ========================================================================
    # EDGE CASE TESTS - Using Fake/Minimal Data
    # ========================================================================
    # These tests validate error handling and boundary conditions with
    # controlled minimal inputs.

    def test_chunk_document_basic(self):
        """Test basic document chunking with minimal fake data."""
        edge_chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
        document = {
            "url": "http://test.com",
            "title": "Test Doc",
            "markdown_content": "# Title\n\nSome content here.",
            "metadata": {"source_url": "http://test.com"},
        }
        chunks = self.chunker.chunk_document(document)
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all("id" in chunk for chunk in chunks)

    def test_chunk_document_empty_content(self):
        """Test chunking document with empty content."""
        document = {
            "url": "http://test.com",
            "title": "Test Doc",
            "markdown_content": "",
            "metadata": {},
        }
        chunks = self.chunker.chunk_document(document)
        assert len(chunks) == 0

    def test_chunk_document_large_content(self):
        """Test chunking document with large content that needs splitting."""
        large_content = "# Title\n\n" + " ".join(["word"] * 200)  # Large content
        document = {
            "url": "http://test.com",
            "title": "Test Doc",
            "markdown_content": large_content,
            "metadata": {"source_url": "http://test.com"},
        }
        chunks = self.chunker.chunk_document(document)
        assert len(chunks) > 1  # Should be split into multiple chunks

    def test_chunk_document_preserves_metadata(self):
        """Test that chunking preserves document metadata."""
        document = {
            "url": "http://test.com",
            "title": "Test Doc",
            "markdown_content": "# Title\n\nContent",
            "metadata": {"source_url": "http://test.com", "custom_field": "value"},
        }
        chunks = self.chunker.chunk_document(document)
        assert all(chunk["metadata"]["source_url"] == "http://test.com" for chunk in chunks)
        assert all(chunk["metadata"]["custom_field"] == "value" for chunk in chunks)

    def test_process_documents_multiple_fake(self):
        """Test processing multiple documents with minimal fake data."""
        edge_chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
        documents = [
            {
                "url": "http://test.com/1",
                "title": "Doc 1",
                "markdown_content": "# Doc 1\n\nContent 1",
                "metadata": {"source_url": "http://test.com/1"},
            },
            {
                "url": "http://test.com/2",
                "title": "Doc 2",
                "markdown_content": "# Doc 2\n\nContent 2",
                "metadata": {"source_url": "http://test.com/2"},
            },
        ]
        chunks = edge_chunker.process_documents(documents)
        assert len(chunks) > 0
        assert len(chunks) >= 2  # At least one chunk per document

