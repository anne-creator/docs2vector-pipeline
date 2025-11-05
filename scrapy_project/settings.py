"""Scrapy project settings."""
import os
import sys

BOT_NAME = "scrapy_project"

SPIDER_MODULES = ["src.scraper"]
NEWSPIDER_MODULE = "src.scraper"

ROBOTSTXT_OBEY = True

# ALWAYS enable pipelines (can be overridden via command line if needed)
# Default to streaming mode for concurrent processing
ITEM_PIPELINES = {
    "src.scraper.pipeline.ValidationPipeline": 300,
    "src.scraper.pipeline.StreamingStoragePipeline": 800,
}

# DEBUG: Print to confirm settings are being loaded
print(f"[SCRAPY SETTINGS] Loaded with ITEM_PIPELINES={ITEM_PIPELINES}", file=sys.stderr)

