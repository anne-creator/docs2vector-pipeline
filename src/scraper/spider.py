"""Enhanced Scrapy spider with change detection."""

import scrapy
import logging
import re
from datetime import datetime
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod

from ..utils.hash_utils import generate_hash
from ..storage.versioning import VersionManager
from config.settings import Settings

logger = logging.getLogger(__name__)


class AmazonSellerHelpSpider(CrawlSpider):
    """ spider for scraping Amazon Seller Central help documentation."""

    name = "amazon_seller_help"
    allowed_domains = ["sellercentral.amazon.com"]
    start_urls = [
        "https://sellercentral.amazon.com/help/hub/reference/external/G2?locale=en-US"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": Settings.SCRAPER_DOWNLOAD_DELAY,
        "CONCURRENT_REQUESTS": Settings.SCRAPER_CONCURRENT_REQUESTS,
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "DEPTH_LIMIT": Settings.SCRAPER_DEPTH_LIMIT,
        # Playwright settings for JavaScript rendering
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": ["--disable-dev-shm-usage"],  # Helps with Docker/limited memory
        },
    }

    # Rules for following links
    # Allow only help pages and deny login pages
    # Unique links only: means that the spider will not visit the same link twice
    rules = (
        Rule(
            LinkExtractor(
                allow=r"/help/hub/reference/external/G\d+",
                deny=[
                    r"/ap/",
                    r"/gp/sign-in",
                    r"/logout",
                ],
                unique=True,
            ),
            callback="parse_help_page",
            follow=True,
            process_request="use_playwright",
        ),
    )
    
    def use_playwright(self, request, response):
        """Add Playwright rendering to requests."""
        request.meta.update({
            "playwright": True,
            "playwright_page_methods": [
                PageMethod("wait_for_selector", "body", timeout=10000),
                PageMethod("wait_for_load_state", "networkidle"),
            ],
            "playwright_abort_request": lambda req: req.resource_type in ["image", "font", "media"],
        })
        return request

    # Initialize spider with version manager for change detection
    def __init__(self, *args, **kwargs):
        """Initialize spider with version manager for change detection."""
        super().__init__(*args, **kwargs)
        self.version_manager = VersionManager()
    
    def _requests_to_follow(self, response):
        """Override to add Playwright to all followed requests."""
        # Get requests from parent CrawlSpider
        for request_or_item in super()._requests_to_follow(response):
            if isinstance(request_or_item, scrapy.Request):
                # Add Playwright meta to all requests
                request_or_item.meta.update({
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body", timeout=10000),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                    "playwright_abort_request": lambda req: req.resource_type in ["image", "font", "media"],
                })
            yield request_or_item

    def start_requests(self):
        """Generate start requests with Playwright enabled."""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body", timeout=10000),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                    "playwright_abort_request": lambda req: req.resource_type in ["image", "font", "media"],
                },
                dont_filter=True,
            )
    
    def parse_start_url(self, response):
        """Parse the start URL (CrawlSpider requires this to process start URLs)."""
        yield from self.parse_help_page(response)

    def parse_help_page(self, response):
        """Parse article pages with change detection."""
        # Extract the main title
        title = (
            response.css("h1::text").get()
            or response.css(".title::text").get()
            or response.xpath("//title/text()").get()
        )

        if not title:
            title = "Untitled"

        # Extract raw HTML content for later processing
        # Try multiple container selectors
        article_html = (
            response.css("article").get() 
            or response.css("main").get()
            or response.css(".help-content").get()
            or response.css("#content").get()
            or response.css("body").get()
        )

        # Extract plain text for change detection
        # Strategy: Extract all meaningful text elements (headings, paragraphs, lists)
        content_parts = []

        # Try structured content extraction first
        # Get all headings and paragraphs from the body
        content_selectors = [
            "h1::text", "h2::text", "h3::text", "h4::text", "h5::text", "h6::text",
            "p::text", "li::text", "td::text", "th::text",
            "div.help-content *::text",
            ".content *::text",
        ]
        
        for selector in content_selectors:
            elements = response.css(selector).getall()
            if elements:
                content_parts.extend(elements)
        
        # If still no content, try broader extraction
        if not content_parts:
            content_parts = response.css("body *::text").getall()

        # Join content parts and clean whitespace
        # Filter out empty strings and script/style content
        content_parts = [
            part.strip() for part in content_parts 
            if part.strip() and len(part.strip()) > 2
        ]
        
        content_text = " ".join(content_parts).strip()
        content_text = " ".join(content_text.split())  # Normalize whitespace
        
        # Fallback: if no content found, use title as minimal content
        if not content_text or len(content_text) < 10:
            content_text = title.strip() if title else "No content available"

        # Extract breadcrumbs for categorization
        breadcrumbs = (
            response.css(".breadcrumb a::text").getall()
            or response.css(".breadcrumbs a::text").getall()
            or []
        )

        # Extract related links
        related_links = []
        for link in response.css("a[href*='/help/']"):
            link_url = response.urljoin(link.css("::attr(href)").get())
            link_text = link.css("::text").get()
            if link_text:
                related_links.append({"text": link_text.strip(), "url": link_url})

        # Extract metadata from the page
        locale_match = re.search(r"locale=([^&]+)", response.url)
        article_id_match = re.search(r"/G(\d+)", response.url)

        metadata = {
            "locale": locale_match.group(1) if locale_match else "en-US",
            "article_id": article_id_match.group(1) if article_id_match else None,
        }

        # Extract "Things to know" and "Things to do" sections if present
        things_to_know = response.css(
            'div:contains("Things to know") + ul li::text'
        ).getall()
        things_to_do = response.css('div:contains("Things to do") + ul li::text').getall()
        things_to_avoid = response.css(
            'div:contains("Things to avoid") + ul li::text'
        ).getall()

        # Check for changes using content hash
        content_hash = generate_hash(content_text)
        change_status = self.version_manager.detect_change(response.url, content_hash)

        metadata.update(
            {
                "page_hash": content_hash,
                "change_status": change_status,
            }
        )

        # Update hash in version manager
        self.version_manager.set_hash(response.url, content_hash, save=False)

        yield {
            "url": response.url,
            "title": title.strip(),
            "content": content_text,  # Add content field for validator compatibility
            "html_content": article_html,
            "text_content": content_text,
            "last_updated": (
                response.css(".last-updated::text").get()
                or response.css(".modified-date::text").get()
                or response.css("time::text").get()
                or ""
            ),
            "breadcrumbs": breadcrumbs,
            "related_links": related_links,
            "things_to_know": things_to_know,
            "things_to_do": things_to_do,
            "things_to_avoid": things_to_avoid,
            "metadata": metadata,
            "scraped_at": datetime.now().isoformat(),
        }

    def closed(self, reason):
        """Called when spider closes - save all hashes."""
        self.version_manager.save()
        logger.info(f"Spider closed: {reason}. Hashes saved.")

