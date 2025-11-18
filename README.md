# Amazon Sellers Data Pipeline

A production-ready data pipeline for extracting, processing, and storing Amazon Seller Central help documentation as vectors in Pinecone for RAG (Retrieval Augmented Generation) systems. Includes REST API for automation with N8N.

## 🎯 Overview

This pipeline provides a **complete end-to-end solution** for:

1. **Scraping** Amazon Seller Central documentation (Scrapy + Playwright)
2. **Processing** HTML content into semantic Markdown chunks
3. **Generating** vector embeddings using sentence-transformers
4. **Storing** vectors in **Pinecone** for semantic search
5. **API Server** for triggering pipeline from N8N workflows

**Key Features:**
- ✅ **Streaming pipeline** - 55-60% faster than batch processing
- ✅ **Intelligent sync** - Only uploads new/updated chunks to Pinecone
- ✅ **REST API** - Trigger pipeline via HTTP (perfect for N8N)
- ✅ **Change detection** - Avoid re-processing unchanged content
- ✅ **Rich metadata** - Hierarchical headers, breadcrumbs, relationships
- ✅ **No Docker required** - Runs locally with Python

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
  - [Running Pipeline Directly](#running-pipeline-directly)
  - [Running API Server](#running-api-server-for-n8n)
  - [N8N Integration](#n8n-integration)
- [Project Structure](#-project-structure)
- [Data Flow](#-data-flow)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Pinecone account (free tier available)
- 4GB+ RAM recommended

### 1. Install

```bash
# Clone/navigate to project
cd docs2vector-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy example config
cp env.example .env

# Edit .env with your Pinecone credentials
USE_PINECONE=true
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=amazon-seller-docs
PINECONE_ENVIRONMENT=us-west1-gcp
```

**Create Pinecone Index:**
1. Go to https://app.pinecone.io/
2. Create index: Name=`amazon-seller-docs`, Dimensions=`384`, Metric=`cosine`
3. Copy API key to `.env`

### 3. Run

**Option A: Run Pipeline Directly**
```bash
python scripts/run_pipeline.py --mode full
```

**Option B: Run API Server (for N8N)**
```bash
python scripts/run_api_server.py
# API available at: http://localhost:8000
# Trigger: POST http://localhost:8000/api/v1/trigger-scrape
```

---

## 🏗️ Architecture

### High-Level Flow

```
┌──────────────────┐
│   1. Scraper     │ → Scrapy spider scrapes Amazon docs
└────────┬─────────┘
         ↓
┌──────────────────┐
│   2. Processor   │ → HTML → Markdown conversion
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 3. Chunker       │ → Semantic chunking with metadata
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 4. Embeddings    │ → Generate 384-dim vectors
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 5. Pinecone      │ → Upload vectors to Pinecone
└──────────────────┘
```

**Note:** Pipeline uses **streaming mode** by default - stages run concurrently for 55-60% speed improvement.

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Scraper** | Web scraping with Scrapy + Playwright | `src/scraper/` |
| **Processor** | HTML cleaning, Markdown conversion | `src/processor/` |
| **Chunker** | Semantic text segmentation | `src/processor/chunker.py` |
| **Embeddings** | Vector generation (sentence-transformers) | `src/embeddings/` |
| **Pinecone** | Vector database integration | `src/integrations/pinecone/` |
| **API Server** | REST API for N8N automation | `src/api/` |
| **Orchestrator** | Pipeline coordination | `src/pipeline/` |

### API Server (for N8N Automation)

The API server allows external systems (like N8N) to trigger pipeline execution:

```
┌─────────────────┐
│ N8N Workflow    │ Cron trigger (monthly)
└────────┬────────┘
         │ POST /api/v1/trigger-scrape
         ↓
┌─────────────────┐
│ FastAPI Server  │ Runs pipeline in background
└────────┬────────┘
         │ Webhook notification
         ↓
┌─────────────────┐
│ N8N Webhook     │ Receives completion status
└─────────────────┘
```

**API Endpoints:**
- `POST /api/v1/trigger-scrape` - Trigger pipeline execution
- `GET /api/v1/status/{job_id}` - Check job status
- `GET /api/v1/health` - Health check
- `GET /api/v1/jobs` - List recent jobs
- `GET /docs` - Interactive API documentation

---

## 📦 Installation

### 1. System Requirements

- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB for dependencies + data
- **Network**: Internet connection for scraping

### 2. Python Setup

```bash
# Navigate to project directory
cd /path/to/docs2vector-pipeline

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This installs:
# - scrapy (web scraping)
# - sentence-transformers (embeddings)
# - pinecone-client (vector database)
# - fastapi + uvicorn (API server)
# - playwright (browser automation)
# - and more...
```

### 4. Install Playwright Browsers

```bash
# Required for scraping JavaScript-heavy pages
playwright install chromium
```

### 5. Verify Installation

```bash
# Check Python version
python --version  # Should be 3.11+

# Test imports
python -c "import scrapy, pinecone, fastapi; print('✅ All imports successful')"
```

---

## ⚙️ Configuration

### Environment Variables

All configuration is in `.env` file:

```bash
# Copy example
cp env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

### Required Settings

```bash
# Pinecone Configuration (REQUIRED)
USE_PINECONE=true
PINECONE_API_KEY=your-api-key-here          # Get from https://app.pinecone.io/
PINECONE_INDEX_NAME=amazon-seller-docs       # Your index name
PINECONE_ENVIRONMENT=us-west1-gcp            # Your environment/region
PINECONE_NAMESPACE=                          # Optional namespace

# Embedding Configuration
EMBEDDING_PROVIDER=sentence-transformers     # Local, no API key needed
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5      # 384-dim vectors
EMBEDDING_BATCH_SIZE=32
```

### Optional Settings

```bash
# Pipeline Mode
PIPELINE_MODE=streaming                      # "streaming" (faster) or "batch"
STORAGE_MODE=local                           # "local" or "s3"

# Scraper Settings
SCRAPER_DOWNLOAD_DELAY=1.0
SCRAPER_CONCURRENT_REQUESTS=2
SCRAPER_DEPTH_LIMIT=4

# Chunking Settings
CHUNK_SIZE=512
CHUNK_OVERLAP=64

# AWS S3 (optional backup)
S3_BUCKET_NAME=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

### Pinecone Index Setup

**Before first run, create Pinecone index:**

1. **Sign up at** https://app.pinecone.io/ (free tier available)
2. **Create new index:**
   - **Name**: `amazon-seller-docs` (or your choice)
   - **Dimensions**: `384` (matches BAAI/bge-small-en-v1.5)
   - **Metric**: `cosine`
   - **Region**: Choose closest to you
3. **Copy credentials:**
   - API Key → `PINECONE_API_KEY` in `.env`
   - Environment → `PINECONE_ENVIRONMENT` in `.env`

---

## 💻 Usage

### Running Pipeline Directly

**Full Pipeline Execution:**
```bash
# Run complete pipeline: scrape → process → chunk → embed → upload
python scripts/run_pipeline.py --mode full
```

**Incremental Update:**
```bash
# Only process changed documents (faster)
python scripts/run_pipeline.py --mode incremental
```

**Check for Updates:**
```bash
# Check if updates are needed without running
python scripts/run_pipeline.py --check
```

### Running API Server (for N8N)

**Start API Server:**
```bash
# Default: localhost:8000
python scripts/run_api_server.py

# Custom port
API_PORT=9000 python scripts/run_api_server.py
```

**Server will be available at:**
- API Base: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### API Usage Examples

**1. Trigger Pipeline:**
```bash
curl -X POST http://localhost:8000/api/v1/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{"mode": "full"}'

# Response:
# {
#   "job_id": "job_20241118_123045",
#   "status": "started",
#   "message": "Pipeline execution started successfully"
# }
```

**2. Check Status:**
```bash
curl http://localhost:8000/api/v1/status/job_20241118_123045

# Response:
# {
#   "job_id": "job_20241118_123045",
#   "status": "running",  # or "completed", "failed"
#   "results": {...}      # populated when completed
# }
```

**3. Health Check:**
```bash
curl http://localhost:8000/api/v1/health

# Response:
# {"status": "healthy", "message": "API is running", "version": "1.0.0"}
```

### N8N Integration

**Simple N8N Workflow (3 nodes):**

```
1. Cron Trigger → Monthly schedule
   ↓
2. HTTP Request → POST /api/v1/trigger-scrape
   ↓
3. Webhook → Receive completion notification
   ↓
4. Email/Slack → Send notification (optional)
```

**N8N HTTP Request Node Configuration:**
- **Method**: POST
- **URL**: `http://your-server:8000/api/v1/trigger-scrape`
- **Body**: `{"webhook_url": "https://your-n8n.com/webhook/abc123"}`

**Detailed N8N Setup:** See `docs/N8N_WORKFLOW.md`

---

## 📂 Project Structure

```
docs2vector-pipeline/
├── src/
│   ├── api/                    # FastAPI server
│   │   ├── server.py          # API endpoints
│   │   └── models.py          # Request/response models
│   ├── scraper/               # Web scraping
│   │   ├── spider.py          # Scrapy spider
│   │   └── pipeline.py        # Scrapy pipelines
│   ├── processor/             # Content processing
│   │   ├── preprocessor.py   # HTML → Markdown
│   │   ├── chunker.py         # Semantic chunking
│   │   └── metadata.py        # Metadata extraction
│   ├── embeddings/            # Vector generation
│   │   ├── generator.py       # Embedding pipeline
│   │   └── providers.py       # Provider implementations
│   ├── integrations/          # External integrations
│   │   ├── pinecone/          # Pinecone client
│   │   ├── s3/                # AWS S3 client
│   │   └── n8n/               # N8N notifications
│   ├── pipeline/              # Orchestration
│   │   ├── orchestrator.py   # Main coordinator
│   │   └── stream_processor.py # Streaming mode
│   └── storage/               # Data management
│       └── file_manager.py    # Local file operations
├── scripts/
│   ├── run_pipeline.py        # Run pipeline directly
│   └── run_api_server.py      # Start API server
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── data/                      # Data storage (created at runtime)
│   ├── raw/                   # Scraped data
│   ├── processed/             # Processed Markdown
│   ├── chunks/                # Chunked documents
│   ├── embeddings/            # Chunks with vectors
│   └── hashes/                # Content hashes
├── docs/                      # Documentation
│   ├── API_INTEGRATION.md     # API usage guide
│   ├── N8N_WORKFLOW.md        # N8N setup guide
│   └── DEPLOYMENT.md          # Deployment options
├── config/
│   ├── settings.py            # Configuration management
│   └── logging.yaml           # Logging configuration
├── .env                       # Environment variables (you create)
├── env.example                # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔄 Data Flow

### 1. Scraping Phase

```python
# Scrapy spider crawls Amazon Seller Central
# - Respects robots.txt and rate limits
# - Concurrent requests (configurable)
# - Saves raw HTML/JSON to data/raw/
```

**Output:** `data/raw/item_*.json` files

### 2. Processing Phase

```python
# HTML → Markdown conversion
# - Removes navigation, ads, footers
# - Preserves semantic structure
# - Extracts metadata (titles, breadcrumbs, links)
```

**Output:** `data/processed/item_*_processed.json` files

### 3. Chunking Phase

```python
# Semantic segmentation
# - Splits by headers (H1, H2, H3)
# - Maintains context with overlap
# - Generates chunk titles
# - Preserves header hierarchy
```

**Output:** `data/chunks/item_*_chunks.json` files

**Example Chunk Structure:**
```json
{
  "id": "G2_chunk_1",
  "content": "Payment processing for sellers involves...",
  "metadata": {
    "document_title": "Amazon Payments Guide",
    "chunk_title": "Payments > Processing > Bank Transfers",
    "source_url": "https://...",
    "h1": "Payment Information",
    "h2": "Processing Methods",
    "h3": "Bank Transfers",
    "chunk_index": 1,
    "change_status": "new"
  }
}
```

### 4. Embedding Phase

```python
# Generate 384-dim vectors using BAAI/bge-small-en-v1.5
# - Batch processing (default: 32 chunks at a time)
# - Uses sentence-transformers (local, no API)
# - CPU or GPU acceleration
```

**Output:** Chunks with `embedding` field added

### 5. Pinecone Upload

```python
# Intelligent sync to Pinecone
# - New chunks → Upload
# - Updated chunks → Delete old + upload new
# - Unchanged chunks → Skip
# - Batch upsert (100-1000 vectors)
```

**Output:** Vectors in Pinecone index

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

### Test Coverage

**Current targets:**
- Overall: >80%
- Critical modules (processor, embeddings): >90%
- Utilities: >85%

### Test Structure

```
tests/
├── unit/
│   ├── test_chunker.py          # Chunking logic
│   ├── test_embeddings.py       # Embedding generation
│   ├── test_pinecone_client.py  # Pinecone integration
│   └── test_preprocessor.py     # HTML processing
└── integration/
    └── test_processing_pipeline.py  # End-to-end tests
```

---

## 🐛 Troubleshooting

### Issue: "PINECONE_API_KEY is required"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify settings
grep PINECONE .env

# Should see:
# USE_PINECONE=true
# PINECONE_API_KEY=your-key
```

### Issue: "Pinecone index not found"

**Solution:**
1. Log in to https://app.pinecone.io/
2. Check index exists with correct name
3. Verify dimensions = 384
4. Check region matches `PINECONE_ENVIRONMENT`

### Issue: "Dimension mismatch" error

**Problem:** Pinecone index dimensions don't match embedding model

**Solution:**
```bash
# Model BAAI/bge-small-en-v1.5 produces 384-dim vectors
# Your Pinecone index MUST be 384 dimensions

# Either:
# 1. Recreate Pinecone index with 384 dims
# OR
# 2. Change embedding model to match your index dimensions
```

### Issue: Pipeline runs slow

**Solutions:**
```bash
# 1. Use streaming mode (faster)
PIPELINE_MODE=streaming

# 2. Reduce batch sizes if low on memory
EMBEDDING_BATCH_SIZE=16

# 3. Increase concurrent requests
SCRAPER_CONCURRENT_REQUESTS=4
```

### Issue: Out of memory

**Solutions:**
```bash
# 1. Reduce batch sizes
EMBEDDING_BATCH_SIZE=8

# 2. Use smaller model (if acceptable)
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Still 384-dim

# 3. Close other applications
# 4. Add swap space (Linux)
```

### Issue: API server not accessible from N8N

**Check:**
```bash
# 1. Server is running
curl http://localhost:8000/api/v1/health

# 2. Firewall allows connections
# 3. Use correct IP (not localhost if on different machine)

# If N8N is on different server:
API_HOST=0.0.0.0 python scripts/run_api_server.py
# Then use: http://YOUR_SERVER_IP:8000
```

---

## 👨‍💻 Development

### Adding New Features

**New Vector Database:**
```python
# 1. Create client in src/integrations/yourvectordb/
# 2. Extend BaseIntegrationClient
# 3. Add to orchestrator.py
```

**New Embedding Provider:**
```python
# 1. Add provider to src/embeddings/providers.py
# 2. Update config/settings.py
# 3. Add to env.example
```

**New Scraper Target:**
```python
# 1. Create spider in src/scraper/
# 2. Configure in scrapy_project/settings.py
```

### Code Style

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Run linter
pylint src/
```

### Performance Monitoring

**Enable detailed logging:**
```bash
# In .env
LOG_LEVEL=DEBUG

# Check logs
tail -f logs/pipeline.log
```

**Monitor resources:**
```bash
# macOS
htop

# Or watch memory
watch -n 2 "ps aux | sort -rk 4 | head -10"
```

### Concurrent Processing Model

The pipeline uses a **streaming architecture** where stages run concurrently:

```
Time 0s:    Scrape Doc 1 → Process → Chunk → Embed → Upload
Time 2s:    Scrape Doc 2 → Process → Chunk → Embed → Upload (Doc 1 continues)
Time 4s:    Scrape Doc 3 → Process → Chunk → Embed → Upload (Docs 1-2 continue)
...all stages overlap for maximum efficiency
```

**Benefits:**
- ✅ 55-60% faster than sequential processing
- ✅ Better resource utilization (CPU + Network both active)
- ✅ Progressive results (see data as it arrives)
- ✅ Resilient to crashes (partial data is saved)

**Configuration:**
```bash
# In .env
PIPELINE_MODE=streaming              # Enable concurrent processing
SCRAPER_CONCURRENT_REQUESTS=2        # Simultaneous HTTP requests
EMBEDDING_BATCH_SIZE=32              # Vectors processed per batch
```

---

## 🚀 Performance

### Benchmarks (500 documents)

| Mode | Time | Notes |
|------|------|-------|
| **Batch** | ~450s | Sequential stages |
| **Streaming** | ~200s | Concurrent stages (55% faster) |

### Optimization Tips

1. **Use streaming mode** (default)
2. **Adjust batch sizes** based on RAM
3. **Use GPU** for embeddings if available
4. **Increase concurrent requests** for faster scraping
5. **Use incremental mode** for regular updates

---

## 📚 Additional Documentation

For detailed information on specific topics:

- **API Integration**: `docs/API_INTEGRATION.md` - Complete API reference with examples
- **N8N Workflows**: `docs/N8N_WORKFLOW.md` - Step-by-step N8N setup with templates
- **Deployment**: `docs/DEPLOYMENT.md` - Deployment options (VPS, Cloud Run, etc.)
- **Streaming Architecture**: `STREAMING_ARCHITECTURE.md` - Deep dive into concurrent processing

---

## 🔒 Security Considerations

**Production Checklist:**
- [ ] Use environment variables for secrets (never commit `.env`)
- [ ] Add API authentication if exposing to internet
- [ ] Use HTTPS for API endpoints
- [ ] Restrict firewall to known IPs
- [ ] Regularly update dependencies
- [ ] Monitor API access logs
- [ ] Use Pinecone namespace for data isolation

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- **Scrapy** - Web scraping framework
- **Sentence Transformers** - Embedding models  
- **Pinecone** - Vector database
- **FastAPI** - API framework
- **Playwright** - Browser automation

---

## 📞 Support

- **Issues**: Create an issue in the repository
- **API Docs**: http://localhost:8000/docs (when server running)
- **Documentation**: See `docs/` folder

---

## ✨ What's New

### Latest Updates

- ✅ **Pinecone Integration** - Fast vector storage in Pinecone
- ✅ **REST API Server** - Trigger pipeline via HTTP
- ✅ **N8N Automation** - Monthly scheduled runs
- ✅ **Streaming Pipeline** - 55% faster processing
- ✅ **Intelligent Sync** - Only upload changed content
- ✅ **No Docker Required** - Simple Python setup

---

## 🎯 Quick Reference

**Start Pipeline:**
```bash
python scripts/run_pipeline.py --mode full
```

**Start API Server:**
```bash
python scripts/run_api_server.py
```

**Trigger via API:**
```bash
curl -X POST http://localhost:8000/api/v1/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{"mode": "full"}'
```

**Check Status:**
```bash
curl http://localhost:8000/api/v1/status/{job_id}
```

**Run Tests:**
```bash
pytest tests/
```

---

**Ready to get started?**

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp env.example .env
# Edit .env with your Pinecone credentials

# 3. Run
python scripts/run_pipeline.py --mode full

# Or start API server for N8N
python scripts/run_api_server.py
```

**Questions?** Check the `docs/` folder for detailed guides or visit http://localhost:8000/docs when the API server is running.
