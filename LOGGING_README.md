# Logging System Documentation

## 📋 Overview

This project implements a **two-tier logging system** designed for easy debugging and monitoring:

1. **High-Level (Console)**: Shows pipeline stage progress and success/failure status
2. **Deep-Level (Log Files)**: Detailed logs for each component for debugging

## 🎯 Quick Start

### Running the Pipeline

```bash
python scripts/run_pipeline.py --mode full
```

**Console Output Example:**
```
======================================================================
🚀 STARTING FULL PIPELINE
======================================================================

📡 STAGE 1/5: SCRAPING
----------------------------------------------------------------------
✅ Scraper completed successfully

⚙️  STAGE 2/5: PROCESSING
----------------------------------------------------------------------
✅ Processor completed: 150 documents

✂️  STAGE 3/5: CHUNKING
----------------------------------------------------------------------
✅ Chunker completed: 1250 chunks

🧠 STAGE 4/5: GENERATING EMBEDDINGS
----------------------------------------------------------------------
✅ Embeddings completed: 1250 vectors

💾 STAGE 5/5: LOADING TO NEO4J
----------------------------------------------------------------------
✅ Storage completed: 1250 chunks loaded

======================================================================
🎉 PIPELINE COMPLETED SUCCESSFULLY
======================================================================
```

### Viewing Detailed Logs

When something goes wrong, check the component-specific logs:

```bash
# View last 50 lines of scraper logs
python scripts/view_logs.py scraper

# View last 100 lines
python scripts/view_logs.py scraper --lines 100

# View only ERROR logs
python scripts/view_logs.py embeddings --level ERROR

# Search for specific text
python scripts/view_logs.py storage --search "CUDA"

# Follow logs in real-time (like tail -f)
python scripts/view_logs.py pipeline --follow
```

## 📁 Log File Structure

```
logs/
├── pipeline.log      # Complete logs from all components
├── scraper.log       # Scraping stage logs only
├── processor.log     # Processing stage logs only
├── chunker.log       # Chunking stage logs only
├── embeddings.log    # Embedding generation logs only
└── storage.log       # Neo4j storage logs only
```

### Log File Characteristics

- **Console**: INFO level only, clean overview
- **Component Files**: DEBUG level, detailed information
- **Master File** (`pipeline.log`): Everything from all components
- **Size**: Max 5-10MB per file with automatic rotation
- **Retention**: 3-5 backup files kept

## 🔍 Finding What Went Wrong

### Step 1: Check Console Output

The console shows which stage failed:

```
❌ Embeddings failed: CUDA out of memory
```

### Step 2: Check Component Log

```bash
# View detailed embeddings logs
python scripts/view_logs.py embeddings --level ERROR
```

**Output:**
```
2025-10-31 14:23:45 [ERROR] src.embeddings.generator:133 - ❌ Error processing batch 5: CUDA out of memory
```

### Step 3: View More Context

```bash
# See more lines around the error
python scripts/view_logs.py embeddings --lines 200
```

## 📊 Log Levels Explained

| Level | Console | Log Files | Usage |
|-------|---------|-----------|-------|
| **DEBUG** | ❌ No | ✅ Yes | Detailed step-by-step execution |
| **INFO** | ✅ Yes | ✅ Yes | Stage progress and completion |
| **WARNING** | ✅ Yes | ✅ Yes | Non-fatal issues |
| **ERROR** | ✅ Yes | ✅ Yes | Failures that stop execution |

## 🛠️ Component-Specific Logging

### Scraper (`logs/scraper.log`)

**What's Logged:**
- Spider initialization with Playwright
- Each page being parsed
- Content extraction results
- Change detection status
- Hash generation

**Example:**
```
2025-10-31 14:20:15 [INFO] src.scraper.spider:83 - 🕷️  Spider initialized with Playwright support
2025-10-31 14:20:16 [DEBUG] src.scraper.spider:126 - 📄 Parsing page: https://sellercentral.amazon.com/help/hub/reference/external/G2
2025-10-31 14:20:17 [INFO] src.scraper.spider:227 - Page processed: new | Hash: a3f5b9c1... | 5432 chars
```

### Processor (`logs/processor.log`)

**What's Logged:**
- HTML cleaning (boilerplate removal)
- HTML to Markdown conversion
- Content length at each step

**Example:**
```
2025-10-31 14:25:10 [DEBUG] src.processor.preprocessor:49 - Cleaning HTML (15234 chars)...
2025-10-31 14:25:10 [DEBUG] src.processor.preprocessor:59 - Removed 12 boilerplate elements
2025-10-31 14:25:11 [INFO] src.processor.preprocessor:118 - ✅ Processed HTML to Markdown: 8456 chars
```

### Chunker (`logs/chunker.log`)

**What's Logged:**
- Document chunking process
- Number of header-based chunks
- Final chunk count per document
- Chunk size and overlap settings

**Example:**
```
2025-10-31 14:26:05 [DEBUG] src.processor.chunker:31 - Initializing SemanticChunker (chunk_size=512, overlap=64)
2025-10-31 14:26:06 [DEBUG] src.processor.chunker:76 - Step 1: Splitting by markdown headers...
2025-10-31 14:26:06 [DEBUG] src.processor.chunker:78 - Created 8 header-based chunks
2025-10-31 14:26:07 [INFO] src.processor.chunker:152 - ✅ Created 12 chunks from Getting Started with Amazon...
```

### Embeddings (`logs/embeddings.log`)

**What's Logged:**
- Model loading with dimensions
- Batch processing progress
- Invalid embeddings detected
- Memory usage indicators

