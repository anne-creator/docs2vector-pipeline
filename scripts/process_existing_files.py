#!/usr/bin/env python
"""Process existing raw files through the pipeline stages."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.pipeline.stream_processor import StreamProcessor
from src.integrations.s3.client import S3Client
from src.integrations.pinecone.client import PineconeClient

def main():
    """Process all existing raw files."""
    print("🔄 Processing Existing Raw Files")
    print("=" * 70)
    
    # Initialize components
    storage_mode = Settings.get_effective_storage_mode()
    s3_client = None
    pinecone_client = None
    
    if storage_mode == "s3" and Settings.is_s3_configured():
        try:
            s3_client = S3Client()
            s3_client.connect()
            print(f"✅ Connected to S3: {Settings.S3_BUCKET_NAME}")
        except Exception as e:
            print(f"⚠️  S3 connection failed: {e}")
            storage_mode = "local"
    
    # Connect to Pinecone if enabled
    if Settings.USE_PINECONE:
        try:
            pinecone_client = PineconeClient()
            if pinecone_client.connect():
                print(f"✅ Connected to Pinecone: {Settings.PINECONE_INDEX_NAME}")
            else:
                print("⚠️  Pinecone connection failed")
                pinecone_client = None
        except Exception as e:
            print(f"⚠️  Pinecone connection failed: {e}")
            pinecone_client = None
    
    # Create stream processor
    processor = StreamProcessor(
        storage_mode=storage_mode,
        s3_client=s3_client,
        pinecone_client=pinecone_client,
        max_workers=3
    )
    
    # Start workers
    processor.start_workers()
    print(f"✅ Started {processor.max_workers} processing workers")
    
    # Find all raw files that haven't been processed
    raw_dir = Settings.get_data_path("raw")
    processed_dir = Settings.get_data_path("processed")
    
    raw_files = list(raw_dir.glob("item_*.json"))
    processed_files = set(processed_dir.glob("item_*_processed.json"))
    processed_stems = {f.stem.replace("_processed", "") for f in processed_files}
    
    # Filter to unprocessed files
    unprocessed = [f for f in raw_files if f.stem not in processed_stems]
    
    print(f"📊 Found {len(raw_files)} raw files, {len(processed_files)} already processed")
    print(f"🔄 Need to process: {len(unprocessed)} files")
    print()
    
    if not unprocessed:
        print("✅ All files already processed!")
        return
    
    # Queue all unprocessed files
    print("📥 Queuing files for processing...")
    for file_path in unprocessed:
        processor.file_queue.put(file_path)
    print(f"✅ Queued {len(unprocessed)} files")
    print()
    
    # Monitor progress
    print("📊 Processing Progress")
    print("-" * 70)
    last_stats = None
    
    while True:
        # Check if queue is done
        if processor.file_queue.empty() and processor.file_queue.unfinished_tasks == 0:
            print("\n✅ All files processed!")
            break
        
        # Print stats
        current_stats = processor.get_stats()
        if current_stats != last_stats:
            print(
                f"📈 Files={current_stats['files_processed']}/{len(unprocessed)}, "
                f"Docs={current_stats['documents_processed']}, "
                f"Chunks={current_stats['chunks_created']}, "
                f"Embeddings={current_stats['embeddings_generated']}, "
                f"Pinecone={current_stats['chunks_uploaded_pinecone']}, "
                f"Errors={current_stats['errors']}"
            )
            last_stats = current_stats.copy()
        
        time.sleep(2)
    
    # Stop workers
    processor.stop_workers()
    
    # Final stats
    final_stats = processor.get_stats()
    print()
    print("=" * 70)
    print("🎉 PROCESSING COMPLETE")
    print("=" * 70)
    print(f"✅ Files processed: {final_stats['files_processed']}")
    print(f"✅ Documents: {final_stats['documents_processed']}")
    print(f"✅ Chunks: {final_stats['chunks_created']}")
    print(f"✅ Embeddings: {final_stats['embeddings_generated']}")
    if Settings.USE_PINECONE:
        print(f"✅ Uploaded to Pinecone: {final_stats['chunks_uploaded_pinecone']}")
    print(f"❌ Errors: {final_stats['errors']}")
    print()
    print(f"📁 Output directory: {Settings.DATA_DIR}")
    
    # Cleanup
    if pinecone_client:
        pinecone_client.disconnect()

if __name__ == "__main__":
    main()

