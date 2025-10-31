#!/usr/bin/env python
"""Debug script to test content extraction selectors on Amazon Seller Help pages."""

import sys
from pathlib import Path
import requests
from scrapy.http import HtmlResponse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_selectors(url):
    """Test various CSS selectors on a URL to find the right ones."""
    print(f"🔍 Testing selectors on: {url}\n")
    
    # Fetch the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return
    
    # Create Scrapy response for testing
    scrapy_response = HtmlResponse(
        url=url,
        body=response.content,
        encoding='utf-8'
    )
    
    # Test different selectors
    selectors_to_test = {
        "article tag": "article",
        "article::text": "article::text",
        "article *::text": "article *::text",
        ".help-content": ".help-content",
        ".help-content::text": ".help-content *::text",
        "main": "main",
        "main *::text": "main *::text",
        ".content": ".content",
        "#content": "#content",
        "[role='main']": "[role='main']",
        "h1": "h1::text",
        "all p tags": "p::text",
        "body text (all)": "body *::text",
    }
    
    print("=" * 80)
    for name, selector in selectors_to_test.items():
        results = scrapy_response.css(selector).getall()
        count = len(results)
        
        if count > 0:
            print(f"\n✅ {name}: '{selector}'")
            print(f"   Found: {count} elements")
            
            # Show first few results
            preview = results[:3] if count > 3 else results
            for i, result in enumerate(preview, 1):
                # Truncate long results
                preview_text = result[:100] + "..." if len(result) > 100 else result
                # Clean whitespace
                preview_text = " ".join(preview_text.split())
                if preview_text.strip():
                    print(f"   [{i}] {preview_text}")
            
            if count > 3:
                print(f"   ... and {count - 3} more")
        else:
            print(f"❌ {name}: '{selector}' - No matches")
        
        print("-" * 80)
    
    # Test title extraction
    print("\n\n📌 Title Extraction:")
    print("=" * 80)
    title_selectors = {
        "h1::text": scrapy_response.css("h1::text").get(),
        ".title::text": scrapy_response.css(".title::text").get(),
        "title tag": scrapy_response.xpath("//title/text()").get(),
        "[role='heading']": scrapy_response.css("[role='heading']::text").get(),
    }
    
    for selector, result in title_selectors.items():
        if result:
            print(f"✅ {selector}: {result.strip()}")
        else:
            print(f"❌ {selector}: No match")
    
    # Check for authentication/login requirements
    print("\n\n🔐 Authentication Check:")
    print("=" * 80)
    auth_indicators = [
        "sign-in", "login", "authenticate", "access denied",
        "unauthorized", "session expired"
    ]
    
    page_text_lower = scrapy_response.text.lower()
    found_indicators = [ind for ind in auth_indicators if ind in page_text_lower]
    
    if found_indicators:
        print(f"⚠️  Possible authentication required!")
        print(f"   Found indicators: {', '.join(found_indicators)}")
    else:
        print("✅ No authentication indicators detected")
    
    # Check page size
    print(f"\n📊 Page Statistics:")
    print("=" * 80)
    print(f"   HTML size: {len(response.content)} bytes")
    print(f"   Status code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
    
    # Extract all links
    print(f"\n🔗 Internal Help Links:")
    print("=" * 80)
    help_links = scrapy_response.css("a[href*='/help/']::attr(href)").getall()
    print(f"   Found {len(help_links)} help links")
    
    if help_links:
        # Show unique G-number links
        g_links = [link for link in help_links if '/external/G' in link]
        unique_g_links = list(set(g_links))[:5]
        print(f"   Sample G-number links:")
        for link in unique_g_links:
            print(f"      - {link}")


def main():
    """Run selector tests on sample URLs."""
    test_urls = [
        "https://sellercentral.amazon.com/help/hub/reference/external/G2?locale=en-US",
        "https://sellercentral.amazon.com/help/hub/reference/external/G200141480?locale=en-US",
    ]
    
    for i, url in enumerate(test_urls, 1):
        if i > 1:
            print("\n\n" + "=" * 100 + "\n")
        test_selectors(url)
        
        if i < len(test_urls):
            print("\n⏸️  Pausing between requests...\n")
            import time
            time.sleep(2)


if __name__ == "__main__":
    main()

