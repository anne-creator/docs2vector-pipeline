"""Content hashing utilities for change detection."""

import hashlib
from typing import Dict, Optional


def generate_hash(content: str, algorithm: str = "md5") -> str:
    """
    Generate a hash for content string.

    Args:
        content: The content string to hash
        algorithm: Hash algorithm to use (md5, sha256)

    Returns:
        Hexadecimal hash string
    """
    if algorithm == "md5":
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def compare_hashes(hash1: str, hash2: str) -> bool:
    """
    Compare two hash strings.

    Args:
        hash1: First hash string
        hash2: Second hash string

    Returns:
        True if hashes are equal, False otherwise
    """
    return hash1.lower() == hash2.lower()


def detect_change(
    current_content: str, stored_hash: Optional[str], algorithm: str = "md5"
) -> Dict[str, any]:
    """
    Detect if content has changed by comparing hashes.

    Args:
        current_content: Current content string
        stored_hash: Previously stored hash (None if new)
        algorithm: Hash algorithm to use

    Returns:
        Dictionary with change_status ('new', 'updated', 'unchanged') and hash
    """
    current_hash = generate_hash(current_content, algorithm)

    if stored_hash is None:
        change_status = "new"
    elif compare_hashes(current_hash, stored_hash):
        change_status = "unchanged"
    else:
        change_status = "updated"

    return {
        "change_status": change_status,
        "hash": current_hash,
        "previous_hash": stored_hash,
    }

