"""Embedding generation service."""

import logging
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from ..utils.exceptions import EmbeddingError
from ..utils.validators import validate_embedding
from config.settings import Settings
from .models import ModelConfig

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates vector embeddings for text chunks."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        batch_size: Optional[int] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize embedding generator.

        Args:
            model_name: Name of the embedding model
            batch_size: Batch size for processing
            device: Device to use ('cpu', 'cuda', etc.)
        """
        self.model_name = model_name or ModelConfig.DEFAULT_MODEL
        self.batch_size = batch_size or ModelConfig.DEFAULT_BATCH_SIZE

        logger.info(f"Loading embedding model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name, device=device)
            logger.info(f"Loaded model with dimension {self.get_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingError(f"Failed to load embedding model: {e}") from e

    def get_dimension(self) -> int:
        """
        Get embedding dimension for current model.

        Returns:
            Embedding dimension
        """
        return ModelConfig.get_model_dimension(self.model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text string

        Returns:
            Embedding vector as list of floats
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts, convert_to_numpy=True, show_progress_bar=False, batch_size=self.batch_size
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e

    def process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process chunks and add embeddings.

        Args:
            chunks: List of chunk dictionaries with 'content' field

        Returns:
            List of chunks with added 'embedding' field
        """
        if not chunks:
            logger.warning("No chunks to process")
            return []

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Extract texts to embed
        texts = [chunk.get("content", "") for chunk in chunks]

        # Process in batches to avoid memory issues
        all_embeddings = []

        for i in tqdm(range(0, len(texts), self.batch_size), desc="Generating embeddings"):
            batch_texts = texts[i : i + self.batch_size]
            try:
                batch_embeddings = self.generate_embeddings_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error processing batch {i // self.batch_size + 1}: {e}")
                raise EmbeddingError(f"Failed to process batch: {e}") from e

        # Add embeddings to chunks and validate
        for i, chunk in enumerate(chunks):
            embedding = all_embeddings[i]
            if validate_embedding(embedding):
                chunk["embedding"] = embedding
            else:
                logger.warning(f"Invalid embedding generated for chunk {chunk.get('id', i)}")
                # Generate a zero embedding as fallback
                dimension = self.get_dimension()
                chunk["embedding"] = [0.0] * dimension

        logger.info(f"Successfully generated embeddings for {len(chunks)} chunks")
        return chunks

