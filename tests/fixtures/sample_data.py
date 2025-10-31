"""Sample data fixtures for testing."""

from datetime import datetime


def sample_scraped_item():
    """Sample scraped item data."""
    return {
        "url": "https://sellercentral.amazon.com/help/hub/reference/external/G123",
        "title": "Test Document",
        "html_content": "<article><h1>Test Document</h1><p>This is test content.</p></article>",
        "text_content": "Test Document This is test content.",
        "last_updated": "2024-01-01",
        "breadcrumbs": ["Home", "Help"],
        "related_links": [],
        "metadata": {
            "locale": "en-US",
            "article_id": "123",
            "page_hash": "abc123",
            "change_status": "new",
        },
        "scraped_at": datetime.now().isoformat(),
    }


def sample_processed_document():
    """Sample processed document."""
    return {
        "url": "https://sellercentral.amazon.com/help/hub/reference/external/G123",
        "title": "Test Document",
        "markdown_content": "# Test Document\n\nThis is test content.",
        "last_updated": "2024-01-01",
        "metadata": {
            "source_url": "https://sellercentral.amazon.com/help/hub/reference/external/G123",
            "document_title": "Test Document",
            "breadcrumbs": ["Home", "Help"],
        },
    }


def sample_chunk():
    """Sample chunk data."""
    return {
        "id": "G123_0",
        "content": "This is test content.",
        "metadata": {
            "source_url": "https://sellercentral.amazon.com/help/hub/reference/external/G123",
            "document_title": "Test Document",
            "chunk_index": 0,
            "chunk_id": "G123_0",
            "doc_id": "https://sellercentral.amazon.com/help/hub/reference/external/G123",
        },
    }


def sample_chunk_with_embedding():
    """Sample chunk with embedding."""
    chunk = sample_chunk()
    chunk["embedding"] = [0.1] * 384  # Mock 384-dim embedding
    return chunk