**Example:**
```
2025-10-31 14:27:00 [INFO] src.embeddings.generator:37 - Loading embedding model: all-MiniLM-L6-v2
2025-10-31 14:27:02 [INFO] src.embeddings.generator:42 - ✅ Model loaded successfully (dimension: 384)
2025-10-31 14:27:03 [DEBUG] src.embeddings.generator:128 - Processing batch 1/40 (32 chunks)...
2025-10-31 14:27:15 [INFO] src.embeddings.generator:153 - ✅ Successfully generated embeddings for 1250 chunks
```

### Storage (`logs/storage.log`)

**What's Logged:**
- Neo4j connection establishment
- Schema initialization
- Vector index creation
- Batch upload progress
- Transaction commits

**Example:**
```
2025-10-31 14:28:00 [INFO] src.storage.neo4j_client:41 - ✅ Connected to Neo4j at neo4j+s://xxxxx.databases.neo4j.io
2025-10-31 14:28:01 [INFO] src.storage.neo4j_client:68 - ✅ Database schema initialized
2025-10-31 14:28:02 [DEBUG] src.storage.neo4j_client:176 - Processing batch 1/13 (100 chunks)...
2025-10-31 14:28:05 [INFO] src.storage.neo4j_client:195 - ✓ Processed batch 1/13: 100 chunks
```

## 🚨 Common Issues and How to Debug

### Issue: Scraper Returns No Data

**Console:**
```
❌ Scraping failed: No raw data file found after scraping
```

**Debug:**
```bash
python scripts/view_logs.py scraper --search "Parsing page"
```

**Look for:**
- Are pages being parsed?
- Are there validation errors?
- Check robots.txt compliance

### Issue: Embeddings Fail with CUDA Error

**Console:**
```
❌ Embedding generation failed: CUDA out of memory
```

**Debug:**
```bash
python scripts/view_logs.py embeddings
```

**Look for:**
- Batch size too large
- GPU memory exhausted
- Fallback to CPU needed

**Solution:**
Edit `config/settings.py`:
```python
EMBEDDING_BATCH_SIZE = 16  # Reduce from 32
```

### Issue: Neo4j Connection Fails

**Console:**
```
❌ Storage failed: Failed to connect to Neo4j: Authentication error
```

**Debug:**
```bash
python scripts/view_logs.py storage --level ERROR
```

**Look for:**
- Connection URI correctness
- Authentication credentials
- Network connectivity

**Solution:**
Check `.env` file:
```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

## 📖 View Logs Tool Reference

### Basic Usage

```bash
python scripts/view_logs.py <component> [options]
```

### Components

- `scraper` - Scraping logs
- `processor` - Processing logs
- `chunker` - Chunking logs
- `embeddings` - Embedding generation logs
- `storage` - Neo4j storage logs
- `pipeline` - All components combined
- `all` - Same as pipeline

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--lines N` or `-n N` | Show last N lines (0 for all) | `--lines 100` |
| `--level LEVEL` | Filter by log level | `--level ERROR` |
| `--search TEXT` or `-s TEXT` | Search for text | `--search "CUDA"` |
| `--follow` or `-f` | Follow log in real-time | `--follow` |

### Examples

```bash
# Show last 50 lines (default)
python scripts/view_logs.py scraper

# Show all lines
python scripts/view_logs.py scraper --lines 0

# Show only errors
python scripts/view_logs.py embeddings --level ERROR

# Search for specific error
python scripts/view_logs.py storage --search "connection refused"

# Follow logs in real-time
python scripts/view_logs.py pipeline --follow

# Combine filters
python scripts/view_logs.py embeddings --level DEBUG --lines 200 --search "batch"
```

## 🔧 Advanced Configuration

### Changing Log Levels

Edit `config/logging.yaml`:

```yaml
loggers:
  src.scraper:
    level: DEBUG  # Change to INFO to reduce verbosity
```

### Changing File Sizes

```yaml
handlers:
  scraper_file:
    maxBytes: 10485760  # 10MB (increase for more history)
    backupCount: 5      # Keep 5 backup files
```

### Changing Console Output

```yaml
handlers:
  console:
    level: INFO  # Change to DEBUG to see more in console
```

## 🎨 Log Output Format

### Console Format
```
HH:MM:SS [LEVEL] Message
```

### File Format
```
YYYY-MM-DD HH:MM:SS [LEVEL] module.name:line_number - Message
```

### Example Comparison

**Console:**
```
14:25:10 [INFO] ✅ Processed HTML to Markdown: 8456 chars
```

**File:**
```
2025-10-31 14:25:10 [INFO] src.processor.preprocessor:118 - ✅ Processed HTML to Markdown: 8456 chars
```

## 💡 Best Practices

1. **Always check console first** - See which stage failed
2. **Use component-specific logs** - Focus on the failed component
3. **Start with ERROR level** - Find the critical issues first
4. **Expand to more lines** - Get context around errors
5. **Use search** - Find specific error messages
6. **Check master log** - See interactions between components

## 🆘 Getting Help

If you're stuck:

1. Check the console output for which stage failed
2. View the component-specific log file
3. Look for ERROR or WARNING messages
4. Search for the error message in this README
5. Check the main README.md for component-specific troubleshooting

## 📚 Additional Resources

- Main documentation: `README.md`
- Configuration guide: `config/settings.py`
- Scraper details: `SCRAPER_ANALYSIS.md`
- Implementation notes: `IMPLEMENTATION_SUCCESS.md`

