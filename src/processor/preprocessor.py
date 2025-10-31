"""HTML cleaning and Markdown conversion."""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from ..utils.exceptions import ProcessorError
from ..utils.validators import sanitize_text

logger = logging.getLogger(__name__)


class Preprocessor:
    """Preprocesses HTML content to Markdown."""

    def __init__(self):
        """Initialize preprocessor."""
        self.boilerplate_selectors = [
            "nav",
            "footer",
            ".ads",
            ".navigation",
            ".sidebar",
            "script",
            "style",
            ".header",
            ".header-menu",
            ".cookie-banner",
        ]

    def clean_html(self, html_content: str) -> str:
        """
        Clean HTML by removing unnecessary elements.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned HTML string
        """
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove boilerplate elements
            for selector in self.boilerplate_selectors:
                for element in soup.select(selector):
                    element.decompose()

            return str(soup)
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            raise ProcessorError(f"Failed to clean HTML: {e}") from e

    def html_to_markdown(self, html_content: Optional[str]) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html_content: HTML content string

        Returns:
            Markdown string
        """
        if not html_content:
            return ""

        try:
            # Clean the HTML first
            clean_html = self.clean_html(html_content)

            # Convert to Markdown
            markdown = md(
                clean_html,
                heading_style="ATX",  # Use # for headings
                bullets="-",  # Use - for lists
            )

            # Clean up the markdown
            # Remove excessive newlines
            markdown = re.sub(r"\n{3,}", "\n\n", markdown)

            # Normalize whitespace
            markdown = sanitize_text(markdown)

            return markdown
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {e}")
            raise ProcessorError(f"Failed to convert HTML to Markdown: {e}") from e

    def process(self, html_content: Optional[str], text_content: Optional[str] = None) -> str:
        """
        Process content: convert HTML to Markdown or use text content as fallback.

        Args:
            html_content: HTML content (preferred)
            text_content: Plain text content (fallback)

        Returns:
            Processed Markdown content
        """
        if html_content:
            return self.html_to_markdown(html_content)
        elif text_content:
            return sanitize_text(text_content)
        else:
            logger.warning("No content provided for processing")
            return ""

