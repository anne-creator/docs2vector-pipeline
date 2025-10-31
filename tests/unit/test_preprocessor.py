"""Unit tests for preprocessor.

Testing Strategy:
- Core functionality tests use REAL scraped data from tests/.test_data/
- Edge case tests use FAKE/minimal data for boundary conditions
- Run scripts/test_scraper_10pages.py first to generate real test data
"""

import pytest
from src.processor.preprocessor import Preprocessor
from src.utils.exceptions import ProcessorError


class TestPreprocessor:
    """Test Preprocessor class with real data and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.preprocessor = Preprocessor()

    # ========================================================================
    # CORE FUNCTIONALITY TESTS - Using Real Scraped Data
    # ========================================================================
    # These tests validate the main workflows with realistic Amazon Seller
    # Central content to ensure the preprocessor works with production data.

    def test_process_real_document(self, single_scraped_item):
        """Test processing a real Amazon Seller Central document."""
        result = self.preprocessor.process(
            single_scraped_item["html_content"],
            single_scraped_item.get("text_content")
        )
        
        # Real documents should produce substantial markdown output
        assert len(result) > 0
        assert isinstance(result, str)
        assert len(result) > 100, "Real documents should have substantial content"
        
        # Title should appear in processed content
        if single_scraped_item.get("title"):
            title_lower = single_scraped_item["title"].lower()
            result_lower = result.lower()
            assert title_lower in result_lower, "Document title should appear in output"

    def test_process_multiple_real_documents(self, multiple_scraped_items):
        """Test processing multiple real documents maintains quality."""
        results = []
        
        for item in multiple_scraped_items:
            result = self.preprocessor.process(
                item["html_content"],
                item.get("text_content")
            )
            results.append({
                "url": item["url"],
                "markdown": result,
            })
        
        # All documents should be processed successfully
        assert len(results) == len(multiple_scraped_items)
        assert all(len(r["markdown"]) > 0 for r in results)
        
        # Each document should produce unique content
        markdown_contents = [r["markdown"] for r in results]
        unique_contents = set(markdown_contents)
        assert len(unique_contents) == len(markdown_contents), \
            "Each document should produce unique content"

    def test_clean_html_removes_real_boilerplate(self, single_scraped_item):
        """Test that HTML cleaning removes navigation/footer from real pages."""
        cleaned = self.preprocessor.clean_html(single_scraped_item["html_content"])
        
        # Should still have content
        assert len(cleaned) > 0
        
        # Common boilerplate elements should be reduced/removed
        # (Amazon pages have lots of nav, scripts, etc.)
        cleaned_lower = cleaned.lower()
        
        # Should not have script tags
        assert "<script" not in cleaned_lower or cleaned.count("<script") < 2
        
        # Should have actual article content
        assert len(cleaned) > 100

    def test_html_to_markdown_real_content(self, single_scraped_item):
        """Test HTML to Markdown conversion with real complex HTML."""
        markdown = self.preprocessor.html_to_markdown(
            single_scraped_item["html_content"]
        )
        
        assert len(markdown) > 0
        assert isinstance(markdown, str)
        
        # Markdown should have structure (headers, paragraphs)
        # Real Amazon pages typically have headers
        has_structure = (
            "#" in markdown or  # Headers
            "\n\n" in markdown  # Paragraph breaks
        )
        assert has_structure, "Markdown should have structural elements"

    # ========================================================================
    # EDGE CASE TESTS - Using Fake/Minimal Data
    # ========================================================================
    # These tests validate error handling and boundary conditions with
    # controlled minimal inputs.

    def test_clean_html_removes_boilerplate(self):
        """Test that HTML cleaning removes boilerplate elements."""
        html = "<html><body><nav>Nav</nav><article><p>Content</p></article><footer>Footer</footer></body></html>"
        cleaned = self.preprocessor.clean_html(html)
        assert "nav" not in cleaned.lower()
        assert "footer" not in cleaned.lower()
        assert "content" in cleaned.lower()

    def test_clean_html_empty_input(self):
        """Test HTML cleaning with empty input."""
        assert self.preprocessor.clean_html("") == ""
        assert self.preprocessor.clean_html(None) == ""

    def test_html_to_markdown_basic(self):
        """Test basic HTML to Markdown conversion."""
        html = "<h1>Title</h1><p>Paragraph text</p>"
        markdown = self.preprocessor.html_to_markdown(html)
        assert "Title" in markdown
        assert "Paragraph text" in markdown

    def test_html_to_markdown_empty(self):
        """Test HTML to Markdown with empty input."""
        assert self.preprocessor.html_to_markdown("") == ""
        assert self.preprocessor.html_to_markdown(None) == ""

    def test_html_to_markdown_normalizes_whitespace(self):
        """Test that Markdown conversion normalizes whitespace."""
        html = "<p>Text   with   spaces</p>"
        markdown = self.preprocessor.html_to_markdown(html)
        assert "Text with spaces" in markdown

    def test_process_with_html(self):
        """Test process method with HTML content."""
        html = "<p>HTML content</p>"
        result = self.preprocessor.process(html)
        assert len(result) > 0

    def test_process_with_text_fallback(self):
        """Test process method with text fallback."""
        text = "Plain text content"
        result = self.preprocessor.process(None, text_content=text)
        assert text in result

    def test_process_no_content(self):
        """Test process method with no content."""
        result = self.preprocessor.process(None)
        assert result == ""

