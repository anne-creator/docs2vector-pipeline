"""Streaming processor for concurrent pipeline execution."""

import logging
import time
import threading
import queue
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from ..processor.preprocessor import Preprocessor
from ..processor.chunker import SemanticChunker
from ..processor.metadata import MetadataExtractor
from ..embeddings.generator import EmbeddingGenerator
from ..storage.file_manager import FileManager
from ..utils.exceptions import PipelineError
from config.settings import Settings

logger = logging.getLogger(__name__)


class RawFileHandler(FileSystemEventHandler):
    """File system event handler for detecting new raw data files."""
    
    def __init__(self, file_queue: queue.Queue, pattern: str = "item_*.json"):
        """
        Initialize file handler.
        
        Args:
            file_queue: Queue to push detected files to
            pattern: File pattern to watch for
        """
        super().__init__()
        self.file_queue = file_queue
        self.pattern = pattern
        self.processed_files = set()
        logger.debug(f"RawFileHandler initialized, watching for: {pattern}")
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file matches pattern and hasn't been processed
        if file_path.match(self.pattern) and file_path not in self.processed_files:
            # Wait a moment to ensure file is fully written
            time.sleep(0.1)
            
            logger.info(f"🔔 Detected new file: {file_path.name}")
            self.file_queue.put(file_path)
            self.processed_files.add(file_path)


