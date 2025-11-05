"""
Unit test to generate embeddings for test data chunks.

This test reads chunks from tests/.test_data/chunks/ and generates
embeddings, saving them to tests/.test_data/embeddings/.

Run this test to prepare embedded test data:
    pytest tests/unit/test_generate_embeddings_for_test_data.py -v
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from src.embeddings.generator import EmbeddingGenerator


class TestGenerateEmbeddingsForTestData:
    """Generate embeddings for test data chunks."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return Path(__file__).parent.parent / ".test_data"
    
    @pytest.fixture
    def chunks_dir(self, test_data_dir):
        """Get chunks directory."""
        return test_data_dir / "chunks"
    
    @pytest.fixture
    def embeddings_dir(self, test_data_dir):
        """Get embeddings directory."""
        embeddings_dir = test_data_dir / "embeddings"
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        return embeddings_dir
    
    def test_generate_embeddings_for_all_chunk_files(
        self, chunks_dir, embeddings_dir
    ):
        """
        Generate embeddings for all chunk files in test data.
        
        This test:
        1. Reads all JSON files from tests/.test_data/chunks/
        2. Generates embeddings using the configured provider
        3. Saves embedded chunks to tests/.test_data/embeddings/
        """
        # Find all chunk files
        chunk_files = list(chunks_dir.glob("chunks_*.json"))
        
        assert len(chunk_files) > 0, f"No chunk files found in {chunks_dir}"
        
        print(f"\n{'='*70}")
        print(f"Found {len(chunk_files)} chunk files to process")
        print(f"{'='*70}\n")
        
        # Initialize embedding generator
        print("Initializing embedding generator...")
        generator = EmbeddingGenerator()
        dimension = generator.get_dimension()
        print(f"✅ Generator initialized (dimension: {dimension})")
        print(f"   Provider: {generator.provider_name}")
        print(f"   Model: {generator.model_name}")
        print(f"   Batch size: {generator.batch_size}\n")
        
        # Process each chunk file
        for chunk_file in chunk_files:
            print(f"Processing: {chunk_file.name}")
            
            # Load chunks
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            print(f"  Loaded {len(chunks)} chunks")
            
            # Generate embeddings
            chunks_with_embeddings = generator.process_chunks(chunks)
            
            # Verify embeddings were added
            assert len(chunks_with_embeddings) == len(chunks)
            assert all('embedding' in chunk for chunk in chunks_with_embeddings)
            assert all(len(chunk['embedding']) == dimension for chunk in chunks_with_embeddings)
            
            print(f"  ✅ Generated {len(chunks_with_embeddings)} embeddings")
            
            # Create output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = chunk_file.stem.replace("chunks_", "")
            output_file = embeddings_dir / f"embeddings_{base_name}_{timestamp}.json"
            
            # Save embedded chunks
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_with_embeddings, f, indent=2, ensure_ascii=False)
            
            print(f"  💾 Saved to: {output_file.name}\n")
        
        print(f"{'='*70}")
        print(f"✅ Successfully processed all {len(chunk_files)} chunk files")
        print(f"{'='*70}\n")
        
        # List output files
        print("Output files created:")
        for output_file in sorted(embeddings_dir.glob("embeddings_*.json")):
            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            print(f"  - {output_file.name} ({file_size:.2f} MB)")
        print()
    
    def test_generate_embeddings_for_single_file(
        self, chunks_dir, embeddings_dir
    ):
        """
        Generate embeddings for a single chunk file (faster test).
        
        Useful for quick testing without processing all files.
        """
        # Get the first chunk file
        chunk_files = sorted(chunks_dir.glob("chunks_*.json"))
        
        if not chunk_files:
            pytest.skip("No chunk files found in test data")
        
        chunk_file = chunk_files[0]
        
        print(f"\nProcessing single file: {chunk_file.name}")
        
        # Load chunks
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Limit to first 10 chunks for speed
        chunks = chunks[:10]
        print(f"Processing first {len(chunks)} chunks")
        
        # Initialize embedding generator
        generator = EmbeddingGenerator()
        dimension = generator.get_dimension()
        
        # Generate embeddings
        chunks_with_embeddings = generator.process_chunks(chunks)
        
        # Verify
        assert len(chunks_with_embeddings) == len(chunks)
        assert all('embedding' in chunk for chunk in chunks_with_embeddings)
        assert all(len(chunk['embedding']) == dimension for chunk in chunks_with_embeddings)
        
        print(f"✅ Successfully generated {len(chunks_with_embeddings)} embeddings")
        print(f"   Embedding dimension: {dimension}")
        
        # Save sample
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = embeddings_dir / f"embeddings_sample_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_with_embeddings, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved sample to: {output_file.name}\n")
    
    def test_verify_embedding_structure(self, chunks_dir):
        """
        Verify the structure of generated embeddings.
        
        This test checks that embeddings have the correct format.
        """
        # Get a sample chunk file
        chunk_files = list(chunks_dir.glob("chunks_*.json"))
        
        if not chunk_files:
            pytest.skip("No chunk files found in test data")
        
        # Load a few chunks
        with open(chunk_files[0], 'r', encoding='utf-8') as f:
            chunks = json.load(f)[:5]  # Just 5 chunks
        
        # Generate embeddings
        generator = EmbeddingGenerator()
        dimension = generator.get_dimension()
        chunks_with_embeddings = generator.process_chunks(chunks)
        
        # Verify structure
        for chunk in chunks_with_embeddings:
            # Check required fields
            assert 'id' in chunk, "Chunk missing 'id' field"
            assert 'content' in chunk, "Chunk missing 'content' field"
            assert 'embedding' in chunk, "Chunk missing 'embedding' field"
            assert 'metadata' in chunk, "Chunk missing 'metadata' field"
            
            # Check embedding
            embedding = chunk['embedding']
            assert isinstance(embedding, list), "Embedding should be a list"
            assert len(embedding) == dimension, f"Embedding dimension mismatch: {len(embedding)} != {dimension}"
            assert all(isinstance(x, (int, float)) for x in embedding), "Embedding should contain numbers"
            
            # Check metadata
            metadata = chunk['metadata']
            assert 'source_url' in metadata, "Metadata missing 'source_url'"
            assert 'document_title' in metadata, "Metadata missing 'document_title'"
            assert 'chunk_index' in metadata, "Metadata missing 'chunk_index'"
        
        print(f"\n✅ Embedding structure verified")
        print(f"   Chunks checked: {len(chunks_with_embeddings)}")
        print(f"   Embedding dimension: {dimension}")
        print(f"   All required fields present\n")


if __name__ == "__main__":
    """Run this test directly."""
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))

