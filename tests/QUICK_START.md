# Quick Start: Testing with Real Data

## 🚀 In 3 Steps

### 1. Generate Real Test Data
```bash
python scripts/test_scraper_10pages.py
```
Creates: `tests/.test_data/raw/raw_data_YYYYMMDD_HHMMSS.json`

### 2. Run Tests
```bash
pytest tests/unit/ -v
```

### 3. Use in Your Tests

**For Core Functionality (use real data):**
```python
def test_my_function(self, single_scraped_item):
    """Test with real Amazon Seller Central document."""
    result = my_function(single_scraped_item["html_content"])
    assert result is not None
```

**For Edge Cases (use fake data):**
```python
def test_empty_input(self):
    """Test with empty input."""
    result = my_function("")
    assert result == ""
```

---

## 📋 Available Fixtures

| Fixture | Use When |
|---------|----------|
| `single_scraped_item` | Testing with 1 real document |
| `multiple_scraped_items` | Testing with 5 real documents |
| `all_scraped_items` | Testing with all ~10 documents |

---

## 📚 Full Documentation

- **Complete Guide**: `tests/TESTING_WITH_REAL_DATA.md`
- **Implementation Details**: `tests/REAL_DATA_IMPLEMENTATION_SUMMARY.md`

---

## ✅ What's Been Updated

**Unit Tests** (Real Data + Edge Cases):
- ✅ `test_preprocessor.py`
- ✅ `test_chunker.py`
- ✅ `test_embeddings.py`

**Integration Tests** (Real Data Only):
- ✅ `test_processing_pipeline.py`

---

That's it! You're ready to test with real data. 🎉

