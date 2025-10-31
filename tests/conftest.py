"""Shared pytest fixtures and configuration."""
# Think of fixtures as: Pre-made test ingredients you can use in any test.


import pytest
import sys
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

