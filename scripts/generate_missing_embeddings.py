#!/usr/bin/env python
"""Generate embeddings for existing chunks files that don't have embeddings yet."""

import sys
import logging
from pathlib import Path
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.embeddings.generator import EmbeddingGenerator
from src.storage.file_manager import FileManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generate embeddings for all chunks files that don't have embeddings."""
    print("🔄 Generating Missing Embeddings")
    print("=" * 70)
    
    # Initialize components
    file_manager = FileManager()
    embedding_generator = EmbeddingGenerator()
    
    # Get all chunks files
    chunks_dir = Settings.get_data_path("chunks")
    chunks_files = list(chunks_dir.glob("item_*_chunks.json"))
    
    # Get all existing embedding files
    embeddings_dir = Settings.get_data_path("embeddings")
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    existing_embeddings = {f.stem.replace("_embeddings", "") for f in embeddings_dir.glob("item_*_embeddings.json")}
    
    # Find chunks files that need embeddings
    files_to_process = []
    for chunks_file in chunks_files:
        base_name = chunks_file.stem.replace("_chunks", "")
        if base_name not in existing_embeddings:
            files_to_process.append(chunks_file)
    
    print(f"📊 Total chunks files: {len(chunks_files)}")
    print(f"✅ Already have embeddings: {len(existing_embeddings)}")
    print(f"⚙️  Need to generate: {len(files_to_process)}")
    print()
    
    if not files_to_process:
        print("✨ All chunks files already have embeddings!")
        return
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for chunks_file in tqdm(files_to_process, desc="Generating embeddings"):
        try:
            # Load chunks
            chunks = file_manager.load_chunks(chunks_file.name)
            
            if not chunks:
                logger.warning(f"No chunks in {chunks_file.name}, skipping")
                continue
            
            # Generate embeddings
            chunks_with_embeddings = embedding_generator.process_chunks(chunks)
            
            # Save embeddings
            base_name = chunks_file.stem.replace("_chunks", "")
            embeddings_filename = f"{base_name}_embeddings.json"
            file_manager.save_embeddings(chunks_with_embeddings, filename=embeddings_filename)
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing {chunks_file.name}: {e}")
            error_count += 1
    
    # Print summary
    print()
    print("=" * 70)
    print("📈 Summary:")
    print(f"  ✅ Successfully generated: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📁 Embeddings saved to: {embeddings_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()

