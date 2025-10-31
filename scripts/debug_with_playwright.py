#!/usr/bin/env python
"""Debug script using Playwright to test content extraction with JavaScript rendering."""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_with_playwright(url):
    """Test content extraction using Playwright with JavaScript rendering."""
    print(f"🎭 Testing with Playwright on: {url}\n")
    print("=" * 80)
    
    async with async_playwright() as p:
        # Launch browser
        print("🚀 Launching Chromium browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Navigate to page
        print(f"📄 Loading page: {url}")
        try:
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            print(f"✅ Page loaded! Status: {response.status}")
        except Exception as e:
            print(f"❌ Error loading page: {e}")
            await browser.close()
            return
        
        # Wait for content to load
        print("⏳ Waiting for content to render...")
        try:
            await page.wait_for_selector('article, main, .content, body', timeout=10000)
            print("✅ Content selector found!")
        except Exception as e:
            print(f"⚠️  Timeout waiting for selector: {e}")
        
        # Extract content using various selectors
        print("\n\n📊 Testing Content Extraction:")
        print("=" * 80)
        
        selectors = {
            "Title (h1)": "h1",
            "Article content": "article",
            "Main content": "main",
            "All paragraphs": "p",
            "All headings": "h1, h2, h3, h4, h5, h6",
            "Links": "a[href*='/help/']",
        }
        
        results = {}
        for name, selector in selectors.items():
            elements = await page.query_selector_all(selector)
            count = len(elements)
            results[name] = count
            
            if count > 0:
                print(f"\n✅ {name}: '{selector}' - Found {count} elements")
                
                # Get text content for first few elements
                for i, elem in enumerate(elements[:3], 1):
                    try:
                        text = await elem.text_content()
                        if text and text.strip():
                            preview = text.strip()[:100]
                            preview = " ".join(preview.split())
                            print(f"   [{i}] {preview}...")
                    except:
                        pass
                
                if count > 3:
                    print(f"   ... and {count - 3} more")
            else:
                print(f"❌ {name}: '{selector}' - No matches")
        
        # Extract full article content
        print("\n\n📝 Full Article Content:")
        print("=" * 80)
        
        try:
            # Try article tag first
            article = await page.query_selector("article")
            if article:
                article_text = await article.text_content()
                words = len(article_text.split())
                print(f"✅ Article found! Word count: {words}")
                print(f"\nFirst 500 characters:")
                print("-" * 80)
                print(article_text.strip()[:500])
                print("-" * 80)
            else:
                # Try main tag
                main = await page.query_selector("main")
                if main:
                    main_text = await main.text_content()
                    words = len(main_text.split())
                    print(f"✅ Main content found! Word count: {words}")
                    print(f"\nFirst 500 characters:")
                    print("-" * 80)
                    print(main_text.strip()[:500])
                    print("-" * 80)
                else:
                    print("⚠️  No article or main content found")
        except Exception as e:
            print(f"❌ Error extracting content: {e}")
        
        # Extract links
        print("\n\n🔗 Help Links Found:")
        print("=" * 80)
        
        try:
            links = await page.query_selector_all("a[href*='/help/']")
            help_links = []
            
            for link in links[:20]:  # First 20 links
                href = await link.get_attribute('href')
                text = await link.text_content()
                if href and '/help/hub/reference/external/G' in href:
                    help_links.append((href, text))
            
            if help_links:
                print(f"✅ Found {len(help_links)} help links matching pattern")
                print("\nSample links:")
                for href, text in help_links[:10]:
                    text_preview = text.strip()[:60] if text else "No text"
                    print(f"  - {href}")
                    print(f"    Text: {text_preview}")
            else:
                print("⚠️  No help links matching /help/hub/reference/external/G* pattern")
                
                # Show any help links found
                all_help_links = await page.query_selector_all("a[href*='/help/']")
                if all_help_links:
                    print(f"\n   Found {len(all_help_links)} general help links")
                    for link in all_help_links[:5]:
                        href = await link.get_attribute('href')
                        print(f"     - {href}")
        except Exception as e:
            print(f"❌ Error extracting links: {e}")
        
        # Take a screenshot for debugging
        screenshot_path = project_root / "scripts" / "debug_screenshot.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"\n📸 Screenshot saved to: {screenshot_path}")
        
        # Get page HTML
        html_content = await page.content()
        print(f"\n📄 Page HTML size: {len(html_content)} bytes")
        
        # Check if page has meaningful content
        body_text = await page.evaluate("() => document.body.innerText")
        print(f"📝 Body text length: {len(body_text)} characters")
        
        # Close browser
        await browser.close()
        print("\n✅ Browser closed")


async def main():
    """Run Playwright tests."""
    print("🐞 Playwright Content Extraction Debugger")
    print("=" * 100)
    print()
    
    test_urls = [
        "https://sellercentral.amazon.com/help/hub/reference/external/G2?locale=en-US",
    ]
    
    for i, url in enumerate(test_urls, 1):
        if i > 1:
            print("\n\n" + "=" * 100 + "\n")
        await test_with_playwright(url)
    
    print("\n\n" + "=" * 100)
    print("✅ Debug complete!")


if __name__ == "__main__":
    asyncio.run(main())

