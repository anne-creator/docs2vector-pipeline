#!/usr/bin/env python
"""Upload existing chunk/embedding files to Pinecone."""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.integrations.pinecone.client import PineconeClient

def main():
    """Upload all existing chunks with embeddings to Pinecone."""
    print("=" * 70)
    print("📌 UPLOADING EXISTING CHUNKS TO PINECONE")
    print("=" * 70)
    print()
    
    # Check if Pinecone is enabled
    if not Settings.USE_PINECONE:
        print("❌ Pinecone is not enabled in .env (USE_PINECONE=false)")
        print("   Set USE_PINECONE=true to enable")
        return 1
    
    # Connect to Pinecone
    print("🔌 Connecting to Pinecone...")
    try:
        pinecone_client = PineconeClient()
        if not pinecone_client.connect():
            print("❌ Failed to connect to Pinecone")
            return 1
        print(f"✅ Connected to Pinecone index: {Settings.PINECONE_INDEX_NAME}")
        print()
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        return 1
    
    # Find all chunk files (they contain embeddings too)
    chunks_dir = Settings.get_data_path("chunks")
    chunk_files = sorted(chunks_dir.glob("item_*_chunks.json"))
    
    print(f"📂 Found {len(chunk_files)} chunk files")
    print()
    
    if not chunk_files:
        print("⚠️  No chunk files found to upload")
        return 0
    
    # Upload in batches
    total_uploaded = 0
    total_errors = 0
    batch_size = 10  # Process 10 files at a time
    
    print("📤 Uploading to Pinecone...")
    print("-" * 70)
    
    for i in range(0, len(chunk_files), batch_size):
        batch_files = chunk_files[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chunk_files) + batch_size - 1) // batch_size
        
        print(f"📦 Batch {batch_num}/{total_batches} ({len(batch_files)} files)")
        
        # Collect all chunks from batch
        batch_chunks = []
        for chunk_file in batch_files:
            try:
                with open(chunk_file) as f:
                    chunks = json.load(f)
                    batch_chunks.extend(chunks)
            except Exception as e:
                print(f"   ⚠️  Error reading {chunk_file.name}: {e}")
                total_errors += 1
                continue
        
        # Upload batch to Pinecone
        if batch_chunks:
            try:
                result = pinecone_client.sync_documents(batch_chunks)
                uploaded_count = result.get("new_count", 0) + result.get("updated_count", 0)
                total_uploaded += uploaded_count
                print(f"   ✅ Uploaded {uploaded_count} chunks")
            except Exception as e:
                print(f"   ❌ Upload failed: {e}")
                total_errors += 1
    
    # Summary
    print()
    print("=" * 70)
    print("🎉 UPLOAD COMPLETE")
    print("=" * 70)
    print(f"✅ Total chunks uploaded: {total_uploaded}")
    print(f"❌ Errors: {total_errors}")
    print(f"📌 Pinecone index: {Settings.PINECONE_INDEX_NAME}")
    print()
    
    # Disconnect
    pinecone_client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

