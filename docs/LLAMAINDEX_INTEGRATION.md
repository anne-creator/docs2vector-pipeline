# LlamaIndex Cloud Integration Guide

## Overview

The pipeline now includes **intelligent synchronization** with LlamaIndex Cloud as an optional Stage 6. This integration automatically uploads your embedded documents to LlamaIndex Cloud for vector search and retrieval.

### Key Features ✨

- **🔄 Intelligent Sync**: Only uploads new and updated documents, skips unchanged ones
- **📊 Change Detection**: Uses content hashing to detect document changes
- **🚀 Batch Upload**: Efficient batch processing for large datasets
- **⚡ Optional**: Completely optional - enable only when needed
- **🛡️ Error Handling**: Robust retry logic and error reporting

## How It Works

### Pipeline Stages

When `USE_LLAMAINDEX=true`, the pipeline runs these stages:

1. **Scraping** → 2. **Processing** → 3. **Chunking** → 4. **Embeddings** → 5. **Neo4j** (optional) → 6. **LlamaIndex Cloud** ⭐

### Change Detection

The pipeline tracks document changes using content hashing:

- **New documents** (change_status="new") → Uploaded to LlamaIndex
- **Updated documents** (change_status="updated") → Old version deleted, new version uploaded
- **Unchanged documents** (change_status="unchanged") → Skipped (no upload needed)

This ensures your LlamaIndex Cloud storage stays perfectly in sync with your local data! 🎯

## Setup Instructions

### 1. Get LlamaIndex Cloud Credentials

