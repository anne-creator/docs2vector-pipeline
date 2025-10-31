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
        logger.debug(f"Batch size: {self.batch_size}, Device: {device or 'auto'}")
        try:
            self.model = SentenceTransformer(self.model_name, device=device)
            dimension = self.get_dimension()
            logger.info(f"✅ Model loaded successfully (dimension: {dimension})")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
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
            logger.debug(f"Generating embedding for text ({len(text)} chars)...")
            embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            logger.debug(f"Generated embedding with dimension {len(embedding)}")
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
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
            logger.debug("Empty text list provided for batch embedding")
            return []

        try:
            logger.debug(f"Generating batch embeddings for {len(texts)} texts...")
            embeddings = self.model.encode(
                texts, convert_to_numpy=True, show_progress_bar=False, batch_size=self.batch_size
            )
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating batch embeddings: {e}")
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
            logger.warning("⚠️  No chunks to process")
            return []

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        logger.debug(f"Model: {self.model_name}, Batch size: {self.batch_size}")

        # Extract texts to embed
        texts = [chunk.get("content", "") for chunk in chunks]

        # Process in batches to avoid memory issues
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        logger.debug(f"Processing in {total_batches} batches...")

        for i in tqdm(range(0, len(texts), self.batch_size), desc="Generating embeddings"):
            batch_num = i // self.batch_size + 1
            batch_texts = texts[i : i + self.batch_size]
            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} chunks)...")
            try:
                batch_embeddings = self.generate_embeddings_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"❌ Error processing batch {batch_num}: {e}")
                raise EmbeddingError(f"Failed to process batch: {e}") from e

        # Add embeddings to chunks and validate
        logger.debug("Validating and adding embeddings to chunks...")
        invalid_count = 0
        for i, chunk in enumerate(chunks):
            embedding = all_embeddings[i]
            if validate_embedding(embedding):
                chunk["embedding"] = embedding
            else:
                logger.warning(f"⚠️  Invalid embedding generated for chunk {chunk.get('id', i)}")
                invalid_count += 1
                # Generate a zero embedding as fallback
                dimension = self.get_dimension()
                chunk["embedding"] = [0.0] * dimension

        if invalid_count > 0:
            logger.warning(f"⚠️  {invalid_count} invalid embeddings replaced with zero vectors")

        logger.info(f"✅ Successfully generated embeddings for {len(chunks)} chunks")
        return chunks