class StreamProcessor:
    """Processes items concurrently as they arrive from the scraper."""
    
    def __init__(
        self,
        storage_mode: str = "local",
        s3_client: Optional[Any] = None,
        max_workers: int = 3
    ):
        """
        Initialize stream processor.
        
        Args:
            storage_mode: Storage mode ("local" or "s3")
            s3_client: Optional S3 client for cloud sync
            max_workers: Maximum number of concurrent processing workers
        """
        self.storage_mode = storage_mode
        self.s3_client = s3_client
        self.max_workers = max_workers
        
        # Initialize pipeline components
        self.preprocessor = Preprocessor()
        self.chunker = SemanticChunker()
        self.metadata_extractor = MetadataExtractor()
        self.embedding_generator = EmbeddingGenerator()
        self.file_manager = FileManager()
        
        # Processing queue and statistics
        self.file_queue: queue.Queue = queue.Queue()
        self.stats = {
            "files_processed": 0,
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "errors": 0
        }
        self.stats_lock = threading.Lock()
        
        # File watcher
        self.observer: Optional[Observer] = None
        self.file_handler: Optional[RawFileHandler] = None
        
        # Worker threads
        self.workers: List[threading.Thread] = []
        self.stop_event = threading.Event()
        
        logger.info(f"🌊 StreamProcessor initialized (workers={max_workers}, storage={storage_mode})")
    
    def start_watching(self, watch_dir: Optional[Path] = None) -> None:
        """
        Start watching for new raw files.
        
        Args:
            watch_dir: Directory to watch (defaults to Settings.get_data_path('raw'))
        """
        if watch_dir is None:
            watch_dir = Settings.get_data_path("raw")
        
        logger.info(f"👀 Starting file watcher on: {watch_dir}")
        
        # Create file handler and observer
        self.file_handler = RawFileHandler(self.file_queue)
        self.observer = Observer()
        self.observer.schedule(self.file_handler, str(watch_dir), recursive=False)
        self.observer.start()
        
        logger.info("✅ File watcher started")
    
    def stop_watching(self) -> None:
        """Stop watching for new files."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("File watcher stopped")
    
    def start_workers(self) -> None:
        """Start worker threads for processing files."""
        logger.info(f"🚀 Starting {self.max_workers} processing workers...")
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"✅ {self.max_workers} workers started")
    
    def stop_workers(self) -> None:
        """Stop all worker threads."""
        logger.info("Stopping workers...")
        self.stop_event.set()
        
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        logger.info("Workers stopped")
    
    def _worker_loop(self) -> None:
        """Main loop for worker threads."""
        worker_name = threading.current_thread().name
        logger.debug(f"{worker_name} started")
        
        while not self.stop_event.is_set():
            try:
                # Get file from queue with timeout
                try:
                    file_path = self.file_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the file
                try:
                    self._process_file(file_path, worker_name)
                except Exception as e:
                    logger.error(f"{worker_name} error processing {file_path.name}: {e}", exc_info=True)
                    with self.stats_lock:
                        self.stats["errors"] += 1
                finally:
                    self.file_queue.task_done()
                    
            except Exception as e:
                logger.error(f"{worker_name} unexpected error: {e}", exc_info=True)
        
        logger.debug(f"{worker_name} stopped")
    
    def _process_file(self, file_path: Path, worker_name: str) -> None:
        """
        Process a single raw file through all pipeline stages.
        
        Args:
            file_path: Path to raw data file
            worker_name: Name of the worker thread
        """
        logger.info(f"⚙️  [{worker_name}] Processing: {file_path.name}")
        
        try:
            # Load raw data
            raw_data = self.file_manager.load_raw_data(file_path.name)
            
            for item in raw_data:
                # Stage 2: Process (HTML to Markdown)
                metadata = self.metadata_extractor.extract(item)
                html_content = item.get("html_content", "")
                text_content = item.get("text_content", "")
                markdown_content = self.preprocessor.process(html_content, text_content)
                
                processed_doc = {
                    "url": item["url"],
                    "title": item.get("title", "Untitled"),
                    "markdown_content": markdown_content,
                    "last_updated": item.get("last_updated", ""),
                    "metadata": metadata,
                }
                
                # Stage 3: Chunk
                chunks = self.chunker.process_documents([processed_doc])
                
                # Stage 4: Generate embeddings
                chunks_with_embeddings = self.embedding_generator.process_chunks(chunks)
                
                # Save intermediate results
                self._save_processed_data(processed_doc, chunks_with_embeddings, file_path)
                
                # Update statistics
                with self.stats_lock:
                    self.stats["documents_processed"] += 1
                    self.stats["chunks_created"] += len(chunks)
                    self.stats["embeddings_generated"] += len(chunks_with_embeddings)
            
            with self.stats_lock:
                self.stats["files_processed"] += 1
            
            logger.info(f"✅ [{worker_name}] Completed: {file_path.name}")
            
        except Exception as e:
            logger.error(f"❌ [{worker_name}] Failed {file_path.name}: {e}")
            raise
    
    def _save_processed_data(
        self,
        processed_doc: Dict[str, Any],
        chunks_with_embeddings: List[Dict[str, Any]],
        source_file: Path
    ) -> None:
        """
        Save processed data to storage.
        
        Args:
            processed_doc: Processed document
            chunks_with_embeddings: Chunks with embeddings
            source_file: Source raw file path
        """
        # Generate filenames based on source file
        base_name = source_file.stem  # e.g., "item_G12345_abc123"
        
        # Save processed document
        proc_filename = f"{base_name}_processed.json"
        proc_path = Settings.get_data_path("processed") / proc_filename
        self.file_manager.save_processed_documents([processed_doc], filename=proc_filename)
        
        # Save chunks with embeddings
        chunks_filename = f"{base_name}_chunks.json"
        chunks_path = Settings.get_data_path("chunks") / chunks_filename
        self.file_manager.save_chunks(chunks_with_embeddings, filename=chunks_filename)
        
        # Sync to S3 if configured
        if self.storage_mode == "s3" and self.s3_client:
            try:
                self.s3_client.upload_file(proc_path, f"pipeline/processed/{proc_filename}")
                self.s3_client.upload_file(chunks_path, f"pipeline/chunks/{chunks_filename}")
            except Exception as e:
                logger.warning(f"S3 sync failed for {base_name}: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get current processing statistics."""
        with self.stats_lock:
            return self.stats.copy()
    
    def wait_for_queue(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all items in queue to be processed.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if queue was emptied, False if timeout
        """
        try:
            if timeout:
                # Wait with timeout
                start_time = time.time()
                while not self.file_queue.empty() or self.file_queue.unfinished_tasks > 0:
                    if time.time() - start_time > timeout:
                        return False
                    time.sleep(0.5)
            else:
                # Wait indefinitely
                self.file_queue.join()
            return True
        except Exception as e:
            logger.error(f"Error waiting for queue: {e}")
            return False

