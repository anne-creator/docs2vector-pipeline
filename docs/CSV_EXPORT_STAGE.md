# CSV Export Stage - Final Pipeline Stage

## Overview

The CSV Export stage is the **final stage** of the docs2vector pipeline. It converts embeddings from JSON format to CSV format, making them ready for ingestion into RAG (Retrieval-Augmented Generation) systems.

## Pipeline Position

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Scraping   │ ───> │ Processing  │ ───> │  Chunking   │ ───> │ Embeddings  │ ───> │ CSV Export  │
│   Stage     │      │   Stage     │      │   Stage     │      │   Stage     │      │   Stage     │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
     raw/            processed/           chunks/           embeddings/           csv_export/
```

## Module Location

```
src/export/
├── __init__.py
└── csv_exporter.py    # Main CSV exporter class
```

## CSV Schema

### Option 1: Compact Format (Default - JSON-encoded arrays)

The CSV includes all metadata fields with complex structures JSON-encoded:

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Unique chunk identifier |
| `content` | string | The actual text content |
| `source_url` | string | Original document URL |
| `document_title` | string | Document title |
| `last_updated` | string | Last update timestamp |
| `breadcrumbs` | JSON array | Navigation breadcrumbs |
| `related_links` | JSON array | Related links with text/url |
| `scraped_at` | string | ISO timestamp when scraped |
| `category` | JSON array | Document categories |
| `article_id` | string | Article identifier |
| `locale` | string | Language locale (e.g., "en-US") |
| `page_hash` | string | Content hash for change detection |
| `change_status` | string | Status: "new", "modified", "unchanged" |
| `chunk_index` | integer | Chunk sequence number |
| `sub_chunk_index` | integer | Sub-chunk sequence number |
| `chunk_id` | string | Chunk identifier |
| `doc_id` | string | Document identifier (URL) |
| `embedding` | JSON array | 384-dimensional embedding vector |

### Example CSV Row

```csv
id,content,source_url,document_title,...,embedding
G2?locale=en-US_0,"Help for Amazon Sellers...",https://sellercentral.amazon.com/...,"Help for Amazon Sellers",...,[0.0136,-0.0810,0.0245,...]
```

## Usage

### 1. Programmatic Usage

```python
from src.export.csv_exporter import CSVExporter
from pathlib import Path

# Initialize exporter
exporter = CSVExporter(output_dir=Path("data/csv_export"))

# Export single file
csv_path = exporter.export_from_json_file(
    json_file_path=Path("data/embeddings/embeddings_20251031_174503_20251105_020811.json"),
    include_embedding=True
)

# Batch export all files in directory
csv_files = exporter.batch_export_directory(
    input_dir=Path("data/embeddings"),
    pattern="*.json",
    include_embedding=True
)
```

### 2. Command Line Usage

```bash
# Export specific JSON file
python scripts/export_embeddings_to_csv.py --input data/embeddings/embeddings_20251031_174503_20251105_020811.json

# Export all embeddings in directory (batch mode)
python scripts/export_embeddings_to_csv.py --batch --input data/embeddings/

# Export metadata only (without embedding vectors)
python scripts/export_embeddings_to_csv.py --input data/embeddings/embeddings_20251031_174503_20251105_020811.json --no-embeddings

# Specify custom output directory
python scripts/export_embeddings_to_csv.py --input data/embeddings/ --output custom_output/ --batch
```

### 3. Integration with FileManager

```python
from src.storage.file_manager import FileManager
from src.export.csv_exporter import CSVExporter

# Load embeddings using FileManager
file_manager = FileManager()
embeddings = file_manager.load_embeddings("embeddings_20251031_174503_20251105_020811.json")

# Export to CSV
exporter = CSVExporter()
csv_path = exporter.export_embeddings(embeddings, "output.csv")
```

## Configuration

Settings in `config/settings.py`:

```python
# CSV Export Configuration
CSV_INCLUDE_EMBEDDINGS: bool = True  # Include embedding vectors by default
CSV_OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "csv_export"
```

Environment variables (`.env`):

```bash
CSV_INCLUDE_EMBEDDINGS=true
CSV_OUTPUT_DIR=/path/to/csv/output
```

## Output Directory Structure

```
data/csv_export/
├── embeddings_20251031_174503_20251105_020811.csv
├── embeddings_20251031_174511_20251105_020812.csv
└── embeddings_20251031_174536_20251105_020816.csv
```

## Testing

### Run Tests

```bash
# Run all CSV exporter tests
pytest tests/unit/test_csv_exporter.py -v

