"""Unit tests for validators."""

import pytest
from src.utils.validators import (
    validate_chunk,
    validate_embedding,
    validate_metadata,
    validate_document,
    sanitize_text,
)


class TestValidators:
    """Test validation functions."""

    def test_validate_chunk_valid(self):
        """Test validation of valid chunk."""
        chunk = {"content": "test", "metadata": {"source_url": "http://test.com"}}
        assert validate_chunk(chunk) is True

    def test_validate_chunk_missing_fields(self):
        """Test validation of chunk with missing fields."""
        chunk = {"content": "test"}
        assert validate_chunk(chunk) is False

        chunk = {"metadata": {}}
        assert validate_chunk(chunk) is False

    def test_validate_embedding_valid(self):
        """Test validation of valid embedding."""
        embedding = [0.1, 0.2, 0.3]
        assert validate_embedding(embedding) is True

    def test_validate_embedding_invalid_type(self):
        """Test validation of invalid embedding type."""
        assert validate_embedding("not a list") is False
        assert validate_embedding(None) is False

    def test_validate_embedding_empty(self):
        """Test validation of empty embedding."""
        assert validate_embedding([]) is False

    def test_validate_metadata_valid(self):
        """Test validation of valid metadata."""
        metadata = {"source_url": "http://test.com"}
        assert validate_metadata(metadata) is True

    def test_validate_metadata_missing_url(self):
        """Test validation of metadata missing source_url."""
        metadata = {"title": "Test"}
        assert validate_metadata(metadata) is False

    def test_validate_document_valid(self):
        """Test validation of valid document."""
        document = {
            "url": "http://test.com",
            "title": "Test",
            "content": "Test content",
        }
        assert validate_document(document) is True

    def test_validate_document_missing_fields(self):
        """Test validation of document with missing fields."""
        document = {"url": "http://test.com", "title": "Test"}
        assert validate_document(document) is False

    def test_sanitize_text_normal(self):
        """Test text sanitization of normal text."""
        text = "normal text"
        assert sanitize_text(text) == "normal text"

    def test_sanitize_text_excessive_whitespace(self):
        """Test text sanitization removes excessive whitespace."""
        text = "text   with    multiple   spaces"
        assert sanitize_text(text) == "text with multiple spaces"

    def test_sanitize_text_not_string(self):
        """Test text sanitization handles non-string input."""
        assert sanitize_text(None) == ""
        assert sanitize_text(123) == ""

