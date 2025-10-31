# Testing with Real Scraped Data

This guide explains how the test suite uses real scraped data alongside fake data for comprehensive testing.

## Testing Strategy

**Unit Tests**: Use BOTH real data (core functionality) AND fake data (edge cases)
- Core functionality tests validate with realistic Amazon Seller Central content
- Edge case tests use minimal fake data for boundary conditions and error handling

**Integration Tests**: Use ONLY real data
- Validates the complete pipeline with production-like content
- Tests: preprocessing → chunking → embeddings → storage

## Quick Start

### 1. Generate Real Test Data

First, run the scraper to generate real test data:

```bash
python scripts/test_scraper_10pages.py
```

This creates data in `tests/.test_data/raw/raw_data_YYYYMMDD_HHMMSS.json`

### 2. Use Fixtures in Your Tests

The following fixtures are now available in all tests via `conftest.py`:

#### Available Fixtures

| Fixture | Description | Returns |
|---------|-------------|---------|
| `real_scraped_data` | All scraped data from latest test run | `list[dict]` |
| `single_scraped_item` | One real scraped document | `dict` |
| `multiple_scraped_items` | 5 real documents (or all if < 5) | `list[dict]` |
| `all_scraped_items` | All scraped documents (~10 pages) | `list[dict]` |

#### Scraped Item Structure

Each scraped item contains:
```python
{
    "url": "https://sellercentral.amazon.com/help/...",
    "title": "Document Title",
    "html_content": "<article>...</article>",
    "text_content": "Plain text version...",
    "last_updated": "2024-01-01",
    "breadcrumbs": ["Home", "Help", "..."],
    "related_links": [...],
    "metadata": {
        "locale": "en-US",
        "article_id": "G...",
        "page_hash": "...",
        "change_status": "new|updated|unchanged"
    },
    "scraped_at": "2024-01-01T12:00:00"
}
```

## Test File Structure

Each unit test file follows this pattern:

```python
"""Unit tests for [component].

Testing Strategy:
- Core functionality tests use REAL scraped data from tests/.test_data/
- Edge case tests use FAKE/minimal data for boundary conditions
- Run scripts/test_scraper_10pages.py first to generate real test data
"""

class TestComponent:
    """Test Component class with real data and edge cases."""
    
    def setup_method(self):
        self.component = Component()
    
    # ========================================================================
    # CORE FUNCTIONALITY TESTS - Using Real Scraped Data
    # ========================================================================
    # These tests validate main workflows with realistic content
    
    def test_with_real_data(self, single_scraped_item):
        """Test with real Amazon Seller Central document."""
        # Your test using real data
        pass
    
    # ========================================================================
    # EDGE CASE TESTS - Using Fake/Minimal Data
    # ========================================================================
    # These tests validate error handling with controlled inputs
    
    def test_edge_case(self):
        """Test with minimal fake data."""
        # Your test using fake data
        pass
```

## Usage Examples

### Example 1: Unit Test with Real Data

```python
def test_process_real_document(self, single_scraped_item):
    """Test processing a real Amazon Seller Central document."""
    preprocessor = Preprocessor()
    
    result = preprocessor.process(
        single_scraped_item["html_content"],
        single_scraped_item.get("text_content")
    )
    
    # Real documents should produce substantial output
    assert len(result) > 100
    assert isinstance(result, str)
```

### Example 2: Unit Test with Fake Data for Edge Cases

```python
def test_clean_html_empty_input(self):
    """Test HTML cleaning with empty input."""
    preprocessor = Preprocessor()
    
    # Test edge cases with controlled minimal data
    assert preprocessor.clean_html("") == ""
    assert preprocessor.clean_html(None) == ""
```

### Example 3: Integration Test (Real Data Only)

```python
@pytest.mark.integration
def test_full_pipeline_single_document(self, single_scraped_item, tmp_path):
    """Test complete pipeline: preprocess -> chunk -> embed."""
    preprocessor = Preprocessor()
    chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
    generator = EmbeddingGenerator()
    
    # Preprocess
    markdown = preprocessor.process(
        single_scraped_item["html_content"],
        single_scraped_item.get("text_content")
    )
    
    # Chunk
    processed_doc = {
        "url": single_scraped_item["url"],
        "title": single_scraped_item["title"],
        "markdown_content": markdown,
        "metadata": single_scraped_item.get("metadata", {})
    }
    chunks = chunker.chunk_document(processed_doc)
    
    # Generate embeddings
    chunks_with_embeddings = generator.process_chunks(chunks)
    
    assert len(chunks_with_embeddings) > 0
    assert all("embedding" in chunk for chunk in chunks_with_embeddings)
```

## Updated Test Files

The following test files have been updated to use real data:

### Unit Tests (Real Data + Edge Cases)
- `tests/unit/test_preprocessor.py` - HTML cleaning, markdown conversion
- `tests/unit/test_chunker.py` - Document chunking, metadata preservation
- `tests/unit/test_embeddings.py` - Embedding generation with real chunks

### Integration Tests (Real Data Only)
- `tests/integration/test_processing_pipeline.py` - Full pipeline end-to-end
- `tests/integration/test_scraper_integration.py` - Scraper runs (generates real data)

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Only Unit Tests
```bash
pytest tests/unit/
```

### Run Only Integration Tests
```bash
pytest tests/integration/ -m integration
```

### Run Specific Test File
```bash
pytest tests/unit/test_preprocessor.py
```

### Run Specific Test
```bash
pytest tests/unit/test_with_real_data_example.py::TestPreprocessorWithRealData::test_process_single_real_document
```

### Verbose Output
```bash
pytest -v tests/unit/test_with_real_data_example.py
```

### Show Print Statements
```bash
pytest -s tests/unit/test_with_real_data_example.py
```

## How It Works

1. **Session-scoped fixture**: `real_scraped_data` loads the JSON file once per test session
2. **Automatic skip**: Tests automatically skip if no real data is found
3. **Most recent data**: Always uses the latest `raw_data_*.json` file
4. **Efficient**: Data is loaded once and shared across all tests

## Benefits of Real Data Testing

✅ **Realistic**: Tests use actual Amazon Seller Central content
✅ **Catches edge cases**: Real HTML often has quirks that fake data doesn't
✅ **Validation**: Confirms your pipeline works with production-like data
✅ **Confidence**: Integration tests with real data give higher confidence

## Combining Fake and Real Data

You can still use the existing fake data fixtures:
- `sample_html_content` - Simple HTML for unit tests
- `sample_markdown_content` - Simple Markdown for unit tests

Use fake data for:
- Fast unit tests
- Testing specific edge cases
- Tests that don't need real complexity

Use real data for:
- Integration tests
- End-to-end pipeline tests
- Validating with production-like content

## Troubleshooting

### "No real scraped data found" Error

**Solution**: Run the scraper first:
```bash
python scripts/test_scraper_10pages.py
```

### Tests Skip with Real Data

Check that the data directory exists:
```bash
ls -la tests/.test_data/raw/
```

### Using Different Data

To use different scraped data, just run the scraper again. The fixtures automatically use the most recent file.

## See Also

- `tests/conftest.py` - Fixture definitions
- `tests/unit/test_with_real_data_example.py` - Example tests
- `scripts/test_scraper_10pages.py` - Data generation script

