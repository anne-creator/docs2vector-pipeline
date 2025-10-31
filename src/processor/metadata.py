"""Metadata extraction and structure validation."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts and structures document metadata."""

    def extract(self, scraped_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured metadata from scraped item.

        Args:
            scraped_item: Raw scraped data dictionary

        Returns:
            Structured metadata dictionary
        """
        metadata = {
            "source_url": scraped_item.get("url", ""),
            "document_title": scraped_item.get("title", "Untitled"),
            "last_updated": scraped_item.get("last_updated", ""),
            "breadcrumbs": scraped_item.get("breadcrumbs", []),
            "related_links": scraped_item.get("related_links", []),
            "scraped_at": scraped_item.get("scraped_at", datetime.now().isoformat()),
        }

        # Extract additional metadata if available
        if "metadata" in scraped_item:
            item_metadata = scraped_item["metadata"]
            metadata.update(
                {
                    "category": item_metadata.get("category", []),
                    "article_id": item_metadata.get("article_id"),
                    "locale": item_metadata.get("locale", "en-US"),
                    "page_hash": item_metadata.get("page_hash"),
                    "change_status": item_metadata.get("change_status", "new"),
                }
            )

        return metadata

    def enrich_chunk_metadata(
        self,
        base_metadata: Dict[str, Any],
        chunk_index: int,
        heading: Optional[str] = None,
        sub_chunk_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Enrich chunk with additional metadata.

        Args:
            base_metadata: Base document metadata
            chunk_index: Index of chunk within document
            heading: Heading associated with chunk
            sub_chunk_index: Sub-chunk index if chunk was further split

        Returns:
            Enriched metadata dictionary
        """
        chunk_metadata = base_metadata.copy()
        chunk_metadata["chunk_index"] = chunk_index

        if heading:
            chunk_metadata["heading"] = heading

        if sub_chunk_index is not None:
            chunk_metadata["sub_chunk_index"] = sub_chunk_index

        return chunk_metadata

