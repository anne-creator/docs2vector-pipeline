# Processor Tests Quick Start Guide

## Running Tests

### Run All Processor Tests (39 tests)
```bash
pytest tests/unit/test_preprocessor.py \
       tests/unit/test_chunker.py \
       tests/unit/test_metadata.py \
       tests/unit/test_processor_pipeline.py -v
```

**Expected Result:** ✅ 39 passed

---

## Test Data Flow

```
1. Scraper generates:
   tests/.test_data/raw/raw_data_TIMESTAMP.json

2. Processor Step 1 generates:
   tests/.test_data/processed/processed_TIMESTAMP.json
   
3. Processor Step 2 generates:
   tests/.test_data/chunks/chunks_TIMESTAMP.json
   
4. Embeddings stage will use:
   tests/.test_data/chunks/chunks_TIMESTAMP.json (as input)
```

---

## Generated Test Data

### Current Test Data (from real scraping)

```
tests/.test_data/
├── raw/
│   └── raw_data_20251031_170118.json          # 10 documents, ~2MB
├── processed/
│   └── processed_20251031_174536.json         # 10 documents, ~131KB
└── chunks/
    └── chunks_20251031_174536.json            # 124 chunks, ~2.1MB
```

### Statistics

- **Raw documents:** 10 Amazon Seller Central pages
- **Processed documents:** 10 with clean Markdown
- **Total chunks:** 124
- **Average chunks per document:** ~12
- **Chunk size:** Max 512 chars (configurable)

---

## Using Test Data in Your Code

### For Embedding Stage

```python
import json
from pathlib import Path

# Load the latest chunks
test_data_dir = Path("tests/.test_data")
chunks_files = list((test_data_dir / "chunks").glob("chunks_*.json"))
latest_chunks_file = max(chunks_files, key=lambda p: p.stat().st_mtime)

with open(latest_chunks_file, 'r') as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

# Each chunk has:
for chunk in chunks:
    chunk_id = chunk["id"]                    # e.g., "G123_0"
    content = chunk["content"]                 # Text to embed
    metadata = chunk["metadata"]               # Full context
    
    # Your embedding code here
    # embedding = your_embedding_model.encode(content)
```

### Load Processed Documents

```python
import json
from pathlib import Path

# Load processed documents (before chunking)
test_data_dir = Path("tests/.test_data")
processed_files = list((test_data_dir / "processed").glob("processed_*.json"))
latest_processed = max(processed_files, key=lambda p: p.stat().st_mtime)

with open(latest_processed, 'r') as f:
    documents = json.load(f)

print(f"Loaded {len(documents)} processed documents")

# Each document has:
for doc in documents:
    url = doc["url"]
    title = doc["title"]
    markdown = doc["markdown_content"]         # Clean Markdown
    metadata = doc["metadata"]                 # Structured metadata
```

---

## Running Individual Pipeline Steps

### Step 1: Preprocess Raw Data → Processed Documents

```bash
pytest tests/unit/test_processor_pipeline.py::TestCompleteProcessorPipeline::test_step1_preprocess_real_data -v -s
```

**Generates:** `tests/.test_data/processed/processed_TIMESTAMP.json`

### Step 2: Chunk Processed Documents → Chunks

```bash
pytest tests/unit/test_processor_pipeline.py::TestCompleteProcessorPipeline::test_step2_chunk_processed_data -v -s
```

**Requires:** Processed data from Step 1
**Generates:** `tests/.test_data/chunks/chunks_TIMESTAMP.json`

### Step 3: Test Complete Pipeline

```bash
pytest tests/unit/test_processor_pipeline.py::TestCompleteProcessorPipeline::test_step3_complete_pipeline_single_document -v -s
```

**Tests:** Complete flow on a single document

---

## Data Structure Reference

### Raw Data (from scraper)
```json
{
  "url": "https://sellercentral.amazon.com/help/hub/reference/external/G123",
  "title": "Document Title",
  "html_content": "<html>...</html>",
  "text_content": "Plain text...",
  "metadata": {
    "locale": "en-US",
    "article_id": "123",
    "page_hash": "abc123",
    "change_status": "new"
  },
  "scraped_at": "2024-10-31T17:01:18"
}
```

### Processed Data (after Step 1)
```json
{
  "url": "https://...",
  "title": "Document Title",
  "markdown_content": "# Title\n\nContent...",
  "last_updated": "2024-01-01",
  "metadata": {
    "source_url": "https://...",
    "document_title": "Document Title",
    "breadcrumbs": ["Home", "Help"],
    "locale": "en-US",
    "article_id": "123",
    "page_hash": "abc123"
  },
  "processed_at": "2024-10-31T17:45:03"
}
```

### Chunks (after Step 2) - **Ready for Embeddings**
```json
{
  "id": "G123_0",
  "content": "# Section Title\n\nChunk content text...",
  "metadata": {
    "chunk_id": "G123_0",
    "doc_id": "https://...",
    "source_url": "https://...",
    "document_title": "Document Title",
    "chunk_index": 0,
    "locale": "en-US",
    "article_id": "123",
    "page_hash": "abc123",
    "h1": "Section Title"
  }
}
```

---

## Configuration

### Chunk Size Settings (`config/settings.py`)

```python
CHUNK_SIZE: int = 512        # Max chunk size (characters)
CHUNK_OVERLAP: int = 64      # Overlap between chunks
```

To change chunk size for testing:
```python
from src.processor.chunker import SemanticChunker

# Custom chunk size
chunker = SemanticChunker(chunk_size=1000, chunk_overlap=100)
```

---

## Troubleshooting

### No real data found?

**Error:** `pytest.skip("No real scraped data found")`

**Solution:** Generate test data first:
```bash
python scripts/test_scraper_10pages.py
```

This creates `tests/.test_data/raw/raw_data_TIMESTAMP.json`

### Import errors?

**Error:** `ModuleNotFoundError: No module named 'langchain_text_splitters'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
pip install langchain-text-splitters
```

### Tests failing?

Check that all processor tests pass:
```bash
pytest tests/unit/test_processor_pipeline.py -v
```

All 14 tests should pass. If not, check:
1. Dependencies installed correctly
2. Test data exists in `tests/.test_data/raw/`
3. No file permission issues

---

## Next Steps

### For Embeddings Stage

1. **Load chunks:**
   ```python
   chunks = json.load(open("tests/.test_data/chunks/chunks_LATEST.json"))
   ```

2. **Generate embeddings:**
   ```python
   for chunk in chunks:
       embedding = your_model.encode(chunk["content"])
       chunk["embedding"] = embedding.tolist()
   ```

3. **Save embeddings:**
   ```python
   output_file = "tests/.test_data/embeddings/embeddings_TIMESTAMP.json"
   json.dump(chunks, open(output_file, 'w'))
   ```

4. **Test embedding stage:**
   - Load chunks with embeddings
   - Test similarity search
   - Verify embedding dimensions

---

## Summary

- ✅ **39 processor tests** - All passing
- ✅ **Real test data** - 10 documents, 124 chunks
- ✅ **Sequential pipeline** - Raw → Processed → Chunks
- ✅ **Ready for embeddings** - Chunks in correct format

**Test data location:** `tests/.test_data/`
**Next stage input:** `tests/.test_data/chunks/chunks_*.json`

