"""Data validation utilities."""

from typing import List, Dict, Any, Optional


def validate_chunk(chunk: Dict[str, Any]) -> bool:
    """
    Validate that a chunk has required fields.

    Args:
        chunk: Dictionary containing chunk data

    Returns:
        True if chunk is valid
    """
    required_fields = ["content", "metadata"]
    return all(field in chunk for field in required_fields)


def validate_embedding(embedding: List[float]) -> bool:
    """
    Validate that an embedding is a list of numbers.

    Args:
        embedding: List of floating point numbers

    Returns:
        True if embedding is valid
    """
    if not isinstance(embedding, list):
        return False
    if len(embedding) == 0:
        return False
    return all(isinstance(x, (int, float)) for x in embedding)


def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate that metadata has required fields.

    Args:
        metadata: Dictionary containing metadata

    Returns:
        True if metadata is valid
    """
    required_fields = ["source_url"]
    return all(field in metadata for field in required_fields)


def validate_document(document: Dict[str, Any]) -> bool:
    """
    Validate that a document has required fields.

    Args:
        document: Dictionary containing document data

    Returns:
        True if document is valid
    """
    # Check for required fields: url, title, and either content or text_content
    has_url = "url" in document and document.get("url")
    has_title = "title" in document and document.get("title")
    has_content = ("content" in document and document.get("content")) or \
                  ("text_content" in document and document.get("text_content"))
    
    return has_url and has_title and has_content


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing excessive whitespace.

    Args:
        text: Input text string

    Returns:
        Sanitized text string
    """
    if not isinstance(text, str):
        return ""
    # Normalize whitespace
    text = " ".join(text.split())
    return text.strip()

