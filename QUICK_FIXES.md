# Quick Fixes for Scraper

## 🔴 **CRITICAL ISSUE IDENTIFIED**

The Amazon Seller Central help pages are **JavaScript-rendered** (SPA), but Scrapy doesn't execute JavaScript by default.

### Current Behavior
- ❌ Scrapes only 1 page instead of 10
- ❌ Extracts empty content (`text_content: ""`)
- ❌ Cannot find links to follow
- ❌ Hash file remains empty

### Root Cause
```
Raw HTML (what Scrapy sees):
<html>
  <body>
    <script>/* React/Angular app bundle */</script>
    <!-- No actual content here -->
  </body>
</html>

Rendered HTML (what browser sees):
<html>
  <body>
    <article>
      <h1>Help Article Title</h1>
      <p>Actual content here...</p>
      <a href="/help/...">Related Links</a>
    </article>
  </body>
</html>
```

---

## ✅ **SOLUTION: Add JavaScript Rendering**

### Option 1: Scrapy-Playwright (RECOMMENDED)

**Install:**
```bash
cd /Users/anne/Document/Dev/project/docs2vector-pipeline
pip install scrapy-playwright
playwright install chromium
```

**Update `requirements.txt`:**
```
scrapy-playwright>=0.0.34
```

**Modify `src/scraper/spider.py`:**

Add to custom_settings:
```python
custom_settings = {
    "DOWNLOAD_DELAY": Settings.SCRAPER_DOWNLOAD_DELAY,
    "CONCURRENT_REQUESTS": Settings.SCRAPER_CONCURRENT_REQUESTS,
    "ROBOTSTXT_OBEY": True,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "DEPTH_LIMIT": Settings.SCRAPER_DEPTH_LIMIT,
    
    # NEW: Add Playwright support
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    "PLAYWRIGHT_LAUNCH_OPTIONS": {
        "headless": True,
    },
}
```

Update parse methods:
```python
def parse_start_url(self, response):
    """Parse the start URL with Playwright."""
    return scrapy.Request(
        url=response.url,
        callback=self.parse_help_page,
        meta={
            "playwright": True,
            "playwright_page_methods": [
                ("wait_for_selector", "article, main, .content", {"timeout": 10000}),
            ],
        },
        dont_filter=True,
    )

def parse_help_page(self, response):
    """Parse article pages with rendered content."""
    # Rest of the method stays the same!
    # Content will now be available because JS has rendered it
    ...
```

**Test:**
```bash
python scripts/test_scraper_10pages.py
```

---

## 🔧 **Additional Quick Fixes**

### Fix 1: Consolidate Data Directory

**Problem:** Data is being saved to two locations (`data/` and `scripts/data/`)

**Fix:** Update `.env` or ensure scripts run from project root:
```bash
# Always run from project root
cd /Users/anne/Document/Dev/project/docs2vector-pipeline
python scripts/test_scraper_10pages.py
```

### Fix 2: Update CSS Selectors (After Playwright)

Once Playwright is working, test the actual selectors that work:
```bash
python scripts/debug_content_extraction.py
```

Then update selectors in `spider.py` based on what you find.

---

## 📋 **Step-by-Step Implementation**

### Step 1: Install (2 minutes)
```bash
cd /Users/anne/Document/Dev/project/docs2vector-pipeline
pip install scrapy-playwright
playwright install chromium
```

### Step 2: Update requirements.txt (1 minute)
Add: `scrapy-playwright>=0.0.34`

### Step 3: Update spider (10 minutes)
Modify `src/scraper/spider.py` with the code above

### Step 4: Test (2 minutes)
```bash
python scripts/test_scraper_10pages.py
```

### Step 5: Verify (1 minute)
Check output in `data/raw/` - should see:
- ✅ Multiple pages scraped (up to 10)
- ✅ Actual content in `text_content` field
- ✅ Links in `related_links` field

---

## 🎯 **Expected Results After Fix**

### Before (Current State)
```json
[
  {
    "url": "...",
    "title": "Amazon",
    "text_content": "",  // EMPTY
    "html_content": null,
    "related_links": []
  }
]
```

### After (With Playwright)
```json
[
  {
    "url": "...",
    "title": "How to list a product",
    "text_content": "To list a product on Amazon...",  // ACTUAL CONTENT
    "html_content": "<article>...</article>",
    "related_links": [
      {"text": "Product requirements", "url": "..."},
      {"text": "Pricing guidelines", "url": "..."}
    ]
  },
  // ... 9 more pages
]
```

---

## ⚡ **Performance Notes**

JavaScript rendering is slower than raw HTML scraping:
- Raw HTML: ~50-100 pages/minute
- With Playwright: ~5-10 pages/minute

**Optimization tips:**
1. Set `CONCURRENT_REQUESTS` to 1-2 (Playwright uses browser instances)
2. Increase `DOWNLOAD_DELAY` to 2-3 seconds
3. Disable images/CSS if not needed:
   ```python
   "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type in ["image", "stylesheet", "font"]
   ```

---

## 🆘 **If You Need Help**

1. Check Scrapy-Playwright docs: https://github.com/scrapy-plugins/scrapy-playwright
2. Test with debug scripts first
3. Check logs in `logs/` directory
4. Run integration tests: `pytest tests/integration/ -v`

---

## 📝 **Alternative: Use API (If Available)**

If Amazon has an API for help content:
1. Open browser DevTools on help page
2. Go to Network tab → Filter: XHR/Fetch
3. Look for JSON responses
4. Replicate API calls in Python

This would be MUCH faster than rendering!

