"""Unit tests for metadata extractor."""

import pytest
from src.processor.metadata import MetadataExtractor


class TestMetadataExtractor:
    """Test MetadataExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MetadataExtractor()

    def test_extract_basic_metadata(self):
        """Test basic metadata extraction."""
        item = {
            "url": "http://test.com",
            "title": "Test Title",
            "breadcrumbs": ["Home", "Help"],
            "related_links": [],
        }
        metadata = self.extractor.extract(item)
        assert metadata["source_url"] == "http://test.com"
        assert metadata["document_title"] == "Test Title"
        assert metadata["breadcrumbs"] == ["Home", "Help"]

    def test_extract_with_nested_metadata(self):
        """Test metadata extraction with nested metadata field."""
        item = {
            "url": "http://test.com",
            "title": "Test",
            "metadata": {
                "category": ["Test"],
                "article_id": "123",
                "locale": "en-US",
            },
        }
        metadata = self.extractor.extract(item)
        assert metadata["category"] == ["Test"]
        assert metadata["article_id"] == "123"
        assert metadata["locale"] == "en-US"

    def test_enrich_chunk_metadata(self):
        """Test enriching chunk metadata."""
        base_metadata = {"source_url": "http://test.com", "document_title": "Test"}
        enriched = self.extractor.enrich_chunk_metadata(base_metadata, chunk_index=0, heading="Section 1")
        assert enriched["chunk_index"] == 0
        assert enriched["heading"] == "Section 1"
        assert enriched["source_url"] == "http://test.com"

    def test_enrich_chunk_metadata_with_sub_index(self):
        """Test enriching chunk metadata with sub-chunk index."""
        base_metadata = {"source_url": "http://test.com"}
        enriched = self.extractor.enrich_chunk_metadata(
            base_metadata, chunk_index=0, sub_chunk_index=1
        )
        assert enriched["chunk_index"] == 0
        assert enriched["sub_chunk_index"] == 1

