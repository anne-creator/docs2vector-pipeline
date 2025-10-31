"""Scrapy pipeline for data processing and storage."""

import logging
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from ..utils.validators import validate_document
from ..storage.file_manager import FileManager
from config.settings import Settings

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """Pipeline to validate scraped items."""

    def process_item(self, item, spider):
        """Validate item before further processing."""
        adapter = ItemAdapter(item)

        # Convert to dict for validation
        item_dict = dict(adapter)

        if not validate_document(item_dict):
            raise DropItem(f"Invalid item: {item.get('url', 'Unknown')}")

        return item


class StoragePipeline:
    """Pipeline to save scraped items to local storage."""

    def __init__(self):
        """Initialize storage pipeline."""
        self.file_manager = FileManager()
        self.items = []

    def process_item(self, item, spider):
        """Collect items for batch saving."""
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item

    def close_spider(self, spider):
        """Save all collected items when spider closes."""
        if self.items:
            try:
                self.file_manager.save_raw_data(self.items)
                logger.info(f"Saved {len(self.items)} items to raw storage")
            except Exception as e:
                logger.error(f"Error saving items: {e}")
                raise

