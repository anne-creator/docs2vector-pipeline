"""Model configurations for embedding generation."""

from typing import Dict, Any

from config.settings import Settings


class ModelConfig:
    """Configuration for embedding models."""

    # Default model configuration
    DEFAULT_MODEL = Settings.EMBEDDING_MODEL
    DEFAULT_BATCH_SIZE = Settings.EMBEDDING_BATCH_SIZE

    # Model specifications
    MODEL_SPECS: Dict[str, Dict[str, Any]] = {
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
    }

    @classmethod
    def get_model_dimension(cls, model_name: str) -> int:
        """
        Get embedding dimension for a model.

        Args:
            model_name: Name of the embedding model

        Returns:
            Embedding dimension
        """
        return cls.MODEL_SPECS.get(model_name, {}).get("dimension", 384)

    @classmethod
    def is_model_supported(cls, model_name: str) -> bool:
        """
        Check if a model is supported.

        Args:
            model_name: Name of the embedding model

        Returns:
            True if model is supported
        """
        return model_name in cls.MODEL_SPECS

