# Embedding Test Data Generation Guide

## Overview

This guide explains how to generate embeddings for your test data chunks using the new test file.

## Quick Start

### Step 1: Choose Your Embedding Provider

**Option A: Sentence Transformers (Recommended)**
```bash
# Create/edit .env
echo "EMBEDDING_PROVIDER=sentence-transformers" > .env
echo "EMBEDDING_MODEL=BAAI/bge-small-en-v1.5" >> .env
echo "EMBEDDING_BATCH_SIZE=32" >> .env
```

**Option B: Ollama (if you have it installed)**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull model and configure
ollama pull nomic-embed-text
echo "EMBEDDING_PROVIDER=ollama" > .env
echo "EMBEDDING_MODEL=nomic-embed-text" >> .env
echo "EMBEDDING_BATCH_SIZE=16" >> .env
```

### Step 2: Run the Embedding Generation Test

**Option 1: Generate embeddings for ALL chunk files**
```bash
# This processes all files in tests/.test_data/chunks/
pytest tests/unit/test_generate_embeddings_for_test_data.py::TestGenerateEmbeddingsForTestData::test_generate_embeddings_for_all_chunk_files -v -s
```

**Option 2: Quick test with a single file (faster)**
```bash
# This processes just the first 10 chunks from one file
pytest tests/unit/test_generate_embeddings_for_test_data.py::TestGenerateEmbeddingsForTestData::test_generate_embeddings_for_single_file -v -s
```

**Option 3: Run all tests in the file**
```bash
# This runs all test methods
pytest tests/unit/test_generate_embeddings_for_test_data.py -v -s
```

### Step 3: Verify Output

Check the generated embeddings:
```bash
# List generated embedding files
ls -lh tests/.test_data/embeddings/

# Check first few lines of an embedding file
head -50 tests/.test_data/embeddings/embeddings_*.json
```

## What the Test Does

### Input
- **Location**: `tests/.test_data/chunks/`
- **Files**: `chunks_*.json`
- **Format**: JSON arrays of chunk objects

### Process
1. Loads all chunk files from test data
2. Initializes the embedding generator (using your configured provider)
3. Generates embeddings for each chunk's content
4. Adds the `embedding` field to each chunk

### Output
- **Location**: `tests/.test_data/embeddings/`
- **Files**: `embeddings_*_<timestamp>.json`
- **Format**: JSON arrays of chunks WITH embeddings

### Example Structure

**Before (chunk without embedding)**:
```json
{
  "id": "G2?locale=en-US_0",
  "content": "Help for Amazon Sellers...",
  "metadata": {
    "source_url": "https://...",
    "document_title": "Help for Amazon Sellers",
    "chunk_index": 0
  }
}
```

**After (chunk with embedding)**:
```json
{
  "id": "G2?locale=en-US_0",
  "content": "Help for Amazon Sellers...",
  "embedding": [0.123, -0.456, 0.789, ..., 0.234],
  "metadata": {
    "source_url": "https://...",
    "document_title": "Help for Amazon Sellers",
    "chunk_index": 0
  }
}
```

## Test Methods Explained

### 1. `test_generate_embeddings_for_all_chunk_files`
- **Purpose**: Generate embeddings for ALL test data
- **Use case**: Prepare complete test dataset with embeddings
- **Speed**: Slow (processes all files)
- **Output**: Multiple embedding files

### 2. `test_generate_embeddings_for_single_file`
- **Purpose**: Quick test with limited data
- **Use case**: Verify setup works correctly
- **Speed**: Fast (only first 10 chunks from 1 file)
- **Output**: One sample embedding file

### 3. `test_verify_embedding_structure`
- **Purpose**: Validate embedding format
- **Use case**: Ensure embeddings have correct structure
- **Speed**: Very fast (only 5 chunks)
- **Output**: No file (just validation)

## Expected Output Example

When you run the full test, you'll see:

```
======================================================================
Found 7 chunk files to process
======================================================================

Initializing embedding generator...
✅ Generator initialized (dimension: 384)
   Provider: sentence-transformers
   Model: BAAI/bge-small-en-v1.5
   Batch size: 32

Processing: chunks_20251031_174503.json
  Loaded 1234 chunks
Generating embeddings: 100%|████████████████| 39/39 [00:15<00:00,  2.51it/s]
  ✅ Generated 1234 embeddings
  💾 Saved to: embeddings_20251031_174503_20251104_153045.json

Processing: chunks_20251031_174511.json
  Loaded 856 chunks
