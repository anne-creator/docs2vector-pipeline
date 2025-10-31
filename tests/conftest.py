"""Shared pytest fixtures and configuration."""
# Think of fixtures as: Pre-made test ingredients you can use in any test.


import pytest
import sys
import json
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture providing a temporary data directory."""
    return tmp_path / "data"


@pytest.fixture
def sample_html_content():
    """Fixture providing sample HTML content."""
    return """
    <html>
        <body>
            <article>
                <h1>Test Document</h1>
                <p>This is a test paragraph.</p>
                <h2>Section 1</h2>
                <p>Content in section 1.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def sample_markdown_content():
    """Fixture providing sample Markdown content."""
    return """# Test Document

This is a test paragraph.

## Section 1

Content in section 1.

- Item 1
- Item 2
"""


# ============================================================================
# Real Scraped Data Fixtures
# ============================================================================
# These fixtures load actual data from test scraper runs (tests/.test_data/)
# Run scripts/test_scraper_10pages.py first to generate the data


@pytest.fixture(scope="session")
def real_scraped_data():
    """Fixture providing real scraped data from test run.
    
    This loads the most recent raw data file from tests/.test_data/raw/
    The data comes from running scripts/test_scraper_10pages.py
    
    Returns:
        list: List of scraped items (documents) with real content
        
    Skips:
        If no real scraped data is found
    """
    test_data_dir = Path(__file__).parent / ".test_data" / "raw"
    
    # Find the most recent raw data file
    raw_files = list(test_data_dir.glob("raw_data_*.json"))
    if not raw_files:
        pytest.skip("No real scraped data found. Run scripts/test_scraper_10pages.py first.")
    
    # Get the most recent file
    latest_file = max(raw_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    return data


@pytest.fixture
def single_scraped_item(real_scraped_data):
    """Fixture providing a single item from real scraped data.
    
    Use this when you need to test with one real document.
    
    Returns:
        dict: A single scraped item with fields like:
            - url: Document URL
            - title: Document title
            - html_content: Raw HTML content
            - text_content: Plain text content
            - last_updated: Last update date
            - breadcrumbs: Navigation breadcrumbs
            - metadata: Additional metadata
    """
    if not real_scraped_data:
        pytest.skip("No scraped data available")
    return real_scraped_data[0]


@pytest.fixture
def multiple_scraped_items(real_scraped_data):
    """Fixture providing multiple items from real scraped data.
    
    Use this when you need to test batch processing with multiple real documents.
    Returns the first 5 items (or all if less than 5).
    
    Returns:
        list: List of scraped items (up to 5 documents)
    """
    if not real_scraped_data:
        pytest.skip("No scraped data available")
    
    # Return first 5 items or all if less than 5
    return real_scraped_data[:5] if len(real_scraped_data) >= 5 else real_scraped_data


@pytest.fixture
def all_scraped_items(real_scraped_data):
    """Fixture providing all items from real scraped data.
    
    Use this when you need to test with the complete dataset (typically 10 pages).
    
    Returns:
        list: All scraped items from the test run
    """
    if not real_scraped_data:
        pytest.skip("No scraped data available")
    return real_scraped_data

