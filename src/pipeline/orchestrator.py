"""Main pipeline orchestrator coordinating all stages."""

import logging
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..processor.preprocessor import Preprocessor
from ..processor.chunker import SemanticChunker
from ..processor.metadata import MetadataExtractor
from ..embeddings.generator import EmbeddingGenerator
from ..storage.file_manager import FileManager
from ..storage.neo4j_client import Neo4jClient
from ..utils.exceptions import PipelineError

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete pipeline execution."""

    def __init__(self):
        """Initialize orchestrator with all pipeline components."""
        self.preprocessor = Preprocessor()
        self.chunker = SemanticChunker()
        self.metadata_extractor = MetadataExtractor()
        self.embedding_generator = EmbeddingGenerator()
        self.file_manager = FileManager()
        self.neo4j_client: Optional[Neo4jClient] = None

    def connect_neo4j(self) -> None:
        """Connect to Neo4j database."""
        try:
            self.neo4j_client = Neo4jClient()
            self.neo4j_client.initialize_schema()
            # Get embedding dimension for vector index
            dimension = self.embedding_generator.get_dimension()
            self.neo4j_client.create_vector_index(dimension)
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise PipelineError(f"Failed to connect to Neo4j: {e}") from e

    def run_scraper(self) -> Path:
        """
        Run the Scrapy spider to scrape data.

        Returns:
            Path to saved raw data file
        """
        logger.info("Starting scraper...")
        try:
            # Run scrapy crawl command
            result = subprocess.run(
                ["scrapy", "crawl", "amazon_seller_help"],
                cwd="scrapy_project",
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"Scrapy error: {result.stderr}")
                raise PipelineError(f"Scrapy crawl failed: {result.stderr}")

            # Find the latest raw data file
            raw_file = self.file_manager.get_latest_file("raw")
            if raw_file is None:
                raise PipelineError("No raw data file found after scraping")

            logger.info(f"Scraping completed. Data saved to: {raw_file}")
            return raw_file
        except Exception as e:
            logger.error(f"Error running scraper: {e}")
            raise PipelineError(f"Failed to run scraper: {e}") from e

    def process_documents(self, raw_data_file: Path) -> List[Dict[str, Any]]:
        """
        Process raw scraped data into cleaned documents.

        Args:
            raw_data_file: Path to raw data JSON file

        Returns:
            List of processed documents
        """
        logger.info(f"Processing documents from {raw_data_file}...")

        # Load raw data
        raw_data = self.file_manager.load_raw_data(raw_data_file.name)
        processed_documents = []

        for item in raw_data:
            try:
                # Extract metadata
                metadata = self.metadata_extractor.extract(item)

                # Process content (HTML to Markdown)
                html_content = item.get("html_content", "")
                text_content = item.get("text_content", "")
                markdown_content = self.preprocessor.process(html_content, text_content)

                # Create processed document
                processed_doc = {
                    "url": item["url"],
                    "title": item.get("title", "Untitled"),
                    "markdown_content": markdown_content,
                    "last_updated": item.get("last_updated", ""),
                    "metadata": metadata,
                }

                processed_documents.append(processed_doc)
            except Exception as e:
                logger.warning(f"Error processing document {item.get('url', 'Unknown')}: {e}")
                continue

        # Save processed documents
        self.file_manager.save_processed_documents(processed_documents)
        logger.info(f"Processed {len(processed_documents)} documents")

        return processed_documents

    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk processed documents.

        Args:
            documents: List of processed documents

        Returns:
            List of chunks
        """
        logger.info(f"Chunking {len(documents)} documents...")

        try:
            chunks = self.chunker.process_documents(documents)
            self.file_manager.save_chunks(chunks)
            logger.info(f"Created {len(chunks)} chunks")

            return chunks
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            raise PipelineError(f"Failed to chunk documents: {e}") from e

    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks.

        Args:
            chunks: List of chunks

        Returns:
            List of chunks with embeddings
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        try:
            chunks_with_embeddings = self.embedding_generator.process_chunks(chunks)
            self.file_manager.save_embeddings(chunks_with_embeddings)
            logger.info(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")

            return chunks_with_embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise PipelineError(f"Failed to generate embeddings: {e}") from e

    def load_to_neo4j(self, chunks_with_embeddings: List[Dict[str, Any]]) -> None:
        """
        Load chunks with embeddings into Neo4j.

        Args:
            chunks_with_embeddings: List of chunks with embeddings
        """
        if self.neo4j_client is None:
            self.connect_neo4j()

        logger.info(f"Loading {len(chunks_with_embeddings)} chunks to Neo4j...")

        try:
            self.neo4j_client.batch_upsert_chunks(chunks_with_embeddings)
            logger.info(f"Successfully loaded {len(chunks_with_embeddings)} chunks to Neo4j")
        except Exception as e:
            logger.error(f"Error loading to Neo4j: {e}")
            raise PipelineError(f"Failed to load to Neo4j: {e}") from e

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete pipeline from scraping to Neo4j loading.

        Returns:
            Dictionary with execution results
        """
        logger.info("=" * 70)
        logger.info("🚀 STARTING FULL PIPELINE")
        logger.info("=" * 70)

        results = {
            "raw_data_file": None,
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "chunks_loaded": 0,
            "success": False,
        }

        try:
            # Stage 1: Scrape
            logger.info("")
            logger.info("📡 STAGE 1/5: SCRAPING")
            logger.info("-" * 70)
            try:
                raw_data_file = self.run_scraper()
                results["raw_data_file"] = str(raw_data_file)
                logger.info(f"✅ Scraper completed successfully")
            except Exception as e:
                logger.error(f"❌ Scraping failed: {e}")
                results["error"] = str(e)
                results["stage"] = "scraper"
                return results

            # Stage 2: Process
            logger.info("")
            logger.info("⚙️  STAGE 2/5: PROCESSING")
            logger.info("-" * 70)
            try:
                processed_docs = self.process_documents(raw_data_file)
                results["documents_processed"] = len(processed_docs)
                logger.info(f"✅ Processor completed: {len(processed_docs)} documents")
            except Exception as e:
                logger.error(f"❌ Processing failed: {e}")
                results["error"] = str(e)
                results["stage"] = "processor"
                return results

            # Stage 3: Chunk
            logger.info("")
            logger.info("✂️  STAGE 3/5: CHUNKING")
            logger.info("-" * 70)
            try:
                chunks = self.chunk_documents(processed_docs)
                results["chunks_created"] = len(chunks)
                logger.info(f"✅ Chunker completed: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"❌ Chunking failed: {e}")
                results["error"] = str(e)
                results["stage"] = "chunker"
                return results

            # Stage 4: Generate embeddings
            logger.info("")
            logger.info("🧠 STAGE 4/5: GENERATING EMBEDDINGS")
            logger.info("-" * 70)
            try:
                chunks_with_embeddings = self.generate_embeddings(chunks)
                results["embeddings_generated"] = len(chunks_with_embeddings)
                logger.info(f"✅ Embeddings completed: {len(chunks_with_embeddings)} vectors")
            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
                results["error"] = str(e)
                results["stage"] = "embeddings"
                return results

            # Stage 5: Load to Neo4j
            logger.info("")
            logger.info("💾 STAGE 5/5: LOADING TO NEO4J")
            logger.info("-" * 70)
            try:
                self.load_to_neo4j(chunks_with_embeddings)
                results["chunks_loaded"] = len(chunks_with_embeddings)
                logger.info(f"✅ Storage completed: {len(chunks_with_embeddings)} chunks loaded")
            except Exception as e:
                logger.error(f"❌ Storage failed: {e}")
                results["error"] = str(e)
                results["stage"] = "storage"
                return results

            results["success"] = True

            logger.info("")
            logger.info("=" * 70)
            logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
        except Exception as e:
            logger.exception(f"❌ PIPELINE FAILED: {e}")
            results["error"] = str(e)
            results["stage"] = "unknown"

        finally:
            if self.neo4j_client:
                self.neo4j_client.close()

        return results

    def run_incremental_update(self) -> Dict[str, Any]:
        """
        Run incremental update for changed documents only.

        Returns:
            Dictionary with execution results
        """
        logger.info("Starting incremental pipeline update...")

        # Similar to full pipeline but only process changed documents
        # This would filter based on change_status from versioning
        # For now, we'll run full pipeline
        logger.warning("Incremental update not fully implemented, running full pipeline")
        return self.run_full_pipeline()

