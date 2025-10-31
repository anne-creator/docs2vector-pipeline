"""Unit tests for file manager."""

import pytest
import json
import tempfile
from pathlib import Path
from src.storage.file_manager import FileManager
from src.utils.exceptions import StorageError


class TestFileManager:
    """Test FileManager class."""

    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.file_manager = FileManager(base_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_raw_data(self):
        """Test saving and loading raw data."""
        data = [{"url": "http://test.com", "title": "Test"}]
        file_path = self.file_manager.save_raw_data(data, "test_raw.json")
        assert file_path.exists()

        loaded = self.file_manager.load_raw_data("test_raw.json")
        assert len(loaded) == 1
        assert loaded[0]["url"] == "http://test.com"

    def test_save_and_load_processed_documents(self):
        """Test saving and loading processed documents."""
        docs = [{"url": "http://test.com", "title": "Test", "markdown_content": "# Test"}]
        file_path = self.file_manager.save_processed_documents(docs, "test_processed.json")
        assert file_path.exists()

        loaded = self.file_manager.load_processed_documents("test_processed.json")
        assert len(loaded) == 1
        assert loaded[0]["url"] == "http://test.com"

    def test_save_and_load_chunks(self):
        """Test saving and loading chunks."""
        chunks = [{"id": "chunk1", "content": "Content", "metadata": {}}]
        file_path = self.file_manager.save_chunks(chunks, "test_chunks.json")
        assert file_path.exists()

        loaded = self.file_manager.load_chunks("test_chunks.json")
        assert len(loaded) == 1
        assert loaded[0]["id"] == "chunk1"

    def test_save_and_load_embeddings(self):
        """Test saving and loading embeddings."""
        chunks = [{"id": "chunk1", "content": "Content", "embedding": [0.1] * 384}]
        file_path = self.file_manager.save_embeddings(chunks, "test_embeddings.json")
        assert file_path.exists()

        loaded = self.file_manager.load_embeddings("test_embeddings.json")
        assert len(loaded) == 1
        assert len(loaded[0]["embedding"]) == 384

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(StorageError):
            self.file_manager.load_raw_data("nonexistent.json")

    def test_get_latest_file(self):
        """Test getting latest file in directory."""
        # Create multiple files with different timestamps
        data1 = [{"item": 1}]
        data2 = [{"item": 2}]
        self.file_manager.save_raw_data(data1, "file1.json")
        import time

        time.sleep(0.1)  # Ensure different timestamps
        self.file_manager.save_raw_data(data2, "file2.json")

        latest = self.file_manager.get_latest_file("raw", "*.json")
        assert latest is not None
        assert "file2.json" in latest.name

