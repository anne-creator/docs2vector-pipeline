#!/usr/bin/env python3
"""
Test script for LlamaIndex Cloud synchronization.

This script tests the LlamaIndex upload functionality by:
1. Loading existing embedding files
2. Connecting to LlamaIndex Cloud
3. Syncing documents (respecting change_status)
4. Reporting sync results

Usage:
    # Set USE_LLAMAINDEX=true in your .env file first!
    python scripts/test_llamaindex_sync.py
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.llamaindex.client import LlamaIndexClient
from src.storage.file_manager import FileManager
from config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_llamaindex_connection():
    """Test LlamaIndex Cloud connection."""
    logger.info("=" * 70)
    logger.info("🧪 TESTING LLAMAINDEX CLOUD CONNECTION")
    logger.info("=" * 70)
    
    # Check if LlamaIndex is enabled
    if not Settings.USE_LLAMAINDEX:
        logger.error("❌ USE_LLAMAINDEX is not enabled in .env file!")
        logger.info("💡 To enable: Set USE_LLAMAINDEX=true in your .env file")
        return False
    
    # Check credentials
    if not Settings.LLAMACLOUD_API_KEY:
        logger.error("❌ LLAMACLOUD_API_KEY is not set in .env file!")
        logger.info("💡 Get your API key from: https://cloud.llamaindex.ai/")
        return False
    
    if not Settings.LLAMACLOUD_INDEX_NAME:
        logger.error("❌ LLAMACLOUD_INDEX_NAME is not set in .env file!")
        logger.info("💡 Set your index/pipeline name in .env")
        return False
    
    logger.info(f"✅ Configuration loaded:")
    logger.info(f"   Index Name: {Settings.LLAMACLOUD_INDEX_NAME}")
    logger.info(f"   Project: {Settings.LLAMACLOUD_PROJECT_NAME}")
    logger.info(f"   Base URL: {Settings.LLAMACLOUD_BASE_URL}")
    logger.info("")
    
    # Test connection
    try:
        client = LlamaIndexClient()
        if client.connect():
            logger.info("✅ Successfully connected to LlamaIndex Cloud!")
            client.disconnect()
            return True
        else:
            logger.error("❌ Failed to connect to LlamaIndex Cloud")
            return False
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False


def test_sync_embeddings(limit: int = 10):
    """
    Test syncing embeddings to LlamaIndex Cloud.
    
    Args:
        limit: Maximum number of embedding files to test with
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("🧪 TESTING LLAMAINDEX SYNC WITH EMBEDDINGS")
    logger.info("=" * 70)
    
    # Initialize clients
    file_manager = FileManager()
    client = LlamaIndexClient()
    
    try:
        # Connect
        if not client.connect():
            logger.error("❌ Failed to connect to LlamaIndex Cloud")
            return False
        
        # Find embedding files
        embeddings_dir = Settings.get_data_path("embeddings")
        embedding_files = list(embeddings_dir.glob("*_embeddings.json"))
        
        if not embedding_files:
            logger.warning("⚠️  No embedding files found!")
            logger.info(f"   Looked in: {embeddings_dir}")
            logger.info("💡 Run the pipeline first to generate embeddings")
            return False
        
        logger.info(f"📁 Found {len(embedding_files)} embedding files")
        logger.info(f"   Testing with first {min(limit, len(embedding_files))} files")
        logger.info("")
        
        # Load embeddings
        all_chunks = []
        for embedding_file in embedding_files[:limit]:
            chunks = file_manager.load_embeddings(embedding_file.name)
            all_chunks.extend(chunks)
            logger.info(f"   ✓ Loaded {len(chunks)} chunks from {embedding_file.name}")
        
        logger.info(f"📊 Total chunks loaded: {len(all_chunks)}")
        
        # Analyze change status distribution
        status_counts = {}
        for chunk in all_chunks:
            status = chunk.get("metadata", {}).get("change_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        logger.info("")
        logger.info("📈 Change Status Distribution:")
        for status, count in status_counts.items():
            logger.info(f"   {status}: {count}")
        logger.info("")
        
        # Sync to LlamaIndex
        logger.info("🔄 Starting sync to LlamaIndex Cloud...")
        result = client.sync_documents(all_chunks)
        
        # Display results
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ SYNC TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"   📝 New documents uploaded: {result['new_count']}")
        logger.info(f"   🔄 Documents updated: {result['updated_count']}")
        logger.info(f"   ⏭️  Unchanged documents skipped: {result['unchanged_count']}")
        if result.get('errors'):
            logger.warning(f"   ⚠️  Errors: {len(result['errors'])}")
            for error in result['errors'][:5]:  # Show first 5 errors
                logger.warning(f"      - {error}")
        logger.info("=" * 70)
        logger.info("")
        logger.info("🌐 Check your LlamaIndex Cloud dashboard to verify the upload:")
        logger.info("   https://cloud.llamaindex.ai/")
        logger.info("")
        
        client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        if client:
            client.disconnect()
        return False


def main():
    """Main test function."""
    logger.info("")
    logger.info("🚀 LlamaIndex Cloud Integration Test")
    logger.info("")
    
    # Test 1: Connection
    if not test_llamaindex_connection():
        logger.error("")
        logger.error("❌ Connection test failed. Please check your configuration.")
        logger.info("")
        logger.info("📝 Quick Setup Guide:")
        logger.info("   1. Get API key: https://cloud.llamaindex.ai/")
        logger.info("   2. Update your .env file:")
        logger.info("      USE_LLAMAINDEX=true")
        logger.info("      LLAMACLOUD_API_KEY=llx-...")
        logger.info("      LLAMACLOUD_INDEX_NAME=your-index-name")
        logger.info("")
        return 1
    
    # Test 2: Sync embeddings
    if not test_sync_embeddings(limit=5):
        logger.error("")
        logger.error("❌ Sync test failed.")
        return 1
    
    logger.info("✅ All tests passed!")
    logger.info("")
    logger.info("💡 Next Steps:")
    logger.info("   1. Run the full pipeline: python scripts/run_pipeline.py")
    logger.info("   2. Check LlamaIndex Cloud: https://cloud.llamaindex.ai/")
    logger.info("   3. The pipeline will automatically sync new/updated documents")
    logger.info("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


