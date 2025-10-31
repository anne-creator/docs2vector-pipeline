"""Unit tests for chunker."""

import pytest
from src.processor.chunker import SemanticChunker
from src.utils.exceptions import ProcessorError


class TestSemanticChunker:
    """Test SemanticChunker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)

    def test_chunk_document_basic(self):
        """Test basic document chunking."""
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

    def test_process_documents_multiple(self):
        """Test processing multiple documents."""
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
        chunks = self.chunker.process_documents(documents)
        assert len(chunks) > 0
        assert len(chunks) >= 2  # At least one chunk per document

