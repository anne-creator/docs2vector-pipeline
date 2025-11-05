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

    # ============================================================================
    # Embedding Configuration
    # ============================================================================
    # Provider: "sentence-transformers" (local), "ollama" (local), "openai" (API)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
    
    # Model name (provider-specific)
    # - sentence-transformers: "BAAI/bge-small-en-v1.5", "all-MiniLM-L6-v2", "all-mpnet-base-v2"
    # - ollama: "nomic-embed-text", "mxbai-embed-large"
    # - openai: "text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    
    # Batch size for embedding generation
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # Ollama Configuration (for local Ollama server)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # OpenAI-Compatible API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_ORG_ID: str = os.getenv("OPENAI_ORG_ID", "")  # Optional
    
    # Embedding dimension (auto-detected if not set, or override for custom models)
    EMBEDDING_DIMENSION: Optional[int] = int(os.getenv("EMBEDDING_DIMENSION", "0")) or None

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
        
        # Validate embedding provider settings
        if cls.EMBEDDING_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when EMBEDDING_PROVIDER is 'openai'")
        
        if cls.EMBEDDING_PROVIDER not in ["sentence-transformers", "ollama", "openai"]:
            errors.append(
                f"Invalid EMBEDDING_PROVIDER: {cls.EMBEDDING_PROVIDER}. "
                "Must be 'sentence-transformers', 'ollama', or 'openai'"
            )

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
            f"EMBEDDING_PROVIDER={self.EMBEDDING_PROVIDER}, "
            f"EMBEDDING_MODEL={self.EMBEDDING_MODEL}, "
            f"CHUNK_SIZE={self.CHUNK_SIZE})"
        )