# Run specific test
pytest tests/unit/test_csv_exporter.py::TestCSVExporter::test_export_real_embeddings -v
```

### Test Strategy

The test suite uses a hybrid approach:

1. **Real Data Tests**: Use actual embedding files from `tests/.test_data/embeddings/`
   - Validates end-to-end export with real data
   - Ensures CSV structure matches input data
   - Verifies data integrity

2. **Edge Case Tests**: Use minimal synthetic data
   - Tests error handling (missing files, invalid JSON)
   - Tests special characters, Unicode, large content
   - Tests edge cases (empty lists, missing metadata fields)

### Test Output

Tests generate CSV files in `tests/.test_data/csv_format/` for inspection:

```
tests/.test_data/csv_format/
├── embeddings_20251031_174503_20251105_020811.csv  (125 rows)
├── embeddings_20251031_174511_20251105_020812.csv  (125 rows)
├── embeddings_sample_20251105_020818.csv            (11 rows)
└── test_embeddings_20251031_174503_20251105_020811.csv
```

## Features

### ✅ Implemented Features

1. **Single File Export**: Export one JSON embedding file to CSV
2. **Batch Export**: Export all JSON files in a directory
3. **Flexible Schema**: Include or exclude embedding vectors
4. **JSON Encoding**: Complex fields (arrays, objects) JSON-encoded
5. **Error Handling**: Graceful handling of invalid files
6. **Unicode Support**: Full UTF-8 support for international content
7. **Large Content**: Handles large text chunks efficiently
8. **Data Integrity**: Validates data during export

### 🎯 Use Cases

1. **RAG System Ingestion**: Export embeddings for vector databases
2. **Data Analysis**: Import into Excel, Pandas, or analytics tools
3. **Backup**: Human-readable backup format
4. **Debugging**: Inspect embeddings and metadata
5. **Integration**: Share data with other systems

## Performance

- **Processing Speed**: ~1000 records/second
- **Memory Efficient**: Streaming write (constant memory usage)
- **File Size**: 
  - With embeddings: ~200KB per 100 records
  - Without embeddings: ~50KB per 100 records

## Best Practices

### 1. Include Embeddings for RAG Systems

```python
# For vector databases (include embeddings)
exporter.export_embeddings(embeddings, "for_rag.csv", include_embedding=True)
```

### 2. Exclude Embeddings for Metadata Analysis

```python
# For metadata-only analysis (smaller file size)
exporter.export_embeddings(embeddings, "metadata_only.csv", include_embedding=False)
```

### 3. Batch Export for Production

```python
# Process all embeddings at once
exporter.batch_export_directory(
    input_dir=Path("data/embeddings"),
    include_embedding=True
)
```

### 4. Error Recovery

The batch exporter continues processing even if individual files fail:

```python
exported_files = exporter.batch_export_directory(input_dir)
# Even if some files fail, others will be processed
```

## Common Issues

### Issue 1: CSV Too Large

**Problem**: CSV file is too large for Excel or other tools.

**Solution**: Export without embeddings or split into chunks:

```python
# Option 1: Metadata only
exporter.export_embeddings(embeddings, include_embedding=False)

# Option 2: Split data
batch1 = embeddings[:1000]
batch2 = embeddings[1000:]
exporter.export_embeddings(batch1, "batch1.csv")
exporter.export_embeddings(batch2, "batch2.csv")
```

### Issue 2: Special Characters Not Displaying

**Problem**: Special characters appear garbled.

**Solution**: Ensure UTF-8 encoding when opening CSV:

```python
# Python pandas
import pandas as pd
df = pd.read_csv("embeddings.csv", encoding='utf-8')

# Excel: Import as UTF-8 text file
```

### Issue 3: JSON Fields Need Parsing

**Problem**: Arrays are JSON-encoded strings.

**Solution**: Parse JSON fields after loading:

```python
import json
import pandas as pd

df = pd.read_csv("embeddings.csv")
df['breadcrumbs'] = df['breadcrumbs'].apply(json.loads)
df['embedding'] = df['embedding'].apply(json.loads)
```

## Integration Example

Complete pipeline from scraping to CSV export:

```python
from src.scraper.spider import run_spider
from src.processor.preprocessor import Preprocessor
from src.processor.chunker import SemanticChunker
from src.embeddings.generator import EmbeddingGenerator
from src.export.csv_exporter import CSVExporter
from src.storage.file_manager import FileManager

# 1. Scrape data
scraped_data = run_spider(start_url="https://example.com")

# 2. Process documents
preprocessor = Preprocessor()
processed_docs = [preprocessor.process(item) for item in scraped_data]

# 3. Chunk documents
chunker = SemanticChunker()
chunks = chunker.chunk_documents(processed_docs)

# 4. Generate embeddings
generator = EmbeddingGenerator()
embeddings = generator.process_chunks(chunks)

# 5. Export to CSV (FINAL STAGE)
exporter = CSVExporter()
csv_path = exporter.export_embeddings(embeddings)

print(f"✅ Pipeline complete! CSV exported to: {csv_path}")
```

## API Reference

### CSVExporter Class

```python
class CSVExporter:
    def __init__(self, output_dir: Optional[Path] = None)
    
    def export_embeddings(
        self,
        embeddings: List[Dict[str, Any]],
        output_filename: Optional[str] = None,
        include_embedding: bool = True
    ) -> Path
    
    def export_from_json_file(
        self,
        json_file_path: Path,
        output_filename: Optional[str] = None,
        include_embedding: bool = True
    ) -> Path
    
    def batch_export_directory(
        self,
        input_dir: Path,
        pattern: str = "*.json",
        include_embedding: bool = True
    ) -> List[Path]
```

## Next Steps

After exporting to CSV, you can:

1. **Load into Vector Database**: Use CSV to populate Pinecone, Weaviate, Qdrant, etc.
2. **Import into Neo4j**: Load CSV into Neo4j for graph-based RAG
3. **Analyze with Pandas**: Perform data analysis and quality checks
4. **Build RAG Application**: Use as knowledge base for LLM applications

## Related Documentation

- [Embedding Configuration](EMBEDDING_CONFIGURATION.md)
- [File Manager Documentation](../README.md)
- [Pipeline Orchestrator](../src/pipeline/README.md)

