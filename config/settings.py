"""Centralized configuration management with environment variable support."""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get project root directory (where config/ is located)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


class Settings:
    """Application settings loaded from environment variables with defaults."""

    # Neo4j Aura Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Pipeline Configuration - Always use project root (absolute path)
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data"))).resolve()
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Embedding Model Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    # Scraper Configuration
    SCRAPER_DOWNLOAD_DELAY: float = float(os.getenv("SCRAPER_DOWNLOAD_DELAY", "1.0"))
    SCRAPER_CONCURRENT_REQUESTS: int = int(os.getenv("SCRAPER_CONCURRENT_REQUESTS", "2"))
    SCRAPER_DEPTH_LIMIT: int = int(os.getenv("SCRAPER_DEPTH_LIMIT", "4"))

    # Chunking Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

    @classmethod
    def validate(cls) -> bool:
        """Validate that required settings are present."""
        errors = []

        if not cls.NEO4J_URI:
            errors.append("NEO4J_URI is required")

        if not cls.NEO4J_USERNAME:
            errors.append("NEO4J_USERNAME is required")

        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD is required")

        if errors:
            logger.error(f"Configuration validation failed: {', '.join(errors)}")
            return False

        return True

    
    @classmethod
    def get_data_path(cls, *subpaths: str) -> Path:
        """Get a path within the data directory."""
        return cls.DATA_DIR.joinpath(*subpaths)

    @classmethod
    def ensure_data_directories(cls) -> None:
        """Ensure all required data directories exist."""
        directories = [
            "raw",
            "processed",
            "chunks",
            "embeddings",
            "hashes",
            "manifests",
        ]
        for directory in directories:
            cls.get_data_path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {cls.get_data_path(directory)}")

    def __repr__(self) -> str:
        """String representation of settings (without sensitive data)."""
        return (
            f"Settings("
            f"NEO4J_URI={self.NEO4J_URI}, "
            f"NEO4J_DATABASE={self.NEO4J_DATABASE}, "
            f"DATA_DIR={self.DATA_DIR}, "
            f"EMBEDDING_MODEL={self.EMBEDDING_MODEL}, "
            f"CHUNK_SIZE={self.CHUNK_SIZE})"
        )

