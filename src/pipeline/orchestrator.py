"""Main pipeline orchestrator coordinating all stages."""

import logging
import os
import subprocess
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..processor.preprocessor import Preprocessor
from ..processor.chunker import SemanticChunker
from ..processor.metadata import MetadataExtractor
from ..embeddings.generator import EmbeddingGenerator
from ..storage.file_manager import FileManager
from ..integrations.s3.client import S3Client
from ..integrations.pinecone.client import PineconeClient
from ..utils.exceptions import PipelineError
from .stream_processor import StreamProcessor
from config.settings import Settings

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete pipeline execution."""

    def __init__(self, storage_mode: Optional[str] = None, pipeline_mode: Optional[str] = None):
        """
        Initialize orchestrator with all pipeline components.
        
        Args:
            storage_mode: Override storage mode ("local", "s3", "auto"), 
                         defaults to Settings.STORAGE_MODE
            pipeline_mode: Override pipeline mode ("batch", "streaming"),
                          defaults to Settings.PIPELINE_MODE
        """
        self.preprocessor = Preprocessor()
        self.chunker = SemanticChunker()
        self.metadata_extractor = MetadataExtractor()
        self.embedding_generator = EmbeddingGenerator()
        self.file_manager = FileManager()
        self.s3_client: Optional[S3Client] = None
        self.pinecone_client: Optional[PineconeClient] = None
        self.stream_processor: Optional[StreamProcessor] = None
        
        # Determine storage mode
        if storage_mode:
            self.storage_mode = storage_mode
        else:
            self.storage_mode = Settings.get_effective_storage_mode()
        
        # Determine pipeline mode
        if pipeline_mode:
            self.pipeline_mode = pipeline_mode
        else:
            self.pipeline_mode = Settings.PIPELINE_MODE
        
        logger.info(f"Pipeline storage mode: {self.storage_mode}")
        logger.info(f"Pipeline processing mode: {self.pipeline_mode}")

    def connect_s3(self) -> bool:
        """
        Connect to AWS S3.
        
        Returns:
            True if connection successful
        """
        try:
            logger.info("Connecting to AWS S3...")
            self.s3_client = S3Client()
            if self.s3_client.connect():
                logger.info("✅ Connected to AWS S3")
                return True
            else:
                logger.warning("⚠️  Failed to connect to S3")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize S3 client: {e}")
            return False
    
    def connect_pinecone(self) -> bool:
        """
        Connect to Pinecone vector database.
        
        Returns:
            True if connection successful
        """
        try:
            logger.info("Connecting to Pinecone...")
            self.pinecone_client = PineconeClient()
            if self.pinecone_client.connect():
                logger.info("✅ Connected to Pinecone")
                return True
            else:
                logger.warning("⚠️  Failed to connect to Pinecone")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize Pinecone client: {e}")
            return False
    
    def sync_to_s3(self, stage: str) -> None:
        """
        Sync data files from local storage to S3.
        
        Args:
            stage: Pipeline stage name (raw, processed, chunks, embeddings)
        """
        if self.storage_mode != "s3":
            return
        
        if not self.s3_client or not self.s3_client._connected:
            logger.warning("S3 client not connected, skipping sync")
            return
        
        try:
            stage_dir = Settings.get_data_path(stage)
            if not stage_dir.exists():
                logger.debug(f"Stage directory {stage} does not exist, skipping sync")
                return
            
            # Get the latest file from this stage
            latest_file = self.file_manager.get_latest_file(stage)
            if latest_file:
                s3_key = f"pipeline/{stage}/{latest_file.name}"
                logger.info(f"📤 Syncing {latest_file.name} to S3...")
                self.s3_client.upload_file(latest_file, s3_key)
                logger.info(f"✅ Synced to s3://{Settings.S3_BUCKET_NAME}/{s3_key}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to sync {stage} to S3: {e}")
            # Don't raise - S3 sync is optional, pipeline should continue

    def run_scraper(self, background: bool = False):
        """
        Run the Scrapy spider to scrape data.
        
        Args:
            background: If True, run in background and return process object (for streaming mode)

        Returns:
            Path to saved raw data file (batch mode) or subprocess.Popen object (streaming mode)
        """
        logger.info("Starting scraper...")
        try:
            # Get the project root directory
            from config.settings import Settings
            project_root = Settings.DATA_DIR.parent  # DATA_DIR is ./data, so parent is project root
            
            # Configure environment
            env = {
                **os.environ,
                "PYTHONPATH": str(project_root),
                "SCRAPY_SETTINGS_MODULE": "scrapy_project.settings",
            }
            
            # Run scrapy crawl command FROM PROJECT ROOT (not from scrapy_project/)
            # This ensures FileManager uses the correct data directory
            # Pipelines are configured in scrapy_project/settings.py
            cmd = ["scrapy", "crawl", "amazon_seller_help"]
            
            logger.info(f"🌊 Running scraper in {'background (streaming)' if background else 'foreground (batch)'} mode")
            
            if background:
                # Run in background for streaming mode
                logger.debug(f"Running command: {' '.join(cmd)}")
                logger.debug(f"Working directory: {project_root}")
                logger.debug(f"Environment PYTHONPATH: {env.get('PYTHONPATH')}")
                
                process = subprocess.Popen(
                    cmd,
                    cwd=str(project_root),  # Run from project root, not scrapy_project/
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stderr with stdout
                    text=True,
                    env=env
                )
                logger.info(f"Scraper running in background (PID: {process.pid})")
                
                # Log the output for debugging (non-blocking)
                import threading
                def log_output():
                    for line in process.stdout:
                        logger.info(f"[Scraper] {line.strip()}")
                
                output_thread = threading.Thread(target=log_output, daemon=True)
                output_thread.start()
                
                return process  # Return process object so caller can monitor it
            else:
                # Run and wait for batch mode
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),  # Run from project root, not scrapy_project/
                    capture_output=True,
                    text=True,
                    env=env
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

    def upload_to_pinecone(self, chunks_with_embeddings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload chunks with embeddings to Pinecone vector database.
        Uses intelligent sync to only upload new/updated documents.

        Args:
            chunks_with_embeddings: List of chunks with embeddings

        Returns:
            Dictionary with sync results
        """
        if self.pinecone_client is None:
            if not self.connect_pinecone():
                raise PipelineError("Failed to connect to Pinecone")

        logger.info(f"Syncing {len(chunks_with_embeddings)} chunks to Pinecone...")

        try:
            # Use sync_documents which intelligently handles new/updated/unchanged
            result = self.pinecone_client.sync_documents(chunks_with_embeddings)
            logger.info(f"Successfully synced chunks to Pinecone")
            return result
        except Exception as e:
            logger.error(f"Error uploading to Pinecone: {e}")
            raise PipelineError(f"Failed to upload to Pinecone: {e}") from e

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete pipeline from scraping to storage.
        Automatically chooses batch or streaming mode based on configuration.

        Returns:
            Dictionary with execution results
        """
        logger.info("=" * 70)
        logger.info("🚀 STARTING FULL PIPELINE")
        logger.info(f"   Processing Mode: {self.pipeline_mode}")
        logger.info(f"   Storage Mode: {self.storage_mode}")
        logger.info("=" * 70)
        
        # Choose execution mode
        if self.pipeline_mode == "streaming":
            return self._run_streaming_pipeline()
        else:
            return self._run_batch_pipeline()
    
    def _run_batch_pipeline(self) -> Dict[str, Any]:
        """
        Run batch pipeline (original behavior - wait for scraping to complete).

        Returns:
            Dictionary with execution results
        """
        logger.info("📦 Running in BATCH mode (sequential stages)")
        logger.info("=" * 70)

        results = {
            "raw_data_file": None,
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "storage_mode": self.storage_mode,
            "success": False,
        }

        # Connect to S3 if using S3 storage
        if self.storage_mode == "s3":
            if not self.connect_s3():
                logger.error("Failed to connect to S3. Falling back to local storage.")
                self.storage_mode = "local"
                results["storage_mode"] = "local"

        try:
            # Determine total stages
            total_stages = 4  # Base stages: scrape, process, chunk, embed
            if Settings.USE_PINECONE:
                total_stages += 1
            current_stage = 1

            # Stage 1: Scrape
            logger.info("")
            logger.info(f"📡 STAGE {current_stage}/{total_stages}: SCRAPING")
            logger.info("-" * 70)
            try:
                raw_data_file = self.run_scraper()
                results["raw_data_file"] = str(raw_data_file)
                logger.info(f"✅ Scraper completed successfully")
                # Sync to S3 if configured
                self.sync_to_s3("raw")
            except Exception as e:
                logger.error(f"❌ Scraping failed: {e}")
                results["error"] = str(e)
                results["stage"] = "scraper"
                return results

            current_stage += 1

            # Stage 2: Process
            logger.info("")
            logger.info(f"⚙️  STAGE {current_stage}/{total_stages}: PROCESSING")
            logger.info("-" * 70)
            try:
                processed_docs = self.process_documents(raw_data_file)
                results["documents_processed"] = len(processed_docs)
                logger.info(f"✅ Processor completed: {len(processed_docs)} documents")
                # Sync to S3 if configured
                self.sync_to_s3("processed")
            except Exception as e:
                logger.error(f"❌ Processing failed: {e}")
                results["error"] = str(e)
                results["stage"] = "processor"
                return results

            current_stage += 1

            # Stage 3: Chunk
            logger.info("")
            logger.info(f"✂️  STAGE {current_stage}/{total_stages}: CHUNKING")
            logger.info("-" * 70)
            try:
                chunks = self.chunk_documents(processed_docs)
                results["chunks_created"] = len(chunks)
                logger.info(f"✅ Chunker completed: {len(chunks)} chunks")
                # Sync to S3 if configured
                self.sync_to_s3("chunks")
            except Exception as e:
                logger.error(f"❌ Chunking failed: {e}")
                results["error"] = str(e)
                results["stage"] = "chunker"
                return results

            current_stage += 1

            # Stage 4: Generate embeddings
            logger.info("")
            logger.info(f"🧠 STAGE {current_stage}/{total_stages}: GENERATING EMBEDDINGS")
            logger.info("-" * 70)
            try:
                chunks_with_embeddings = self.generate_embeddings(chunks)
                results["embeddings_generated"] = len(chunks_with_embeddings)
                logger.info(f"✅ Embeddings completed: {len(chunks_with_embeddings)} vectors")
                # Sync to S3 if configured
                self.sync_to_s3("embeddings")
            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
                results["error"] = str(e)
                results["stage"] = "embeddings"
                return results

            # Stage 5: Upload to Pinecone (Optional)
            if Settings.USE_PINECONE:
                current_stage += 1
                logger.info("")
                logger.info(f"📌 STAGE {current_stage}/{total_stages}: UPLOADING TO PINECONE")
                logger.info("-" * 70)
                try:
                    sync_result = self.upload_to_pinecone(chunks_with_embeddings)
                    results["chunks_synced_pinecone"] = sync_result.get("new_count", 0) + sync_result.get("updated_count", 0)
                    results["pinecone_sync_details"] = sync_result
                    logger.info(f"✅ Pinecone sync completed")
                except Exception as e:
                    logger.error(f"❌ Pinecone upload failed: {e}")
                    results["error"] = str(e)
                    results["stage"] = "pinecone"
                    return results

            # Final summary
            logger.info("")
            logger.info("💾 DATA STORAGE")
            logger.info("-" * 70)
            logger.info(f"✅ All data saved locally in: {Settings.DATA_DIR}")
            if self.storage_mode == "s3":
                logger.info(f"✅ Data synced to S3 bucket: {Settings.S3_BUCKET_NAME}")
            if Settings.USE_PINECONE:
                logger.info(f"✅ Vectors uploaded to Pinecone index: {Settings.PINECONE_INDEX_NAME}")

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
            if self.s3_client:
                self.s3_client.disconnect()
            if self.pinecone_client:
                self.pinecone_client.disconnect()

        return results
    
    def _run_streaming_pipeline(self) -> Dict[str, Any]:
        """
        Run streaming pipeline (concurrent processing as items arrive).

        Returns:
            Dictionary with execution results
        """
        logger.info("🌊 Running in STREAMING mode (concurrent stages)")
        logger.info("=" * 70)

        results = {
            "processing_mode": "streaming",
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "chunks_uploaded_pinecone": 0,
            "storage_mode": self.storage_mode,
            "success": False,
        }

        # Connect to S3 if using S3 storage
        if self.storage_mode == "s3":
            if not self.connect_s3():
                logger.error("Failed to connect to S3. Falling back to local storage.")
                self.storage_mode = "local"
                results["storage_mode"] = "local"
        
        # Connect to Pinecone if enabled (for streaming uploads)
        if Settings.USE_PINECONE:
            if not self.connect_pinecone():
                logger.error("Failed to connect to Pinecone. Streaming uploads will be skipped.")
            else:
                logger.info("✅ Pinecone connected - will upload vectors in real-time during streaming")

        try:
            # Initialize stream processor with Pinecone client
            self.stream_processor = StreamProcessor(
                storage_mode=self.storage_mode,
                s3_client=self.s3_client,
                pinecone_client=self.pinecone_client,
                max_workers=3
            )
            
            # Start file watcher
            self.stream_processor.start_watching()
            
            # Start processing workers
            self.stream_processor.start_workers()
            
            # Stage 1: Start scraper in background (it will save files as it goes)
            logger.info("")
            logger.info("📡 STAGE 1: SCRAPING (Background)")
            logger.info("-" * 70)
            try:
                scraper_process = self.run_scraper(background=True)
                logger.info("✅ Scraper started in background")
                logger.info("🌊 Items will be processed concurrently as they arrive...")
            except Exception as e:
                logger.error(f"❌ Scraping failed: {e}")
                results["error"] = str(e)
                results["stage"] = "scraper"
                return results

            # Stages 2-5 run concurrently in worker threads as items arrive
            logger.info("")
            logger.info("⚙️  STAGES 2-5: PROCESSING (Concurrent)")
            logger.info("-" * 70)
            logger.info("🔄 Stage 2: Processing → Stage 3: Chunking → Stage 4: Embeddings → Stage 5: Pinecone Upload")
            logger.info("   All stages running in parallel for each scraped item")
            
            # Monitor progress
            logger.info("")
            logger.info("📊 MONITORING PROGRESS")
            logger.info("-" * 70)
            
            # Wait for scraper to finish and queue to empty
            # Poll for completion (scraper done + queue empty)
            max_wait = 600  # 10 minutes max
            start_time = time.time()
            last_stats = None
            
            while time.time() - start_time < max_wait:
                current_stats = self.stream_processor.get_stats()
                
                # Print stats if changed
                if current_stats != last_stats:
                    logger.info(
                        f"📈 Progress: Files={current_stats['files_processed']}, "
                        f"Docs={current_stats['documents_processed']}, "
                        f"Chunks={current_stats['chunks_created']}, "
                        f"Embeddings={current_stats['embeddings_generated']}, "
                        f"Pinecone={current_stats['chunks_uploaded_pinecone']}, "
                        f"Errors={current_stats['errors']}"
                    )
                    last_stats = current_stats.copy()
                
                # Check if scraper is still running
                scraper_running = scraper_process and scraper_process.poll() is None
                
                # Check if we're done: scraper finished AND queue is empty
                if not scraper_running and \
                   self.stream_processor.file_queue.empty() and \
                   self.stream_processor.file_queue.unfinished_tasks == 0:
                    # Wait a bit more to ensure all files are processed
                    logger.info("🛑 Scraper finished. Waiting for remaining items to be processed...")
                    time.sleep(5)
                    if self.stream_processor.file_queue.empty() and \
                       self.stream_processor.file_queue.unfinished_tasks == 0:
                        logger.info("✅ All items processed")
                        break
                
                time.sleep(2)
            
            # Get final stats
            final_stats = self.stream_processor.get_stats()
            results["documents_processed"] = final_stats["documents_processed"]
            results["chunks_created"] = final_stats["chunks_created"]
            results["embeddings_generated"] = final_stats["embeddings_generated"]
            results["chunks_uploaded_pinecone"] = final_stats["chunks_uploaded_pinecone"]
            
            # Note: Pinecone upload now happens in real-time during streaming
            # The old Stage 5 batch upload has been removed and is now handled in StreamProcessor
            
            # Final summary
            logger.info("")
            logger.info("💾 DATA STORAGE")
            logger.info("-" * 70)
            logger.info(f"✅ All data saved locally in: {Settings.DATA_DIR}")
            if self.storage_mode == "s3":
                logger.info(f"✅ Data synced to S3 bucket: {Settings.S3_BUCKET_NAME}")
            if Settings.USE_PINECONE:
                logger.info(f"✅ Vectors uploaded to Pinecone in real-time: {results['chunks_uploaded_pinecone']} chunks to index: {Settings.PINECONE_INDEX_NAME}")

            results["success"] = True

            logger.info("")
            logger.info("=" * 70)
            logger.info("🎉 STREAMING PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.exception(f"❌ STREAMING PIPELINE FAILED: {e}")
            results["error"] = str(e)
            results["stage"] = "unknown"

        finally:
            # Cleanup
            if self.stream_processor:
                self.stream_processor.stop_workers()
                self.stream_processor.stop_watching()
            if self.s3_client:
                self.s3_client.disconnect()
            if self.pinecone_client:
                self.pinecone_client.disconnect()

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

