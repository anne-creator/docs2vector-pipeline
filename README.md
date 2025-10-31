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
┌─────────────┐
│   Scraper   │ → Raw HTML/Text data
└─────────────┘
       ↓
┌─────────────┐
│  Processor  │ → Cleaned Markdown + Metadata
└─────────────┘
       ↓
┌─────────────┐
│  Chunker    │ → Semantic chunks with overlap
└─────────────┘
       ↓
┌─────────────┐
│ Embeddings  │ → Vector embeddings for chunks
└─────────────┘
       ↓
┌─────────────┐
│   Storage   │ → Neo4j Aura + Local files
└─────────────┘
```

> **Note**: While the diagram shows sequential stages, the actual execution is **concurrent and asynchronous**. See [Concurrent Processing Model](#concurrent-processing-model) for detailed explanation.

### Core Modules

- **`src/scraper/`**: Enhanced Scrapy spider with change detection
- **`src/processor/`**: HTML cleaning, Markdown conversion, semantic chunking
- **`src/embeddings/`**: Vector embedding generation using sentence-transformers
- **`src/storage/`**: Local file management and Neo4j Aura integration
- **`src/pipeline/`**: Orchestration and scheduling logic
- **`src/utils/`**: Shared utilities (hashing, validation, exceptions)

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
- **Environment variables** (`.env` file)
- **`config/settings.py`** for defaults and validation

Key configuration options:
- `CHUNK_SIZE`: Maximum chunk size in characters (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 64)
- `EMBEDDING_MODEL`: Embedding model name (default: all-MiniLM-L6-v2)
- `EMBEDDING_BATCH_SIZE`: Batch size for embedding generation (default: 32)
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

Final processed data is loaded into Neo4j Aura with:
- **Document nodes** with URL, title, and metadata
- **Chunk nodes** with content, embeddings, and indexing
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
pytest -m integration   # Run only integration tests
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

## Troubleshooting

### Neo4j Connection Issues
- Verify `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` in `.env`
- Check network connectivity to Neo4j Aura
- Verify database name matches

### Scraper Not Working
- Check robots.txt compliance
- Verify start URLs are accessible
- Review Scrapy logs in console output

### Embedding Generation Slow
- Reduce `EMBEDDING_BATCH_SIZE` if memory constrained
- Consider using GPU acceleration
- Process in smaller batches

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support contact information here]

