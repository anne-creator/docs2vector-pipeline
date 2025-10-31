"""Integration tests for the Amazon Seller Help scraper."""

# Install the correct reactor BEFORE any other imports
# This must be done before Scrapy/Twisted imports to avoid reactor conflicts
import sys
if 'twisted.internet.reactor' not in sys.modules:
    # Install asyncio reactor for Playwright support
    import asyncio
    from twisted.internet import asyncioreactor
    asyncioreactor.install(asyncio.get_event_loop_policy().new_event_loop())

import pytest
import json
from pathlib import Path
from scrapy.crawler import CrawlerRunner
from twisted.internet import defer, reactor
from itemadapter import ItemAdapter

from src.scraper.spider import AmazonSellerHelpSpider
from src.storage.file_manager import FileManager


@pytest.fixture(scope="function")
def reactor_cleanup():
    """Ensure reactor is stopped before and after each test."""
    # Stop reactor before test if it's running
    if reactor.running:
        reactor.stop()
    yield
    # Clean up after test
    if reactor.running:
        reactor.stop()


class ScraperTestPipeline:
    """Simple pipeline to collect items for testing."""
    
    file_manager = None  # Will be set by test
    
    def __init__(self):
        self.items = []
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)
        self.items.append(item_dict)
        return item
    
    def close_spider(self, spider):
        # Save items to file for verification
        if self.items:
            file_manager = self.file_manager or FileManager()
            file_manager.save_raw_data(self.items, filename="test_scrape.json")


