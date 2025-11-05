# Amazon Sellers Data Pipeline

A production-ready data pipeline for extracting, processing, and storing Amazon Seller Central help documentation into a Neo4j Aura vector database for RAG (Retrieval Augmented Generation) systems.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Running the Pipeline](#running-the-pipeline)
  - [Running Scraper Directly](#running-scraper-directly)
  - [Configuration](#configuration)
- [Data Storage](#data-storage)
- [Testing](#testing)
- [Development](#development)
  - [Project Structure](#project-structure)
  - [Adding New Features](#adding-new-features)
  - [Code Style](#code-style)
- [Change Detection](#change-detection)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Concurrent Processing Model](#concurrent-processing-model)
- [Performance Considerations](#performance-considerations)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Troubleshooting](#troubleshooting)

## Overview

This pipeline implements a complete workflow for:
- **Scraping** Amazon Seller Central documentation
- **Processing** HTML content into semantic Markdown chunks
- **Generating** vector embeddings for semantic search
- **Storing** processed data in Neo4j Aura with vector indexing

## Architecture

The pipeline follows a modular architecture with clear separation of concerns:

```
┌──────────────────┐
│   1. Scraper     │ → output: Raw HTML/Text data
└──────────────────┘
         ↓
┌──────────────────┐
│   2. Processor   │ → output: HTML cleaning, Markdown conversion
└──────────────────┘
         ↓
┌──────────────────┐
│ 3. Semantic      │ → output: Intelligently segmented chunks + Metadata
│    Chunking      │
└──────────────────┘
         ↓
┌──────────────────┐
│ 4. Embeddings    │ → output: Vector embeddings for chunks
└──────────────────┘
         ↓
┌──────────────────┐
│   5. Storage     │ → Neo4j Aura + Local files
└──────────────────┘
```

> **Note**: While the diagram shows sequential stages, the actual execution is **concurrent and asynchronous**. See [Concurrent Processing Model](#concurrent-processing-model) for detailed explanation.

### Core Modules

- **`src/scraper/`**: Enhanced Scrapy spider with change detection
- **`src/processor/`**: HTML cleaning and Markdown conversion
- **`src/processor/chunker.py`**: Semantic chunking with intelligent text segmentation and automatic chunk title generation
- **`src/embeddings/`**: Vector embedding generation using sentence-transformers
- **`src/storage/`**: Local file management and Neo4j Aura integration
- **`src/pipeline/`**: Orchestration and scheduling logic
- **`src/utils/`**: Shared utilities (hashing, validation, exceptions)

### Semantic Chunking Features

The chunking system provides intelligent text segmentation with the following features:

**Automatic Chunk Title Generation** ✨
- Extracts descriptive titles from markdown header hierarchy
- Combines parent and child headers for context (e.g., "Payment > Bank Details")
- Falls back to document title when no headers are available
- Adds part numbers to sub-chunks (e.g., "Section (Part 1)")

**Example:**
```
Document: "Account Settings"
  Chunk 1: "Account Settings > Payment Information"
  Chunk 2: "Payment Information > Bank Account Details"
  Chunk 3: "Payment Information > Credit Card Information"
```

This improves RAG retrieval by providing both document-level and chunk-level context.

## Prerequisites

- Python 3.8 or higher
- Neo4j Aura account (or local Neo4j instance)
- Access to Amazon Seller Central help documentation

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password-here
   NEO4J_DATABASE=neo4j
   DATA_DIR=./data
   ```

5. **Validate environment setup**:
   ```bash
   python scripts/setup_env.py
   ```

## Usage

### Running the Pipeline

#### Full Pipeline Execution
Run the complete pipeline from scraping to Neo4j loading:
```bash
python scripts/run_pipeline.py --mode full
```

#### Incremental Update
Only process changed documents:
```bash
python scripts/run_pipeline.py --mode incremental
```

#### Auto Mode
Automatically determine if update is needed:
```bash
python scripts/run_pipeline.py --mode auto
```

#### Check Only
Check if an update is needed without running:
```bash
python scripts/run_pipeline.py --check
```

### Running Scraper Directly

You can also run the Scrapy spider directly:
```bash
cd scrapy_project
scrapy crawl amazon_seller_help
```

### Configuration

Configuration is managed through:
- **Environment variables** (`.env` file) - see `env.example` for template
- **`config/settings.py`** for defaults and validation

#### Embedding Configuration

The pipeline supports **three embedding providers**:
- **Sentence Transformers** (local, default) - No API key needed
- **Ollama** (local server) - No API key needed
- **OpenAI-Compatible APIs** (cloud) - API key required

**Quick Setup**:
```bash
# Copy the example configuration
cp env.example .env

# Edit .env to set your provider (default is sentence-transformers)
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

📖 **See [docs/EMBEDDING_CONFIGURATION.md](docs/EMBEDDING_CONFIGURATION.md) for detailed setup guide**

#### Key Configuration Options

- `EMBEDDING_PROVIDER`: Provider to use (default: sentence-transformers)
- `EMBEDDING_MODEL`: Model name (default: BAAI/bge-small-en-v1.5)
- `EMBEDDING_BATCH_SIZE`: Batch size for embedding generation (default: 32)
- `CHUNK_SIZE`: Maximum chunk size in characters (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 64)
- `SCRAPER_DOWNLOAD_DELAY`: Delay between requests in seconds (default: 1.0)
- `SCRAPER_CONCURRENT_REQUESTS`: Number of concurrent requests (default: 2)

## Data Storage

The pipeline uses a local file-based storage structure:

```
data/
├── raw/              # Raw scraped JSON data
├── raw_data_*.json
├── processed/         # Processed Markdown documents
│   └── processed_docs_*.json
├── chunks/          # Semantic chunks
│   └── chunks_*.json
├── embeddings/     # Chunks with embeddings
│   └── chunks_with_embeddings_*.json
├── hashes/          # Content hash tracking
│   └── content_hashes.json
└── manifests/       # Update manifests
```

### Chunk Metadata Structure

Each chunk includes rich metadata for improved retrieval:

```json
{
  "id": "G2?locale=en-US_1",
  "content": "...",
  "metadata": {
    "source_url": "https://...",
    "document_title": "Help for Amazon Sellers",
    "chunk_title": "Payment Information > Bank Details",
    "chunk_index": 1,
    "sub_chunk_index": 0,
    "chunk_id": "G2?locale=en-US_1",
    "doc_id": "https://...",
    "h1": "Account Settings",
    "h2": "Payment Information",
    "h3": "Bank Details",
    "last_updated": "",
    "breadcrumbs": [],
    "related_links": [...],
    "category": [],
    "article_id": "2",
    "locale": "en-US",
    "page_hash": "...",
    "change_status": "new"
  }
}
```

**Key Metadata Fields:**
- `document_title`: Parent document's title
- `chunk_title`: Descriptive title for this specific chunk (extracted from headers)
- `h1`, `h2`, `h3`, `h4`: Markdown header hierarchy for context
- `chunk_index`: Position within document
- `sub_chunk_index`: Position within split section (if applicable)

### Neo4j Storage

Final processed data is loaded into Neo4j Aura with:
- **Document nodes** with URL, title, and metadata
- **Chunk nodes** with content, chunk_title, embeddings, and full metadata
- **Relationships** between documents and chunks
- **Vector index** for semantic similarity search

## Testing

### Running Unit Tests

Run all unit tests:
```bash
pytest tests/unit/
```

Run specific test file:
```bash
pytest tests/unit/test_preprocessor.py
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html tests/unit/
```

Run tests with specific markers:
```bash
pytest -m unit          # Run only unit tests
pytest -m "not slow"    # Skip slow tests
```

### Test Coverage

Generate and view coverage reports:

**HTML Report** (recommended for detailed analysis):
```bash
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html  # View in browser
```

**Terminal Report**:
```bash
pytest --cov=src --cov-report=term-missing tests/
```

**Coverage Targets**:
- Overall coverage goal: **>80%**
- Critical modules (processor, storage, embeddings): **>90%**
- Utility modules: **>85%**

**Viewing Coverage by Module**:
```bash
# Generate detailed coverage for specific module
pytest --cov=src.processor --cov-report=term-missing tests/unit/test_preprocessor.py
```

### Test Structure

- **Unit tests**: Test individual components in isolation
  - `test_preprocessor.py`: HTML/Markdown conversion
  - `test_chunker.py`: Semantic chunking logic
  - `test_embeddings.py`: Embedding generation (mocked)
  - `test_file_manager.py`: File operations
  - `test_neo4j_client.py`: Neo4j operations (mocked)
  - `test_hash_utils.py`: Content hashing
  - `test_metadata.py`: Metadata extraction
  - `test_validators.py`: Data validation

- **Integration tests** (future): Test component interactions
- **End-to-end tests** (future): Test full pipeline execution

### Coverage Exclusions

Excluded from coverage metrics:
- Configuration files (`config/*.py`)
- CLI entry points (`scripts/*.py`)
- External dependencies and mock objects
- Error handling for unreachable edge cases

## Development

### Project Structure

```
docs2vector-pipeline/
├── config/              # Configuration files
├��─ src/                 # Source code
│   ├── pipeline/       # Orchestration
│   ├── scraper/         # Web scraping
│   ├── processor/      # Content processing
│   ├── embeddings/     # Vector generation
│   ├── storage/        # Storage backends
│   └── utils/          # Utilities
├── tests/               # Test suite
├── scrapy_project/      # minimal configuration files to run Scrapy spiders:
├── scripts/             # CLI scripts Executable scripts for running the pipeline
└── data/                # Data storage (gitignored)
```

### Adding New Features

1. **New processor module**: Add to `src/processor/`
2. **New storage backend**: Implement interface in `src/storage/`
3. **New scraper**: Extend `src/scraper/spider.py`

### Code Style

The project follows PEP 8 style guidelines. Use `black` for formatting:
```bash
black src/ tests/
```

## Change Detection

The pipeline implements intelligent change detection:
- **Content hashing**: MD5 hashes of scraped content
- **Version tracking**: Persistent hash storage in `data/hashes/`
- **Change status**: Identifies new, updated, or unchanged documents
- **Sampling**: Can sample URLs to detect changes before full update

## Error Handling

The pipeline uses custom exceptions:
- `PipelineError`: Base exception for pipeline errors
- `ScraperError`: Scraping-related errors
- `ProcessorError`: Processing errors
- `EmbeddingError`: Embedding generation errors
- `StorageError`: Storage operation errors

All errors are logged with context for debugging.

## Logging

Logging is configured via `config/logging.yaml`:
- **Console output**: INFO level and above
- **File output**: DEBUG level to `logs/pipeline.log`
- **Rotating logs**: Max 10MB per file, 5 backups

## Concurrent Processing Model

### Overview

This pipeline implements **concurrent and asynchronous processing** at multiple levels, allowing efficient handling of hundreds or thousands of documents without waiting for all scraping to complete before processing begins.

### Stage 1: Scrapy Spider (Asynchronous Scraping)

**Scrapy's Built-in Concurrency**:
- Scrapy is built on **Twisted**, an asynchronous networking framework
- Multiple pages are fetched **simultaneously** (controlled by `SCRAPER_CONCURRENT_REQUESTS` setting, default: 2)
- When a spider encounters multiple URLs, it doesn't wait for one to finish before requesting the next

**Why `yield` Instead of `return`**:
```python
def parse(self, response):
    # Process multiple items on a page
    for product_link in response.css('a.product::attr(href)'):
        yield scrapy.Request(product_link, callback=self.parse_product)
        # Spider continues processing remaining links immediately
```

- `yield` **returns control** to Scrapy's engine while keeping the function alive
- Allows processing of **all items** (links, products, etc.) on a page
- If `return` was used, only the **first item** would be processed
- The spider continues running to handle all discovered URLs

**Flow Example**:
```
Time 0s:  Request Page 1, Page 2 (concurrent)
Time 1s:  Page 1 received → yield 5 links → Request Link 1, 2, 3 (concurrent)
Time 1.5s: Page 2 received → yield 3 links → Request Link 4, 5, 6 (concurrent)
Time 2s:  Links 1, 2, 3 received → yield items → Sent to pipeline
...continues asynchronously...
```

### Stage 2: Scrapy Item Pipeline (Per-Item Processing)

**Concurrent Item Processing**:
- Each item yielded by the spider is **immediately sent** to the pipeline
- Does **NOT** wait for all scraping to complete
- Multiple items are processed **in parallel** by pipeline stages

**Architecture Flow**:
```
Spider yields Item 1 ─────→ Pipeline processes Item 1 ─────→ Saved to file
     ↓ (continues)              ↓ (while...)                     ↓
Spider yields Item 2 ─────→ Pipeline processes Item 2 ─────→ Saved to file
     ↓ (continues)              ↓ (while...)                     ↓
Spider yields Item 3 ─────→ Pipeline processes Item 3 ─────→ Saved to file
```

**Pipeline Stages (per-item)**:
1. **Item Validation** - `process_item()` validates each item
2. **Data Cleaning** - HTML cleaning, Markdown conversion (if enabled)
3. **Storage** - Write to JSON file

**Key Characteristics**:
- Pipeline stages are **sequential per item** but **concurrent across items**
- Item 1 can be in "Storage" stage while Item 2 is in "Validation" stage
- Like an **assembly line**: continuous flow rather than batch processing

### Stage 3: Post-Scraping Processing (Batch Operations)

After scraping completes, the following stages run on **collected data**:

**Processor & Chunker**:
- Processes all scraped documents from saved files
- Currently **sequential** (one document at a time)
- Can be parallelized using `multiprocessing` or `concurrent.futures` (future enhancement)

**Embedding Generation**:
- Processes chunks in **batches** (configurable via `EMBEDDING_BATCH_SIZE`, default: 32)
- Batch processing optimizes model inference
- Example with 1000 chunks, batch size 32:
  ```
  Batch 1: Process chunks 0-31   (parallel within batch via vectorization)
  Batch 2: Process chunks 32-63  (parallel within batch via vectorization)
  ...
  Batch 32: Process chunks 992-999
  ```

**Neo4j Loading**:
- Uses **batch transactions** (default: 100 chunks per transaction)
- Each transaction commits atomically
- Connection pooling enables efficient database operations

### Real-World Example: Processing 500 Documents

**Traditional Sequential Approach** (NOT how we do it):
```
Scrape all 500 docs (500s) → Process all (100s) → Chunk all (50s) → Embed all (200s) → Load all (50s)
Total: 900 seconds
```

**Our Concurrent Approach**:
```
Time 0s:    Start scraping (concurrent requests)
Time 1s:    Doc 1 scraped → Pipeline processes → Saved
Time 1.5s:  Doc 2 scraped → Pipeline processes → Saved (while scraping continues)
Time 2s:    Doc 3 scraped → Pipeline processes → Saved (while scraping continues)
...
Time 300s:  All docs scraped and pipeline-processed
Time 400s:  Post-processing (chunking, embeddings, Neo4j) on all collected data
Total: ~400 seconds (55% reduction)
```

### Configuration for Concurrency

Control concurrent behavior via settings:

**Scrapy Concurrency**:
```python
SCRAPER_CONCURRENT_REQUESTS = 2  # Number of simultaneous HTTP requests
SCRAPER_DOWNLOAD_DELAY = 1.0     # Delay between requests (politeness)
```

**Embedding Batch Size**:
```python
EMBEDDING_BATCH_SIZE = 32  # Process 32 chunks at once
```

**Neo4j Batch Size**:
```python
NEO4J_BATCH_SIZE = 100  # Commit 100 chunks per transaction
```

### Benefits of This Architecture

1. **Faster Execution**: Scraping and pipeline processing overlap
2. **Better Resource Utilization**: CPU works while waiting for network I/O
3. **Scalability**: Can handle thousands of documents efficiently
4. **Resilience**: Individual item failures don't block other items
5. **Incremental Progress**: Data is saved continuously, not all at once

### Monitoring Concurrent Execution

Watch for these indicators in logs:
- Scrapy shows: `Crawled (200) <GET url>` - multiple URLs in progress
- Pipeline shows: `Processing item: <item_id>` - items processed as they arrive
- Not: "Waiting for all scraping to complete..." (doesn't happen)

## Performance Considerations

- **Batch processing**: Embeddings generated in configurable batches
- **Connection pooling**: Neo4j connection reuse
- **Incremental updates**: Only process changed documents
- **Local caching**: Intermediate results stored locally
- **Concurrent scraping**: Multiple pages fetched simultaneously (Scrapy's async engine)
- **Streaming pipeline**: Items processed as scraped, not in bulk

## Limitations

- Scraper respects robots.txt and rate limits
- Embedding generation requires GPU for large-scale processing
- Neo4j vector index requires Neo4j 5.0+ (Aura supports this)
- Change detection is based on content hashes (not structural analysis)

## Future Enhancements

- Enhanced change detection with structural analysis
- Support for additional data sources
- PDF document processing
- Multi-language support
- Advanced chunking strategies
- Integration testing suite
- Performance benchmarking

## Running BGE-small-en-v1.5 Locally

This guide explains how to run the BGE-small-en-v1.5 embedding model locally using two approaches:
1. **Sentence Transformers** (Direct, Recommended)
2. **Ollama** (Alternative, if you prefer Ollama server)

### Option 1: Using Sentence Transformers (Recommended) ⭐

This is the **simplest and recommended** approach for BGE-small-en-v1.5.

#### Setup

1. **Configure Environment**:
   ```bash
   # Create or edit .env file
   cat > .env << 'EOF'
   EMBEDDING_PROVIDER=sentence-transformers
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   EMBEDDING_BATCH_SIZE=32
   
   # ... other settings
   EOF
   ```

2. **First Run** (automatic model download):
   ```bash
   # The model will be automatically downloaded on first use (~130MB)
   python scripts/run_pipeline.py
   ```

3. **Pre-download Model** (optional):
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
   ```

#### Specifications
- **Embedding Dimension**: 384
- **Max Tokens**: 512
- **Model Size**: ~130MB
- **Memory Usage**: ~500MB-1GB during inference
- **Speed**: Fast (optimized for CPU and GPU)

#### Advantages
✅ No additional server needed  
✅ Works offline after initial download  
✅ Lower memory footprint  
✅ Direct Python integration  
✅ Best for development and testing  

---

### Option 2: Using Ollama (Alternative)

If you prefer using Ollama server or need to run multiple models, follow this guide.

⚠️ **Note**: Ollama doesn't have the exact `BAAI/bge-small-en-v1.5` model. The closest alternative is `nomic-embed-text` (768-dim).

#### Prerequisites Check

Before installing, check if Ollama is already installed:

```bash
# Check if Ollama is installed
which ollama

# If installed, check version
ollama --version

# Check if Ollama service is running
curl http://localhost:11434/api/tags 2>/dev/null && echo "✅ Ollama is running" || echo "❌ Ollama not running"
```

#### Install Ollama

**On macOS**:
```bash
# Method 1: Using Homebrew (recommended)
brew install ollama

# Method 2: Official installer
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

**On Linux**:
```bash
# Official installer
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

**On Windows**:
1. Download installer from https://ollama.ai/download
2. Run the installer
3. Verify in PowerShell: `ollama --version`

#### Setup Ollama Embedding Model

**Terminal 1: Start Ollama Server**
```bash
# Start Ollama server (keep this terminal open)
ollama serve
```

**Terminal 2: Pull Embedding Model**
```bash
# Pull the nomic-embed-text model (closest to BGE-small)
ollama pull nomic-embed-text

# Alternative: mxbai-embed-large (higher quality, larger)
# ollama pull mxbai-embed-large

# List all downloaded models
ollama list
```

#### Test the Model

```bash
# Test embedding generation
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "This is a test embedding"
}'

# Expected output: JSON with "embedding" array
```

#### Configure Pipeline for Ollama

```bash
# Create or edit .env file
cat > .env << 'EOF'
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_BATCH_SIZE=16

# ... other settings
EOF
```

#### Run the Pipeline

```bash
# Verify configuration
python scripts/verify_embedding_config.py

# Run pipeline (make sure Ollama server is running!)
python scripts/run_pipeline.py
```

#### Ollama Model Specifications

| Model | Dimensions | Context | Memory | Use Case |
|-------|-----------|---------|--------|----------|
| **nomic-embed-text** | 768 | 8192 | ~700MB | General purpose, long context |
| **mxbai-embed-large** | 1024 | 512 | ~1.2GB | Highest quality |

---

### Performance Comparison

| Approach | Setup | Memory | Speed | Offline | Recommended For |
|----------|-------|--------|-------|---------|----------------|
| **Sentence Transformers** ⭐ | Easy | 500MB-1GB | ⚡⚡⚡ | ✅ Yes | Development, Production |
| **Ollama** | Moderate | 700MB-1.5GB | ⚡⚡ | ✅ Yes | Multi-model workflows |

---

### Memory Management

#### Check Available Memory

```bash
# Quick memory check (macOS/Linux)
free -h  # Linux
vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f Mi\n", "$1:", $2 * $size / 1048576);'  # macOS

# Or use Activity Monitor (macOS) / Task Manager (Windows)
open -a "Activity Monitor"  # macOS
```

#### Free Up Memory Before Running

1. **Close memory-intensive applications**:
   ```bash
   # Close common memory hogs
   killall "Google Chrome"
   killall "Slack"
   osascript -e 'quit app "Docker"'  # If not needed
   ```

2. **Monitor memory usage**:
   ```bash
   # Install htop (if not installed)
   brew install htop  # macOS
   
   # Run htop to monitor
   htop
   # Press 'F6' to sort by memory
   # Press 'q' to quit
   ```

3. **Clear system cache** (if needed):
   ```bash
   # Clear user cache
   rm -rf ~/Library/Caches/*
   
   # Purge system memory (requires sudo)
   sudo purge
   ```

#### Recommended Memory Availability

- **Minimum**: 4GB free RAM
- **Recommended**: 8GB free RAM
- **Optimal**: 12GB+ free RAM

**Memory breakdown for pipeline**:
- Python process: ~1-2GB
- Embedding model: ~500MB-1.5GB (depending on choice)
- Ollama server: ~500MB (if using Ollama)
- Working memory: ~2-3GB
- **Total**: 4-7GB

---

### Troubleshooting

#### Issue: Model Download Fails (Sentence Transformers)

```bash
# Solution 1: Clear cache and retry
rm -rf ~/.cache/huggingface/
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Solution 2: Manual download
export HF_ENDPOINT=https://hf-mirror.com  # If behind firewall
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
```

#### Issue: Ollama Connection Refused

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama server
ollama serve

# Check if model exists
ollama list

# Pull model if missing
ollama pull nomic-embed-text
```

#### Issue: Out of Memory

```bash
# Reduce batch size in .env
EMBEDDING_BATCH_SIZE=8  # Default is 32

# Or use CPU instead of GPU
# Set device in code (if needed)
```

#### Issue: Slow Embedding Generation

```bash
# Check GPU availability (if applicable)
python -c "import torch; print('GPU available:', torch.cuda.is_available())"

# For CPU-only systems, use smaller batch sizes
EMBEDDING_BATCH_SIZE=16
```

---

### Quick Start Commands Reference

```bash
# ============================================================================
# Option 1: Sentence Transformers (Recommended)
# ============================================================================

# Setup
echo "EMBEDDING_PROVIDER=sentence-transformers" >> .env
echo "EMBEDDING_MODEL=BAAI/bge-small-en-v1.5" >> .env

# Run (model downloads automatically on first use)
python scripts/run_pipeline.py

# ============================================================================
# Option 2: Ollama
# ============================================================================

# Check if installed
ollama --version || brew install ollama

# Terminal 1: Start server
ollama serve

# Terminal 2: Setup and run
ollama pull nomic-embed-text
echo "EMBEDDING_PROVIDER=ollama" >> .env
echo "EMBEDDING_MODEL=nomic-embed-text" >> .env
python scripts/run_pipeline.py

# ============================================================================
# Monitoring
# ============================================================================

# Terminal 3: Monitor resources
htop  # or: watch -n 2 "ps aux | sort -rk 4 | head -10"
```

---

### Additional Resources

- **Sentence Transformers Documentation**: https://www.sbert.net/
- **BGE Model Card**: https://huggingface.co/BAAI/bge-small-en-v1.5
- **Ollama Documentation**: https://ollama.ai/docs
- **Embedding Configuration Guide**: [docs/EMBEDDING_CONFIGURATION.md](docs/EMBEDDING_CONFIGURATION.md)

