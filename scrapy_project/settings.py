"""Scrapy project settings."""

BOT_NAME = "scrapy_project"

SPIDER_MODULES = ["src.scraper"]
NEWSPIDER_MODULE = "src.scraper"

ROBOTSTXT_OBEY = True

# Enable pipelines
ITEM_PIPELINES = {
    "src.scraper.pipeline.ValidationPipeline": 300,
    "src.scraper.pipeline.StoragePipeline": 800,
}