1. Sign up at [https://cloud.llamaindex.ai/](https://cloud.llamaindex.ai/)
2. Create a new project (or use an existing one)
3. Create or select a pipeline/index
4. Get your API key from the dashboard

### 2. Configure Environment Variables

Edit your `.env` file and add:

```bash
# Enable LlamaIndex Cloud integration
USE_LLAMAINDEX=true

# Your LlamaIndex Cloud credentials
LLAMACLOUD_API_KEY=llx-your-api-key-here
LLAMACLOUD_INDEX_NAME=your-pipeline-name

# Optional (usually not needed)
LLAMACLOUD_PROJECT_NAME=Default
LLAMACLOUD_ORGANIZATION_ID=your-org-id
LLAMACLOUD_BASE_URL=https://api.cloud.llamaindex.ai
```

### 3. Test Connection

Run the test script to verify your setup:

```bash
python scripts/test_llamaindex_sync.py
```

Expected output:
```
🧪 TESTING LLAMAINDEX CLOUD CONNECTION
✅ Configuration loaded:
   Index Name: your-pipeline-name
   Project: Default
   Base URL: https://api.cloud.llamaindex.ai

✅ Successfully connected to LlamaIndex Cloud!

🔄 Starting sync to LlamaIndex Cloud...
✅ SYNC COMPLETED
   📝 New documents uploaded: X
   🔄 Documents updated: Y
   ⏭️  Unchanged documents skipped: Z
```

### 4. Run Full Pipeline

Now run your pipeline normally:

```bash
python scripts/run_pipeline.py
```

The pipeline will automatically:
1. Scrape → Process → Chunk → Generate Embeddings
2. Upload to LlamaIndex Cloud (Stage 6)
3. Show sync results in the logs

## Usage Examples

### Example 1: First Run (All New Documents)

```bash
# First time running with LlamaIndex enabled
python scripts/run_pipeline.py
```

Output:
```
☁️  STAGE 6/6: UPLOADING TO LLAMAINDEX CLOUD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Starting document sync to LlamaCloud index 'your-index'...
   Total local documents: 1500
   New documents: 1500
   Updated documents: 0
   Unchanged documents: 0 (will be skipped)

📤 Uploading 1500 new documents...
✅ Successfully uploaded 100 documents
✅ Successfully uploaded 100 documents
... (continues in batches of 100)

✅ SYNC COMPLETED
   📝 New documents uploaded: 1500
   🔄 Documents updated: 0
   ⏭️  Unchanged documents skipped: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Example 2: Second Run (Only Changed Documents)

```bash
# Run again after website content has changed
python scripts/run_pipeline.py
```

Output:
```
☁️  STAGE 6/6: UPLOADING TO LLAMAINDEX CLOUD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Starting document sync to LlamaCloud index 'your-index'...
   Total local documents: 1550
   New documents: 60 (new pages)
   Updated documents: 15 (content changed)
   Unchanged documents: 1475 (will be skipped)

📤 Uploading 60 new documents...
✅ Successfully uploaded 60 documents

🔄 Updating 15 documents...
✅ Successfully deleted 15 documents
✅ Successfully uploaded 15 documents

✅ SYNC COMPLETED
   📝 New documents uploaded: 60
   🔄 Documents updated: 15
   ⏭️  Unchanged documents skipped: 1475
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Result**: Only 75 documents uploaded (60 new + 15 updated), saving time and API costs! 💰

## Sync Behavior Details

### How Sync Works

The `sync_documents()` method intelligently handles all scenarios:

| Change Status | Action | Description |
|--------------|--------|-------------|
| `new` | ✅ Upload | First time seeing this document - upload to LlamaIndex |
| `updated` | 🔄 Replace | Content changed - delete old version, upload new version |
| `unchanged` | ⏭️ Skip | Content identical - skip upload (already in LlamaIndex) |

### Metadata Preservation

Each document uploaded includes rich metadata:

```python
{
    "text": "document content...",
    "metadata": {
        "source_url": "https://...",
        "document_title": "Page Title",
        "chunk_id": "unique-chunk-identifier",
        "doc_id": "document-url",
        "change_status": "new|updated|unchanged",
        "scraped_at": "2025-11-05T15:26:26.096668",
        "article_id": "200573210",
        "chunk_index": 0,
        "chunk_title": "Section Title"
        # ... and more
    },
    "id": "unique-chunk-identifier",
    "embedding": [0.123, 0.456, ...] (384 or 768 dimensions)
}
```

This metadata enables powerful filtering and search in LlamaIndex! 🔍

## Disabling LlamaIndex

To disable LlamaIndex and skip Stage 6:

```bash
# In .env file
USE_LLAMAINDEX=false
```

Or simply leave it unset (default is `false`).

The pipeline will skip the LlamaIndex upload stage and continue to work normally.

## Troubleshooting

### Issue: "Failed to connect to LlamaCloud"

**Solution**: Check your credentials:
```bash
# Run test script for diagnostics
python scripts/test_llamaindex_sync.py
```

Verify in `.env`:
- `LLAMACLOUD_API_KEY` is correct (starts with `llx-`)
- `LLAMACLOUD_INDEX_NAME` matches your pipeline name
- No extra spaces or quotes

### Issue: "Index name is required"

**Solution**: Set your index/pipeline name:
```bash
LLAMACLOUD_INDEX_NAME=your-pipeline-name
```

### Issue: "API rate limit exceeded"

**Solution**: The pipeline uses batch uploads (100 documents per batch) with retry logic. If you hit rate limits:
1. Reduce batch size in the code (default: 100)
2. Wait a few minutes and retry
3. Check your LlamaIndex Cloud plan limits

### Issue: Documents not appearing in LlamaIndex Cloud

**Checklist**:
1. ✅ Check logs for "✅ SYNC COMPLETED" message
2. ✅ Verify sync results show uploaded documents: `📝 New documents uploaded: X`
3. ✅ Wait 1-2 minutes for indexing (LlamaIndex needs time to process)
4. ✅ Refresh your LlamaIndex Cloud dashboard
5. ✅ Check the correct project/pipeline is selected

## API Reference

### PipelineOrchestrator

#### `upload_to_llamaindex(chunks_with_embeddings)`

Uploads chunks with embeddings to LlamaIndex Cloud.

```python
from src.pipeline.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()
result = orchestrator.upload_to_llamaindex(chunks_with_embeddings)

print(f"Uploaded: {result['new_count']}")
print(f"Updated: {result['updated_count']}")
```

### LlamaIndexClient

#### `sync_documents(documents, batch_size=100)`

Intelligently syncs documents to LlamaIndex Cloud.

```python
from src.integrations.llamaindex.client import LlamaIndexClient

client = LlamaIndexClient()
client.connect()

result = client.sync_documents(documents, batch_size=100)
# Returns: {"new_count": X, "updated_count": Y, "unchanged_count": Z, ...}

client.disconnect()
```

#### `upload_documents(documents)`

Directly uploads documents (no change detection).

```python
client.upload_documents(documents)
```

#### `delete_documents(document_ids=None, metadata_filter=None)`

Deletes documents by IDs or metadata filter.

```python
# Delete by IDs
client.delete_documents(document_ids=["id1", "id2", "id3"])

# Delete by metadata filter
client.delete_documents(metadata_filter={"article_id": "200573210"})
```

## Performance Tips

### 1. Batch Size Tuning

Default batch size is 100. Adjust based on your needs:

```python
# In your code
result = client.sync_documents(documents, batch_size=50)  # Smaller batches
```

### 2. Concurrent Processing

Use streaming mode for faster processing:

```bash
# In .env
PIPELINE_MODE=streaming
```

This processes documents as they're scraped, reducing total time.

### 3. Incremental Updates

Run the pipeline regularly (daily/weekly) to:
- ✅ Only sync changed documents
- ✅ Save API calls and costs
- ✅ Keep LlamaIndex Cloud up-to-date automatically

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Stage 1: Scraping       →  data/raw/                       │
│  Stage 2: Processing     →  data/processed/                 │
│  Stage 3: Chunking       →  data/chunks/                    │
│  Stage 4: Embeddings     →  data/embeddings/                │
│  Stage 5: Neo4j (opt)    →  Neo4j Graph Database            │
│  Stage 6: LlamaIndex ⭐  →  LlamaIndex Cloud                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                  ┌───────────────────────┐
                  │   LlamaIndex Cloud    │
                  │   Vector Storage      │
                  ├───────────────────────┤
                  │  • Vector Search      │
                  │  • Semantic Retrieval │
                  │  • RAG Applications   │
                  └───────────────────────┘
```

## Next Steps

After setting up LlamaIndex integration:

1. **Query Your Data**: Use LlamaIndex Cloud dashboard to query your documents
2. **Build RAG Apps**: Integrate LlamaIndex into your applications
3. **Monitor Syncs**: Check logs for sync statistics and errors
4. **Automate**: Set up scheduled pipeline runs (cron, GitHub Actions, etc.)

## Support

For issues or questions:

- **Pipeline Issues**: Check logs in `logs/pipeline.log`
- **LlamaIndex Docs**: [https://docs.llamaindex.ai/](https://docs.llamaindex.ai/)
- **API Reference**: [https://docs.cloud.llamaindex.ai/](https://docs.cloud.llamaindex.ai/)

---

**Happy syncing! 🚀**


