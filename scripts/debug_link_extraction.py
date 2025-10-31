#!/usr/bin/env python
"""Debug script to test LinkExtractor patterns and robots.txt compliance."""

import sys
from pathlib import Path
import requests
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from urllib.robotparser import RobotFileParser

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_robots_txt():
    """Check if robots.txt allows crawling."""
    print("🤖 Testing robots.txt compliance\n")
    print("=" * 80)
    
    robots_url = "https://sellercentral.amazon.com/robots.txt"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    try:
        response = requests.get(robots_url, timeout=10)
        print(f"✅ robots.txt fetched successfully\n")
        print("Content preview:")
        print("-" * 80)
        print(response.text[:500])
        print("-" * 80)
        
        # Parse robots.txt
        rp = RobotFileParser()
        rp.parse(response.text.splitlines())
        
        # Test specific paths
        test_paths = [
            "https://sellercentral.amazon.com/help/hub/reference/external/G2",
            "https://sellercentral.amazon.com/help/hub/reference/external/G200141480",
            "https://sellercentral.amazon.com/help/",
        ]
        
        print("\n\nPath accessibility check:")
        print("=" * 80)
        for path in test_paths:
            can_fetch = rp.can_fetch(user_agent, path)
            status = "✅ ALLOWED" if can_fetch else "❌ BLOCKED"
            print(f"{status}: {path}")
            
    except Exception as e:
        print(f"❌ Error checking robots.txt: {e}")


def test_link_extractor(url):
    """Test LinkExtractor to see what links it finds."""
    print(f"\n\n🔗 Testing LinkExtractor on: {url}\n")
    print("=" * 80)
    
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
    
    # Create Scrapy response
    scrapy_response = HtmlResponse(
        url=url,
        body=response.content,
        encoding='utf-8'
    )
    
    # Test the actual LinkExtractor configuration from spider
    link_extractor = LinkExtractor(
        allow=r"/help/hub/reference/external/G\d+",
        deny=[
            r"/ap/",
            r"/gp/sign-in",
            r"/logout",
        ],
        unique=True,
    )
    
    # Extract links
    extracted_links = link_extractor.extract_links(scrapy_response)
    
    print(f"✅ Found {len(extracted_links)} matching links\n")
    
    if extracted_links:
        print("Extracted links:")
        print("-" * 80)
        for i, link in enumerate(extracted_links[:20], 1):  # Show first 20
            print(f"{i:2d}. {link.url}")
            if link.text:
                text_preview = link.text[:60] + "..." if len(link.text) > 60 else link.text
                print(f"    Text: {text_preview}")
        
        if len(extracted_links) > 20:
            print(f"\n... and {len(extracted_links) - 20} more links")
    else:
        print("❌ No links matched the pattern!")
        print("\nDebugging info:")
        print("-" * 80)
        
        # Show all help links
        all_help_links = scrapy_response.css("a[href*='/help/']::attr(href)").getall()
        print(f"Total links with '/help/': {len(all_help_links)}")
        
        if all_help_links:
            print("\nSample help links found:")
            for link in all_help_links[:10]:
                print(f"  - {link}")
        
        # Test simpler patterns
        print("\n\nTesting alternative patterns:")
        print("-" * 80)
        
        alternative_patterns = [
            (r"/help/", "Any help page"),
            (r"/help/hub/reference/", "Help hub reference"),
            (r"/help/hub/reference/.*G\d+", "Help pages with G-numbers (any position)"),
            (r"external/G\d+", "External G-number pages"),
        ]
        
        for pattern, description in alternative_patterns:
            extractor = LinkExtractor(allow=pattern, unique=True)
            links = extractor.extract_links(scrapy_response)
            print(f"  {description}: '{pattern}' -> {len(links)} links")


def check_page_structure(url):
    """Check if the page requires authentication or has special structure."""
    print(f"\n\n📄 Checking page structure: {url}\n")
    print("=" * 80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check for redirects
        if response.history:
            print("⚠️  Page was redirected:")
            for i, resp in enumerate(response.history, 1):
                print(f"  {i}. {resp.status_code} -> {resp.url}")
            print(f"  Final: {response.status_code} -> {response.url}")
        else:
            print(f"✅ No redirects (Status: {response.status_code})")
        
        # Check content type
        content_type = response.headers.get('Content-Type', 'Unknown')
        print(f"\nContent-Type: {content_type}")
        
        # Check for common authentication indicators in HTML
        scrapy_response = HtmlResponse(
            url=response.url,
            body=response.content,
            encoding='utf-8'
        )
        
        # Look for login forms or auth requirements
        login_indicators = {
            "login form": scrapy_response.css("form[action*='sign-in'], form[action*='login']").getall(),
            "password field": scrapy_response.css("input[type='password']").getall(),
            "sign-in button": scrapy_response.css("button:contains('Sign'), a:contains('Sign')").getall(),
        }
        
        print("\n🔐 Authentication indicators:")
        print("-" * 80)
        for indicator, elements in login_indicators.items():
            if elements:
                print(f"  ⚠️  Found {len(elements)} {indicator}(s)")
            else:
                print(f"  ✅ No {indicator}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all debug tests."""
    print("🐞 Link Extraction Debugger")
    print("=" * 100)
    
    # Test robots.txt
    test_robots_txt()
    
    # Test URLs
    test_urls = [
        "https://sellercentral.amazon.com/help/hub/reference/external/G2?locale=en-US",
    ]
    
    for url in test_urls:
        check_page_structure(url)
        test_link_extractor(url)
    
    print("\n\n" + "=" * 100)
    print("✅ Debug complete!")


if __name__ == "__main__":
    main()

