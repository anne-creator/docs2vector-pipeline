"""Local file storage management."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.exceptions import StorageError
from config.settings import Settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manages local file storage operations."""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize FileManager.

        Args:
            base_dir: Base directory for data storage (defaults to Settings.DATA_DIR)
        """
        self.base_dir = base_dir or Settings.DATA_DIR
        logger.debug(f"FileManager initialized (base_dir: {self.base_dir})")
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Ensure all required data directories exist."""
        directories = ["raw", "processed", "chunks", "embeddings", "hashes", "manifests", "csv_export"]
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")

    def save_raw_data(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """
        Save raw scraped data to JSON file.

        Args:
            data: List of scraped items
            filename: Optional filename (defaults to timestamped name)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_data_{timestamp}.json"

        file_path = self.base_dir / "raw" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            logger.debug(f"Saving {len(data)} items to {file_path}...")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Saved {len(data)} items to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"❌ Error saving raw data: {e}")
            raise StorageError(f"Failed to save raw data: {e}") from e

    def load_raw_data(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load raw scraped data from JSON file.

        Args:
            filename: Name of the file to load

        Returns:
            List of scraped items
        """
        file_path = self.base_dir / "raw" / filename
        if not file_path.exists():
            raise StorageError(f"Raw data file not found: {file_path}")

        try:
            logger.debug(f"Loading raw data from {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"✅ Loaded {len(data)} items from {file_path}")
            return data
        except Exception as e:
            logger.error(f"❌ Error loading raw data: {e}")
            raise StorageError(f"Failed to load raw data: {e}") from e

    def save_processed_documents(
        self, documents: List[Dict[str, Any]], filename: Optional[str] = None
    ) -> Path:
        """
        Save processed documents to JSON file.

        Args:
            documents: List of processed documents
            filename: Optional filename (defaults to timestamped name)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"processed_docs_{timestamp}.json"

        file_path = self.base_dir / "processed" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(documents)} processed documents to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving processed documents: {e}")
            raise StorageError(f"Failed to save processed documents: {e}") from e

    def load_processed_documents(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load processed documents from JSON file.

        Args:
            filename: Name of the file to load

        Returns:
            List of processed documents
        """
        file_path = self.base_dir / "processed" / filename
        if not file_path.exists():
            raise StorageError(f"Processed documents file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} processed documents from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading processed documents: {e}")
            raise StorageError(f"Failed to load processed documents: {e}") from e

    def save_chunks(self, chunks: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """
        Save chunks to JSON file.

        Args:
            chunks: List of chunks
            filename: Optional filename (defaults to timestamped name)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chunks_{timestamp}.json"

        file_path = self.base_dir / "chunks" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(chunks)} chunks to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving chunks: {e}")
            raise StorageError(f"Failed to save chunks: {e}") from e

    def load_chunks(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load chunks from JSON file.

        Args:
            filename: Name of the file to load

        Returns:
            List of chunks
        """
        file_path = self.base_dir / "chunks" / filename
        if not file_path.exists():
            raise StorageError(f"Chunks file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} chunks from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            raise StorageError(f"Failed to load chunks: {e}") from e

    def save_embeddings(
        self, chunks_with_embeddings: List[Dict[str, Any]], filename: Optional[str] = None
    ) -> Path:
        """
        Save chunks with embeddings to JSON file.

        Args:
            chunks_with_embeddings: List of chunks with embeddings
            filename: Optional filename (defaults to timestamped name)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chunks_with_embeddings_{timestamp}.json"

        file_path = self.base_dir / "embeddings" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(chunks_with_embeddings, f, ensure_ascii=False)
            logger.info(f"Saved {len(chunks_with_embeddings)} chunks with embeddings to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            raise StorageError(f"Failed to save embeddings: {e}") from e

    def load_embeddings(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load chunks with embeddings from JSON file.

        Args:
            filename: Name of the file to load

        Returns:
            List of chunks with embeddings
        """
        file_path = self.base_dir / "embeddings" / filename
        if not file_path.exists():
            raise StorageError(f"Embeddings file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} chunks with embeddings from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            raise StorageError(f"Failed to load embeddings: {e}") from e

    def get_latest_file(self, subdirectory: str, pattern: str = "*.json") -> Optional[Path]:
        """
        Get the latest file matching a pattern in a subdirectory.

        Args:
            subdirectory: Subdirectory name (raw, processed, chunks, etc.)
            pattern: File pattern to match

        Returns:
            Path to latest file or None if no files found
        """
        directory = self.base_dir / subdirectory
        if not directory.exists():
            return None

        files = list(directory.glob(pattern))
        if not files:
            return None

        # Return most recently modified file
        return max(files, key=lambda p: p.stat().st_mtime)

