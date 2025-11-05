# Chunk Title Enhancement

## Overview

Enhanced the semantic chunking system to automatically generate descriptive titles for each chunk based on the markdown header hierarchy. This improvement significantly enhances RAG (Retrieval Augmented Generation) performance by providing better context for chunk retrieval.

## Problem Solved

**Before:** All chunks from the same document had the same `document_title`:
```json
{
  "content": "Bank account details...",
  "metadata": {
    "document_title": "Help for Amazon Sellers"  // Same for all 44 chunks
  }
}
```

**After:** Each chunk now has a unique, descriptive `chunk_title`:
```json
{
  "content": "Bank account details...",
  "metadata": {
    "document_title": "Help for Amazon Sellers",  // Parent document
    "chunk_title": "Payment Information > Bank Account Details"  // Specific to this chunk
  }
}
```

## Implementation

### Code Changes

1. **Added `_extract_chunk_title()` method** (`src/processor/chunker.py`):
   - Extracts headers from markdown structure
   - Builds hierarchical titles (e.g., "Parent > Child")
   - Falls back to document title when no headers exist

2. **Updated `chunk_document()` method**:
   - Calls `_extract_chunk_title()` for each chunk
   - Adds `chunk_title` to chunk metadata
   - Appends part numbers for sub-chunks (e.g., "Section (Part 1)")

3. **Added comprehensive tests** (`tests/unit/test_chunker.py`):
   - Test single header extraction
   - Test nested header hierarchy
   - Test deep hierarchy (h1 → h2 → h3)
   - Test fallback to document title
   - Test sub-chunk part numbering
   - Test with real scraped data

### Files Modified

- `src/processor/chunker.py` - Core chunking logic
- `tests/unit/test_chunker.py` - Added 6 new test cases
- `README.md` - Documented the new feature
- `scripts/demo_chunk_titles.py` - Created demonstration script

## Features

### 1. Header Hierarchy Extraction

The system extracts markdown headers at all levels (h1, h2, h3, h4):

```markdown
# Account Settings              → "Account Settings"
## Payment Information           → "Account Settings > Payment Information"
### Bank Account Details         → "Payment Information > Bank Account Details"
```

### 2. Contextual Titles

For nested sections, combines the last two header levels to provide context:

```
h1: Account Settings
h2: Payment Information
h3: Bank Details
→ Chunk Title: "Payment Information > Bank Details"
```

### 3. Sub-Chunk Numbering

When large sections are split into multiple chunks, adds part numbers:

```
Original: "Security Settings"
Split into 3 chunks:
  - "Security Settings (Part 1)"
  - "Security Settings (Part 2)"
  - "Security Settings (Part 3)"
```

### 4. Intelligent Fallback

If no headers are found, uses the document title:

```
Content with no headers → Chunk Title: "Help for Amazon Sellers"
```

## Benefits for RAG

### Improved Retrieval Accuracy

**Query:** "How do I update my bank account?"

**Before (document_title only):**
- Less specific matching
- Harder to rank relevant chunks

**After (with chunk_title):**
- Can match against "Payment Information > Bank Account Details"
- More precise retrieval
- Better ranking

### Better Context for LLM

When chunks are retrieved, the LLM receives:
- `document_title`: Overall document context
- `chunk_title`: Specific section context
- `content`: Actual information

This helps the LLM provide more accurate, contextual responses.

### Enhanced Semantic Search

Vector embeddings can now include chunk titles, improving semantic search:

```python
# Embedding includes both title and content
embedding_text = f"{chunk_title}: {content}"
```

## Testing Results

All 15 tests pass, including 6 new chunk_title specific tests:

```
✅ test_chunk_title_single_header
✅ test_chunk_title_nested_headers
✅ test_chunk_title_deep_hierarchy
✅ test_chunk_title_fallback_to_document_title
✅ test_chunk_title_with_sub_chunks
✅ test_chunk_title_present_in_all_chunks_real_data
```

## Usage Example

### Running the Demo

```bash
python scripts/demo_chunk_titles.py
```

### Sample Output

```
Chunk 1:
  📌 Chunk Title: Amazon Seller Account Settings
  📝 Content Preview: Account settings allow you to manage...

Chunk 2:
  📌 Chunk Title: Amazon Seller Account Settings > Payment Information
  📝 Content Preview: You can update your payment methods...

Chunk 3:
  📌 Chunk Title: Payment Information > Bank Account Details
  📝 Content Preview: Enter your routing number and account...
```

### Programmatic Usage

```python
from src.processor.chunker import SemanticChunker

chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)

document = {
    "url": "https://example.com/help",
    "title": "Help Documentation",
    "markdown_content": "# Section\n\n## Subsection\n\nContent here.",
    "metadata": {"source_url": "https://example.com/help"}
}

chunks = chunker.chunk_document(document)

for chunk in chunks:
    print(f"Title: {chunk['metadata']['chunk_title']}")
    print(f"Content: {chunk['content']}")
```

## Future Enhancements

### Option 1: LLM-Generated Titles (Advanced)

For chunks without clear headers or for even better quality:

```python
# Use LLM to generate descriptive titles
title = llm.generate(f"Create a 10-word title for: {content}")
```

**Pros:**
- More descriptive and contextual
- Works for any content structure
- Can capture semantic meaning

**Cons:**
- Costs money (API calls)
- Slower processing
- Requires API key management

### Option 2: Enhanced Title Templates

Customize title format for different document types:

```python
title_templates = {
    "help": "{h1} - {h2}",
    "tutorial": "How to: {h2}",
    "reference": "{h1} Reference: {h2}"
}
```

### Option 3: Title Quality Scoring

Evaluate and improve low-quality titles:

```python
if is_low_quality(chunk_title):
    chunk_title = improve_title(chunk_title, content)
```

## Backward Compatibility

✅ **Fully backward compatible**
- Existing code continues to work
- New `chunk_title` field is additive
- Old chunks without `chunk_title` still function
- Can be reprocessed to add titles

## Performance Impact

- **Minimal overhead**: Header extraction is fast (< 1ms per chunk)
- **No external dependencies**: Uses existing markdown structure
- **No API calls**: All processing is local

## Configuration

No additional configuration required. The feature works automatically with default settings.

To customize chunk size and overlap:

```python
chunker = SemanticChunker(
    chunk_size=500,    # Max chunk size
    chunk_overlap=50   # Overlap between chunks
)
```

## Migration Guide

### For Existing Data

To add chunk titles to existing chunks:

```bash
# Reprocess existing documents
python scripts/run_pipeline.py --reprocess
```

### For New Integrations

Simply use the chunker as before - `chunk_title` will automatically be included:

```python
chunks = chunker.chunk_document(document)
# Each chunk now has metadata.chunk_title
```

## Conclusion

The chunk title enhancement provides immediate value for RAG systems by:
- ✅ Providing descriptive, contextual titles for every chunk
- ✅ Improving retrieval accuracy and ranking
- ✅ Enabling better semantic search
- ✅ Maintaining full backward compatibility
- ✅ Requiring zero configuration

This is a foundational improvement that makes the pipeline more effective for production RAG applications.

---

**Date:** November 3, 2025
**Author:** AI Assistant
**Version:** 1.0

