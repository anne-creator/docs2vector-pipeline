"""Model configurations for embedding generation."""

from typing import Dict, Any, Optional
import logging

from config.settings import Settings

logger = logging.getLogger(__name__)


class ModelConfig:
    """Configuration for embedding models across different providers."""

    # Default configuration from settings
    DEFAULT_PROVIDER = Settings.EMBEDDING_PROVIDER
    DEFAULT_MODEL = Settings.EMBEDDING_MODEL
    DEFAULT_BATCH_SIZE = Settings.EMBEDDING_BATCH_SIZE

    # Model specifications by provider
    MODEL_SPECS: Dict[str, Dict[str, Dict[str, Any]]] = {
        "sentence-transformers": {
            "BAAI/bge-small-en-v1.5": {
                "dimension": 384,
                "max_tokens": 512,
                "description": "High-quality BGE model, excellent performance-to-size ratio",
            },
            "all-MiniLM-L6-v2": {
                "dimension": 384,
                "max_tokens": 256,
                "description": "Fast and efficient model, good balance of speed and quality",
            },
            "all-mpnet-base-v2": {
                "dimension": 768,
                "max_tokens": 384,
                "description": "Higher quality embeddings, slower than MiniLM",
            },
        },
        "ollama": {
            "nomic-embed-text": {
                "dimension": 768,
                "max_tokens": 8192,
                "description": "High-quality open embedding model optimized for long context",
            },
            "mxbai-embed-large": {
                "dimension": 1024,
                "max_tokens": 512,
                "description": "Large embedding model with excellent performance",
            },
        },
        "openai": {
            "text-embedding-3-small": {
                "dimension": 1536,
                "max_tokens": 8191,
                "description": "OpenAI's efficient and cost-effective embedding model",
            },
            "text-embedding-3-large": {
                "dimension": 3072,
                "max_tokens": 8191,
                "description": "OpenAI's most powerful embedding model",
            },
            "text-embedding-ada-002": {
                "dimension": 1536,
                "max_tokens": 8191,
                "description": "Legacy OpenAI embedding model (still supported)",
            },
        },
    }

    @classmethod
    def get_model_dimension(cls, model_name: str, provider: Optional[str] = None) -> int:
        """
        Get embedding dimension for a model.

        Args:
            model_name: Name of the embedding model
            provider: Provider name (defaults to DEFAULT_PROVIDER)

        Returns:
            Embedding dimension
        """
        provider = provider or cls.DEFAULT_PROVIDER
        
        # Check if custom dimension is set in settings
        if Settings.EMBEDDING_DIMENSION:
            logger.info(f"Using custom embedding dimension: {Settings.EMBEDDING_DIMENSION}")
            return Settings.EMBEDDING_DIMENSION
        
        # Look up dimension from specs
        if provider in cls.MODEL_SPECS and model_name in cls.MODEL_SPECS[provider]:
            return cls.MODEL_SPECS[provider][model_name]["dimension"]
        
        # Default fallback
        logger.warning(
            f"Unknown model {model_name} for provider {provider}, defaulting to 384 dimensions"
        )
        return 384

    @classmethod
    def is_model_supported(cls, model_name: str, provider: Optional[str] = None) -> bool:
        """
        Check if a model is supported.

        Args:
            model_name: Name of the embedding model
            provider: Provider name (defaults to DEFAULT_PROVIDER)

        Returns:
            True if model is supported
        """
        provider = provider or cls.DEFAULT_PROVIDER
        return provider in cls.MODEL_SPECS and model_name in cls.MODEL_SPECS[provider]

    @classmethod
    def get_provider_models(cls, provider: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all available models for a provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary of model specifications
        """
        return cls.MODEL_SPECS.get(provider, {})

