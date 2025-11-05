"""Scrapy pipeline for data processing and storage."""

import logging
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from pathlib import Path

from ..utils.validators import validate_document
from ..storage.file_manager import FileManager
from config.settings import Settings

logger = logging.getLogger(__name__)  # Will use src.scraper logger


class ValidationPipeline:
    """Pipeline to validate scraped items."""

    def process_item(self, item, spider):
        """Validate item before further processing."""
        adapter = ItemAdapter(item)

        # Convert to dict for validation
        item_dict = dict(adapter)

        if not validate_document(item_dict):
            logger.error(f"❌ Validation failed for item: {item.get('url', 'Unknown')}")
            raise DropItem(f"Invalid item: {item.get('url', 'Unknown')}")

        logger.debug(f"✓ Validated item: {item_dict.get('title', 'Untitled')[:40]}...")
        return item


class StoragePipeline:
    """Pipeline to save scraped items to local storage (batch mode)."""

    def __init__(self):
        """Initialize storage pipeline."""
        self.file_manager = FileManager()
        self.items = []
        logger.debug("StoragePipeline initialized (batch mode)")

    def process_item(self, item, spider):
        """Collect items for batch saving."""
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        logger.debug(f"Collected item {len(self.items)}: {item.get('title', 'Untitled')[:40]}...")
        return item

    def close_spider(self, spider):
        """Save all collected items when spider closes."""
        if self.items:
            try:
                logger.info(f"Saving {len(self.items)} items to raw storage...")
                self.file_manager.save_raw_data(self.items)
                logger.info(f"✅ Saved {len(self.items)} items to raw storage")
            except Exception as e:
                logger.error(f"❌ Error saving items: {e}")
                raise
        else:
            logger.warning("No items to save")


class StreamingStoragePipeline:
    """Pipeline to save scraped items immediately (streaming mode for concurrent processing)."""

    def __init__(self):
        """Initialize streaming storage pipeline."""
        self.file_manager = FileManager()
        self.item_count = 0
        logger.info("🌊 StreamingStoragePipeline initialized (concurrent processing mode)")

    def _generate_filename(self, item_dict: dict) -> str:
        """
        Generate a unique filename for an item based on URL.
        
        Args:
            item_dict: Item dictionary with URL
            
        Returns:
            Filename for this item
        """
        url = item_dict.get('url', 'unknown')
        
        # Create a hash of the URL for a safe filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # Extract page ID if available (from article_id or URL)
        article_id = item_dict.get('metadata', {}).get('article_id', '')
        if article_id:
            filename = f"item_{article_id}_{url_hash}.json"
        else:
            filename = f"item_{url_hash}.json"
        
        return filename

    def process_item(self, item, spider):
        """Save item immediately to enable downstream processing."""
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)
        
        try:
            # Generate unique filename for this item
            filename = self._generate_filename(item_dict)
            
            # Save immediately (single-item list for compatibility)
            self.file_manager.save_raw_data([item_dict], filename=filename)
            
            self.item_count += 1
            title = item_dict.get('title', 'Untitled')[:50]
            logger.info(f"📤 [{self.item_count}] Saved: {title}... → {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving item: {e}")
            raise
        
        return item

    def close_spider(self, spider):
        """Log summary when spider closes."""
        logger.info(f"🌊 Streaming complete: {self.item_count} items saved individually")
        logger.info(f"✅ Items available for concurrent processing in: {Settings.get_data_path('raw')}")

