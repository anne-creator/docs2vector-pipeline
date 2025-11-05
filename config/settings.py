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

    # ============================================================================
    # Storage Configuration
    # ============================================================================
    # Storage mode: "local" (data/ folder only), "s3" (AWS S3), "auto" (S3 if configured, else local)
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "auto")
    
    # Pipeline Processing Mode
    # "batch": Wait for all scraping to complete, then process all at once (traditional)
    # "streaming": Process items as they're scraped for concurrent stage execution (faster)
    PIPELINE_MODE: str = os.getenv("PIPELINE_MODE", "streaming")
    
    # Neo4j Configuration (OPTIONAL - disabled by default)
    USE_NEO4J: bool = os.getenv("USE_NEO4J", "false").lower() == "true"
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
    EMBEDDING_DIMENSION: Optional[int] = int(os.getenv("EMBEDDING_DIMENSION") or "0") or None

    # Scraper Configuration
    SCRAPER_DOWNLOAD_DELAY: float = float(os.getenv("SCRAPER_DOWNLOAD_DELAY", "1.0"))
    SCRAPER_CONCURRENT_REQUESTS: int = int(os.getenv("SCRAPER_CONCURRENT_REQUESTS", "2"))
    SCRAPER_DEPTH_LIMIT: int = int(os.getenv("SCRAPER_DEPTH_LIMIT", "4"))

    # Chunking Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

    # CSV Export Configuration
    CSV_INCLUDE_EMBEDDINGS: bool = os.getenv("CSV_INCLUDE_EMBEDDINGS", "true").lower() == "true"
    CSV_OUTPUT_DIR: Path = Path(os.getenv("CSV_OUTPUT_DIR", str(PROJECT_ROOT / "data" / "csv_export"))).resolve()

    # ============================================================================
    # Integration Configuration
    # ============================================================================
    # LlamaIndex Cloud Configuration
    LLAMAINDEX_API_KEY: str = os.getenv("LLAMAINDEX_API_KEY", "")
    LLAMAINDEX_BASE_URL: str = os.getenv("LLAMAINDEX_BASE_URL", "https://cloud.llamaindex.ai")
    LLAMAINDEX_PIPELINE_ID: str = os.getenv("LLAMAINDEX_PIPELINE_ID", "")

    # n8n Configuration
    N8N_BASE_URL: str = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")
    N8N_WEBHOOK_URL: str = os.getenv("N8N_WEBHOOK_URL", "")

    # ClickHouse Configuration
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_USERNAME: str = os.getenv("CLICKHOUSE_USERNAME", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    CLICKHOUSE_DATABASE: str = os.getenv("CLICKHOUSE_DATABASE", "default")

    # AWS S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required settings are present."""
        errors = []

        # Validate storage mode
        if cls.STORAGE_MODE not in ["local", "s3", "auto"]:
            errors.append(
                f"Invalid STORAGE_MODE: {cls.STORAGE_MODE}. "
                "Must be 'local', 's3', or 'auto'"
            )
        
        # Validate pipeline mode
        if cls.PIPELINE_MODE not in ["batch", "streaming"]:
            errors.append(
                f"Invalid PIPELINE_MODE: {cls.PIPELINE_MODE}. "
                "Must be 'batch' or 'streaming'"
            )
        
        # Validate S3 configuration if storage mode is s3
        if cls.STORAGE_MODE == "s3":
            if not cls.S3_BUCKET_NAME:
                errors.append("S3_BUCKET_NAME is required when STORAGE_MODE is 's3'")
            if not cls.AWS_ACCESS_KEY_ID:
                errors.append("AWS_ACCESS_KEY_ID is required when STORAGE_MODE is 's3'")
            if not cls.AWS_SECRET_ACCESS_KEY:
                errors.append("AWS_SECRET_ACCESS_KEY is required when STORAGE_MODE is 's3'")

        # Validate Neo4j configuration only if enabled
        if cls.USE_NEO4J:
            if not cls.NEO4J_URI:
                errors.append("NEO4J_URI is required when USE_NEO4J is enabled")
            if not cls.NEO4J_USERNAME:
                errors.append("NEO4J_USERNAME is required when USE_NEO4J is enabled")
            if not cls.NEO4J_PASSWORD:
                errors.append("NEO4J_PASSWORD is required when USE_NEO4J is enabled")
        
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
            "csv_export",
        ]
        for directory in directories:
            cls.get_data_path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {cls.get_data_path(directory)}")
    
    @classmethod
    def is_s3_configured(cls) -> bool:
        """Check if S3 credentials are configured."""
        return bool(
            cls.S3_BUCKET_NAME and 
            cls.AWS_ACCESS_KEY_ID and 
            cls.AWS_SECRET_ACCESS_KEY
        )
    
    @classmethod
    def get_effective_storage_mode(cls) -> str:
        """
        Get the effective storage mode based on configuration.
        
        Returns:
            "local" or "s3" based on STORAGE_MODE and available credentials
        """
        if cls.STORAGE_MODE == "local":
            return "local"
        elif cls.STORAGE_MODE == "s3":
            return "s3"
        elif cls.STORAGE_MODE == "auto":
            # Use S3 if configured, otherwise local
            return "s3" if cls.is_s3_configured() else "local"
        else:
            logger.warning(f"Unknown STORAGE_MODE: {cls.STORAGE_MODE}, defaulting to local")
            return "local"

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

