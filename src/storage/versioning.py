"""Version control for content tracking."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from ..utils.exceptions import StorageError
from config.settings import Settings

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages content versioning and change detection."""

    def __init__(self, hash_file: Optional[Path] = None):
        """
        Initialize VersionManager.

        Args:
            hash_file: Path to hash storage file (defaults to data/hashes/content_hashes.json)
        """
        if hash_file is None:
            hash_file = Settings.get_data_path("hashes", "content_hashes.json")
        self.hash_file = hash_file
        self.hash_file.parent.mkdir(parents=True, exist_ok=True)
        self._hashes: Dict[str, str] = self._load_hashes()

    def _load_hashes(self) -> Dict[str, str]:
        """
        Load content hashes from file.
        Example:
        {
            "https://sellercentral.amazon.com/help/hub/reference/external/G200141480": "a3f5b9c2d1e8...",
            "https://sellercentral.amazon.com/help/hub/reference/external/G1801": "f7e2a8b4c9d6..."
        }
        """
        if not self.hash_file.exists():
            logger.debug(f"Hash file not found, starting with empty hash store: {self.hash_file}")
            return {}

        # Load hashes from file
        try:
            # Open file and load hashes
            with open(self.hash_file, "r", encoding="utf-8") as f:
                hashes = json.load(f)
            logger.info(f"Loaded {len(hashes)} content hashes from {self.hash_file}")
            return hashes
        except Exception as e:
            # If error, log warning and return empty dictionary
            logger.warning(f"Error loading hashes, starting with empty store: {e}")
            return {}

    def _save_hashes(self) -> None:
        """Save content hashes to file."""
        try:
            with open(self.hash_file, "w", encoding="utf-8") as f:
                json.dump(self._hashes, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self._hashes)} content hashes to {self.hash_file}")
        except Exception as e:
            logger.error(f"Error saving hashes: {e}")
            raise StorageError(f"Failed to save hashes: {e}") from e

    def get_hash(self, url: str) -> Optional[str]:
        """
        Get stored hash for a URL.

        Args:
            url: Document URL

        Returns:
            Stored hash or None if not found
        """
        return self._hashes.get(url)

    def set_hash(self, url: str, content_hash: str, save: bool = True) -> None:
        """
        Store hash for a URL.

        Args:
            url: Document URL
            content_hash: Content hash string
            save: Whether to save to file immediately
        """
        self._hashes[url] = content_hash
        if save:
            self._save_hashes()

    def detect_change(self, url: str, current_hash: str) -> str:
        """
        Detect if content has changed.

        Args:
            url: Document URL
            current_hash: Current content hash

        Returns:
            Change status: 'new', 'updated', or 'unchanged'
        """
        stored_hash = self.get_hash(url)

        if stored_hash is None:
            return "new"
        elif stored_hash == current_hash:
            return "unchanged"
        else:
            return "updated"

    def update_hash(self, url: str, content_hash: str) -> str:
        """
        Update hash and return change status.

        Args:
            url: Document URL
            content_hash: Current content hash

        Returns:
            Change status: 'new', 'updated', or 'unchanged'
        """
        change_status = self.detect_change(url, content_hash)
        self.set_hash(url, content_hash, save=True)
        return change_status

    def get_all_urls(self) -> list[str]:
        """
        Get all tracked URLs.

        Returns:
            List of URLs
        """
        return list(self._hashes.keys())

    def save(self) -> None:
        """Explicitly save hashes to file."""
        self._save_hashes()