Generating embeddings: 100%|████████████████| 27/27 [00:11<00:00,  2.45it/s]
  ✅ Generated 856 embeddings
  💾 Saved to: embeddings_20251031_174511_20251104_153102.json

...

======================================================================
✅ Successfully processed all 7 chunk files
======================================================================

Output files created:
  - embeddings_20251031_174503_20251104_153045.json (12.45 MB)
  - embeddings_20251031_174511_20251104_153102.json (8.67 MB)
  ...
```

## Troubleshooting

### Issue: "No module named 'sentence_transformers'"

```bash
# Install dependencies
pip install -r requirements.txt
```

### Issue: Model download fails

```bash
# Pre-download model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
```

### Issue: Out of memory

```bash
# Reduce batch size in .env
echo "EMBEDDING_BATCH_SIZE=8" >> .env

# Or process files one at a time
pytest tests/unit/test_generate_embeddings_for_test_data.py::TestGenerateEmbeddingsForTestData::test_generate_embeddings_for_single_file -v -s
```

### Issue: Ollama connection refused

```bash
# Make sure Ollama is running
ollama serve

# In another terminal, verify it's accessible
curl http://localhost:11434/api/tags
```

### Issue: "No chunk files found"

```bash
# Make sure chunk files exist
ls tests/.test_data/chunks/

# If missing, run the processor tests first to generate chunks
```

## Performance Expectations

### With Sentence Transformers (CPU)
- **Small file** (100 chunks): ~5-10 seconds
- **Medium file** (500 chunks): ~20-30 seconds
- **Large file** (1000 chunks): ~40-60 seconds
- **All files** (7000+ chunks): ~5-10 minutes

### With Sentence Transformers (GPU)
- **10x faster** than CPU
- **All files**: ~1-2 minutes

### With Ollama
- **Similar to CPU** performance
- May be slower due to network overhead

## Memory Usage

Expected memory consumption:
- **Python process**: 1-2 GB
- **Model**: 500MB-1GB
- **Working memory**: 1-2 GB
- **Total**: 3-5 GB

Monitor memory:
```bash
# macOS
open -a "Activity Monitor"

# Or in terminal
htop  # Press F6 to sort by memory
```

## Verifying Generated Embeddings

### Check file sizes
```bash
ls -lh tests/.test_data/embeddings/
```

### Inspect an embedding
```bash
# View first embedding in a file
python -c "
import json
with open('tests/.test_data/embeddings/embeddings_*.json') as f:
    data = json.load(f)
    print(f'Total chunks: {len(data)}')
    print(f'First chunk ID: {data[0][\"id\"]}')
    print(f'Embedding dimension: {len(data[0][\"embedding\"])}')
    print(f'First 5 values: {data[0][\"embedding\"][:5]}')
"
```

### Count embeddings
```bash
# Count how many chunks have embeddings
python -c "
import json
import glob
total = 0
for file in glob.glob('tests/.test_data/embeddings/*.json'):
    with open(file) as f:
        data = json.load(f)
        total += len(data)
print(f'Total chunks with embeddings: {total}')
"
```

## Next Steps

After generating embeddings:

1. **Use in tests**: Import embedded chunks in other tests
   ```python
   import json
   with open('tests/.test_data/embeddings/embeddings_*.json') as f:
       chunks_with_embeddings = json.load(f)
   ```

2. **Load to Neo4j**: Use these for Neo4j integration tests
   ```python
   from src.storage.neo4j_client import Neo4jClient
   client = Neo4jClient()
   client.batch_upsert_chunks(chunks_with_embeddings)
   ```

3. **Test semantic search**: Query similar chunks
   ```python
   # Find similar chunks to a query
   query_embedding = generator.generate_embedding("payment methods")
   # Use cosine similarity to find matches
   ```

## Running as a Standalone Script

You can also run the test file directly:

```bash
# Run directly with Python
python tests/unit/test_generate_embeddings_for_test_data.py

# This will run all tests in the file
```

## Summary

✅ **Recommended workflow**:
1. Use sentence-transformers with BGE-small-en-v1.5
2. Start with single file test to verify setup
3. Run full test to generate all embeddings
4. Verify output files are created
5. Use embedded chunks in downstream tests

📖 For more details on embedding configuration, see:
- [README.md - Running BGE-small-en-v1.5 Locally](README.md#running-bge-small-en-v15-locally)
- [docs/EMBEDDING_CONFIGURATION.md](docs/EMBEDDING_CONFIGURATION.md)

