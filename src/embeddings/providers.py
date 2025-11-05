"""Embedding provider implementations."""

import logging
from typing import List, Optional
from abc import ABC, abstractmethod

from ..utils.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """Provider using local sentence-transformers models."""

    def __init__(self, model_name: str, device: Optional[str] = None):
        """Initialize SentenceTransformer provider."""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name, device=device)
            self.model_name = model_name
            logger.info(f"✅ Loaded sentence-transformers model: {model_name}")
        except Exception as e:
            raise EmbeddingError(f"Failed to load sentence-transformers model: {e}") from e

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        from .models import ModelConfig

        return ModelConfig.get_model_dimension(self.model_name, "sentence-transformers")


class OllamaProvider(EmbeddingProvider):
    """Provider using local Ollama server."""

    def __init__(self, model_name: str, base_url: str):
        """Initialize Ollama provider."""
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        logger.info(f"✅ Initialized Ollama provider: {model_name} at {base_url}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        import requests

        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            raise EmbeddingError(f"Ollama API error: {e}") from e

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.generate_embedding(text) for text in texts]

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        from .models import ModelConfig

        return ModelConfig.get_model_dimension(self.model_name, "ollama")


class OpenAIProvider(EmbeddingProvider):
    """Provider using OpenAI-compatible API."""

    def __init__(
        self, model_name: str, api_key: str, api_base: str, org_id: Optional[str] = None
    ):
        """Initialize OpenAI provider."""
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.org_id = org_id
        logger.info(f"✅ Initialized OpenAI-compatible provider: {model_name} at {api_base}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        import requests

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id

        try:
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=headers,
                json={"input": text, "model": self.model_name},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except Exception as e:
            raise EmbeddingError(f"OpenAI API error: {e}") from e

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        import requests

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id

        try:
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=headers,
                json={"input": texts, "model": self.model_name},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()["data"]
            # Sort by index to ensure correct order
            data.sort(key=lambda x: x["index"])
            return [item["embedding"] for item in data]
        except Exception as e:
            raise EmbeddingError(f"OpenAI API batch error: {e}") from e

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        from .models import ModelConfig

        return ModelConfig.get_model_dimension(self.model_name, "openai")

