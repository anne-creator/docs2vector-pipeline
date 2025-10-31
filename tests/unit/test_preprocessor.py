"""Unit tests for preprocessor."""

import pytest
from src.processor.preprocessor import Preprocessor
from src.utils.exceptions import ProcessorError


class TestPreprocessor:
    """Test Preprocessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.preprocessor = Preprocessor()

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

