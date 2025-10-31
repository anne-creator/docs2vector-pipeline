#!/usr/bin/env python
"""Debug script to test if CSS selectors work on Amazon Seller Central pages."""

import sys
from pathlib import Path
import requests
from parsel import Selector

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_amazon_selectors():
    """Test CSS selectors on a real Amazon Seller Central page."""

    test_url = "https://sellercentral.amazon.com/help/hub/reference/external/G2?locale=en-US"

    print("=" * 60)
    print("🔍 TESTING CSS SELECTORS ON AMAZON SELLER CENTRAL")
    print("=" * 60)
    print(f"📄 Test URL: {test_url}")
    print()

    # Fetch the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        print("⏳ Fetching page...")
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📊 Content Length: {len(response.text)} characters")
        print()

        # Parse with Scrapy's selector
        selector = Selector(text=response.text)

        # Test different selectors
        print("=" * 60)
        print("🧪 TESTING SELECTORS")
        print("=" * 60)
        print()

        # Test 1: Page title
        print("1️⃣  Testing h1::text")
        h1_result = selector.css("h1::text").get()
        print(f"   Result: {h1_result}")
        print()

        # Test 2: Article tag
        print("2️⃣  Testing article tag")
        article_result = selector.css("article").get()
        if article_result:
            print(f"   Found! Length: {len(article_result)} chars")
            print(f"   Preview: {article_result[:200]}...")
        else:
            print("   ❌ Not found")
        print()

        # Test 3: Content div
        print("3️⃣  Testing .help-content class")
        help_content = selector.css(".help-content").get()
        if help_content:
            print(f"   Found! Length: {len(help_content)} chars")
        else:
            print("   ❌ Not found")
        print()

        # Test 4: Paragraphs
        print("4️⃣  Testing p tags")
        paragraphs = selector.css("p::text").getall()
        print(f"   Found {len(paragraphs)} paragraphs")
        if paragraphs:
            print(f"   First paragraph: {paragraphs[0][:100]}...")
        print()

        # Test 5: All text content
        print("5️⃣  Testing all text extraction")
        all_text = selector.css("body::text").getall()
        print(f"   Found {len(all_text)} text nodes")
        total_chars = sum(len(t.strip()) for t in all_text)
        print(f"   Total text: {total_chars} characters")
        print()

        # Test 6: Check for login/redirect
        print("6️⃣  Checking for login requirement")
        login_indicators = [
            selector.css("input[type='password']").get(),
            "sign in" in response.text.lower()[:1000],
            "login" in response.text.lower()[:1000],
        ]

        if any(login_indicators):
            print("   ⚠️  WARNING: Page might require login!")
            print("   Amazon Seller Central requires authentication")
        else:
            print("   ✅ No obvious login required")
        print()

        # Test 7: Check robots.txt compliance
        print("7️⃣  Testing robots.txt")
        robots_url = "https://sellercentral.amazon.com/robots.txt"
        robots_response = requests.get(robots_url, timeout=10)
        print(f"   Status: {robots_response.status_code}")

        if "Disallow: /help" in robots_response.text:
            print("   ⚠️  WARNING: /help might be disallowed in robots.txt")
        else:
            print("   ✅ /help appears to be allowed")
        print()

        # Save HTML for inspection
        output_file = project_root / "data" / "test_scrape" / "debug_page.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print("=" * 60)
        print("💾 SAVED HTML FOR INSPECTION")
        print("=" * 60)
        print(f"📁 File: {output_file}")
        print(f"💡 Open it to inspect: open {output_file}")
        print()

        # Show HTML structure preview
        print("=" * 60)
        print("📋 HTML STRUCTURE PREVIEW (first 2000 chars)")
        print("=" * 60)
        print(response.text[:2000])
        print("...")
        print()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching page: {e}")
        print()
        print("💡 Possible reasons:")
        print("   • No internet connection")
        print("   • Amazon blocking automated requests")
        print("   • Page requires login")
        print("   • Firewall/proxy blocking")


if __name__ == "__main__":
    test_amazon_selectors()
