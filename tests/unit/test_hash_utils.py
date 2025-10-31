"""Unit tests for hash utilities."""

import pytest
from src.utils.hash_utils import (
    generate_hash,
    compare_hashes,
    detect_change,
)


class TestHashUtils:
    """Test hash utility functions."""

    def test_generate_hash_md5(self):
        """Test MD5 hash generation."""
        content = "test content"
        hash_value = generate_hash(content, algorithm="md5")
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5 produces 32 character hex string
        assert hash_value == generate_hash(content, algorithm="md5")  # Deterministic

    def test_generate_hash_sha256(self):
        """Test SHA256 hash generation."""
        content = "test content"
        hash_value = generate_hash(content, algorithm="sha256")
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 character hex string

    def test_generate_hash_invalid_algorithm(self):
        """Test hash generation with invalid algorithm."""
        with pytest.raises(ValueError):
            generate_hash("test", algorithm="invalid")

    def test_compare_hashes_equal(self):
        """Test hash comparison with equal hashes."""
        hash1 = "abc123"
        hash2 = "abc123"
        assert compare_hashes(hash1, hash2) is True

    def test_compare_hashes_different(self):
        """Test hash comparison with different hashes."""
        hash1 = "abc123"
        hash2 = "def456"
        assert compare_hashes(hash1, hash2) is False

    def test_compare_hashes_case_insensitive(self):
        """Test hash comparison is case insensitive."""
        hash1 = "ABC123"
        hash2 = "abc123"
        assert compare_hashes(hash1, hash2) is True

    def test_detect_change_new(self):
        """Test change detection for new content."""
        result = detect_change("new content", None)
        assert result["change_status"] == "new"
        assert result["hash"] is not None
        assert result["previous_hash"] is None

    def test_detect_change_unchanged(self):
        """Test change detection for unchanged content."""
        content = "same content"
        current_hash = generate_hash(content)
        result = detect_change(content, current_hash)
        assert result["change_status"] == "unchanged"
        assert result["hash"] == current_hash

    def test_detect_change_updated(self):
        """Test change detection for updated content."""
        old_hash = generate_hash("old content")
        result = detect_change("new content", old_hash)
        assert result["change_status"] == "updated"
        assert result["hash"] != old_hash
        assert result["previous_hash"] == old_hash

