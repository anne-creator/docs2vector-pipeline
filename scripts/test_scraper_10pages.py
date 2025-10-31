#!/usr/bin/env python
"""Simple test scraper: Scrape 10 pages and save to scripts/.test_data/"""

import sys
import shutil
from pathlib import Path
from scrapy.crawler import CrawlerProcess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test data directory - stores data locally in scripts/.test_data/
TEST_DATA_DIR = Path(__file__).parent.parent / "tests" / ".test_data"

from src.scraper.spider import AmazonSellerHelpSpider
from config.settings import Settings


def main():
    """Run spider to scrape 10 pages using existing pipelines."""
    
    # Clean up previous test data
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
        print("🗑️  Cleaned up previous test data\n")
    
    # Override Settings.DATA_DIR to use test directory (only affects this script run)
    Settings.DATA_DIR = TEST_DATA_DIR
    
    # Ensure data directories exist
    Settings.ensure_data_directories()
    
    print("🕷️  Starting scraper...")
    print(f"📁 Output: {Settings.DATA_DIR / 'raw'}")
    print(f"🔢 Page limit: 10 pages\n")
    
    # Configure Scrapy settings - use existing pipelines
    settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 1,  # Lower for Playwright (uses browser instances)
        'DOWNLOAD_DELAY': 2.0,  # Increased delay for Playwright
        'CLOSESPIDER_PAGECOUNT': 10,  # Stop after 10 pages
        'ITEM_PIPELINES': {
            'src.scraper.pipeline.ValidationPipeline': 300,
            'src.scraper.pipeline.StoragePipeline': 800,
        },
        'LOG_LEVEL': 'INFO',
        # Playwright settings (also defined in spider, but can override here)
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    }
    
    try:
        # Create and run crawler
        process = CrawlerProcess(settings)
        process.crawl(AmazonSellerHelpSpider)
        process.start()
        
        print("\n✅ Scraping complete!")
        print(f"📄 Data saved to: {Settings.DATA_DIR / 'raw'}")
        print(f"🔐 Hashes saved to: {Settings.DATA_DIR / 'hashes'}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