@pytest.mark.integration
class TestScraperIntegration:
    """Integration tests for the scraper spider and pipelines."""

    def test_scraper_runs_successfully(self, tmp_path, monkeypatch, reactor_cleanup):
        """Test that the scraper runs successfully with a small page limit."""
        # Use temporary directory for test data
        monkeypatch.setattr("config.settings.Settings.DATA_DIR", tmp_path)
        
        # Create file manager with temp dir
        file_manager = FileManager(base_dir=tmp_path)
        file_manager.ensure_directories()
        
        # Store collected items
        collected_items = []
        
        # Store file manager for pipeline to use
        ScraperTestPipeline.file_manager = file_manager
        
        # Configure Scrapy with minimal settings for fast testing
        settings = {
            'USER_AGENT': 'Mozilla/5.0 (Test) AppleWebKit/537.36',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 1,
            'DOWNLOAD_DELAY': 0.5,
            'CLOSESPIDER_PAGECOUNT': 2,  # Only scrape 2 pages for speed
            'ITEM_PIPELINES': {
                'tests.integration.test_scraper_integration.ScraperTestPipeline': 800,
            },
            'LOG_LEVEL': 'ERROR',  # Reduce log noise during tests
        }
        
        # Use CrawlerRunner to avoid reactor restart issues
        runner = CrawlerRunner(settings)
        
        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(AmazonSellerHelpSpider)
        
        # Run crawler in reactor
        d = crawl()
        d.addBoth(lambda _: reactor.stop() if reactor.running else None)
        reactor.run(installSignalHandlers=False)
        
        # Get collected items from pipeline
        # Access via the spider's test_collected_items attribute
        # Note: We'll need to get items from the pipeline instance or saved file
        saved_file = tmp_path / "raw" / "test_scrape.json"
        if saved_file.exists():
            with open(saved_file, 'r', encoding='utf-8') as f:
                collected_items = json.load(f)
        
        # Verify items were collected
        assert len(collected_items) > 0, "No items were scraped"
        assert len(collected_items) <= 2, "Should not exceed page limit"

    def test_scraped_items_have_required_fields(self, tmp_path, monkeypatch, reactor_cleanup):
        """Test that scraped items have all required fields (url, title, content)."""
        # Use temporary directory for test data
        monkeypatch.setattr("config.settings.Settings.DATA_DIR", tmp_path)
        
        # Create file manager with temp dir
        file_manager = FileManager(base_dir=tmp_path)
        file_manager.ensure_directories()
        
        # Store file manager for pipeline to use
        ScraperTestPipeline.file_manager = file_manager
        
        # Configure Scrapy
        settings = {
            'USER_AGENT': 'Mozilla/5.0 (Test) AppleWebKit/537.36',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 1,
            'DOWNLOAD_DELAY': 0.5,
            'CLOSESPIDER_PAGECOUNT': 2,  # Only scrape 2 pages for speed
            'ITEM_PIPELINES': {
                'tests.integration.test_scraper_integration.ScraperTestPipeline': 800,
            },
            'LOG_LEVEL': 'ERROR',
        }
        
        # Use CrawlerRunner to avoid reactor restart issues
        runner = CrawlerRunner(settings)
        
        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(AmazonSellerHelpSpider)
        
        # Run crawler in reactor
        d = crawl()
        d.addBoth(lambda _: reactor.stop() if reactor.running else None)
        reactor.run(installSignalHandlers=False)
        
        # Get collected items from saved file
        saved_file = tmp_path / "raw" / "test_scrape.json"
        assert saved_file.exists(), "No items were saved"
        
        with open(saved_file, 'r', encoding='utf-8') as f:
            collected_items = json.load(f)
        
        # Verify all items have required fields
        assert len(collected_items) > 0, "No items were scraped"
        
        for item in collected_items:
            assert 'url' in item, f"Item missing 'url' field: {item.get('title', 'Unknown')}"
            assert 'title' in item, f"Item missing 'title' field"
            assert item['url'], f"Item has empty URL"
            assert item['title'], f"Item has empty title"
            # Check for either 'content' or 'text_content'
            assert 'content' in item or 'text_content' in item, \
                f"Item missing content field: {item.get('title', 'Unknown')}"
            content = item.get('content') or item.get('text_content', '')
            assert content, f"Item has empty content"

    def test_file_manager_saves_data_correctly(self, tmp_path, monkeypatch):
        """Test that FileManager saves scraped data to the correct location."""
        # Use temporary directory for test data
        monkeypatch.setattr("config.settings.Settings.DATA_DIR", tmp_path)
        
        file_manager = FileManager(base_dir=tmp_path)
        file_manager.ensure_directories()
        
        # Sample test data
        test_items = [
            {
                'url': 'https://test.example.com/page1',
                'title': 'Test Page 1',
                'text_content': 'This is test content for page 1',
                'scraped_at': '2024-01-01T00:00:00'
            },
            {
                'url': 'https://test.example.com/page2',
                'title': 'Test Page 2',
                'text_content': 'This is test content for page 2',
                'scraped_at': '2024-01-01T00:00:01'
            }
        ]
        
        # Save test data
        saved_path = file_manager.save_raw_data(test_items, filename="test_data.json")
        
        # Verify file was created
        assert saved_path.exists(), "Saved file does not exist"
        assert saved_path.parent == tmp_path / "raw", "File not saved to raw directory"
        
        # Verify file contents
        with open(saved_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert len(loaded_data) == len(test_items), "Loaded data count doesn't match"
        assert loaded_data[0]['url'] == test_items[0]['url'], "Data doesn't match saved data"
        assert loaded_data[0]['title'] == test_items[0]['title'], "Title doesn't match"

    @pytest.mark.slow
    def test_scraper_10_pages_with_production_pipelines(self, tmp_path, monkeypatch):
        """
        Integration test: Scrape 10 pages from real website using production pipelines.
        
        This is the same as the original working test_scraper_10pages.py script,
        except it stores data in a temporary test directory instead of data/.
        
        This test:
        - Scrapes from the REAL Amazon Seller Help website (not fake data)
        - Uses production spider (AmazonSellerHelpSpider) 
        - Uses production pipelines (ValidationPipeline, StoragePipeline)
        - Stores data in TEMPORARY test directories (not production data/)
        - Verifies data quality and pipeline functionality
        
        Note: Marked as @pytest.mark.slow since it scrapes real pages (takes ~30 seconds).
        Run with: pytest -m slow tests/integration/
        """
        from scrapy.crawler import CrawlerProcess
        from config.settings import Settings
        
        # ONLY DIFFERENCE from original script: Use temporary directory for test data
        monkeypatch.setattr("config.settings.Settings.DATA_DIR", tmp_path)
        
        # Ensure data directories exist (same as original)
        Settings.ensure_data_directories()
        
        print(f"\n🕷️  Starting scraper...")
        print(f"📁 Output: {tmp_path / 'raw'}")
        print(f"🔢 Page limit: 10 pages\n")
        
        # Configure Scrapy settings - EXACTLY like original script
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
            # Create and run crawler - EXACTLY like original script
            process = CrawlerProcess(settings)
            process.crawl(AmazonSellerHelpSpider)
            process.start()
            
            print("\n✅ Scraping complete!")
            print(f"📄 Data saved to: {tmp_path / 'raw'}")
            print(f"🔐 Hashes saved to: {tmp_path / 'hashes'}")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
            pytest.fail("Test interrupted by user")
        except Exception as e:
            print(f"\n\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"Scraping failed: {e}")
        
        # Verify data was saved to temporary directory
        raw_dir = tmp_path / "raw"
        assert raw_dir.exists(), "Raw data directory was not created"
        
        # Find the saved JSON file (will have timestamp in filename)
        json_files = list(raw_dir.glob("raw_data_*.json"))
        assert len(json_files) > 0, "No raw data files were created"
        
        saved_file = json_files[0]  # Get the most recent one
        print(f"📄 Verifying data in: {saved_file.name}")
        
        # Load and verify the scraped data
        with open(saved_file, 'r', encoding='utf-8') as f:
            scraped_items = json.load(f)
        
        # Assertions
        assert len(scraped_items) > 0, "No items were scraped"
        assert len(scraped_items) <= 10, f"Should not exceed page limit of 10, got {len(scraped_items)}"
        print(f"📊 Scraped {len(scraped_items)} pages")
        
        # Verify data quality for each item
        for idx, item in enumerate(scraped_items):
            # Required fields
            assert 'url' in item, f"Item {idx} missing 'url' field"
            assert 'title' in item, f"Item {idx} missing 'title' field"
            assert item['url'], f"Item {idx} has empty URL"
            assert item['title'], f"Item {idx} has empty title"
            
            # Content field (could be 'content' or 'text_content')
            assert 'content' in item or 'text_content' in item, \
                f"Item {idx} missing content field"
            content = item.get('content') or item.get('text_content', '')
            assert content, f"Item {idx} has empty content"
            assert len(content) > 50, f"Item {idx} has suspiciously short content ({len(content)} chars)"
            
            # Metadata fields
            assert 'scraped_at' in item, f"Item {idx} missing 'scraped_at' timestamp"
            
            print(f"  ✓ Page {idx + 1}: {item['title'][:60]}... ({len(content)} chars)")
        
        # Verify hashes were saved
        hashes_dir = tmp_path / "hashes"
        assert hashes_dir.exists(), "Hashes directory was not created"
        hash_file = hashes_dir / "content_hashes.json"
        assert hash_file.exists(), "Content hashes file was not created"
        
        with open(hash_file, 'r', encoding='utf-8') as f:
            hashes = json.load(f)
        
        assert len(hashes) > 0, "No content hashes were saved"
        print(f"🔐 Verified {len(hashes)} content hashes")
        
        print(f"✅ Integration test passed! All data stored in temp directory.")
        print(f"   (Real data/ directory remains untouched)")

