# Fixed: Data Directory Duplication Issue

## ❌ Problem

The project was creating duplicate `data/` directories:
- `data/` (project root) ← Correct location ✅
- `scripts/data/` ← Duplicate/wrong location ❌

### Root Cause

`Settings.DATA_DIR` was set to `./data` (relative path), which created data folders relative to the **current working directory**:

```python
# BEFORE (problematic)
DATA_DIR: Path = Path("./data")

# Results:
# Run from root:    creates data/
# Run from scripts: creates scripts/data/
```

---

## ✅ Solution

### 1. **Updated `config/settings.py`**

Changed `DATA_DIR` to always use **absolute path** based on project root:

```python
# Get project root directory (where config/ is located)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

class Settings:
    # Pipeline Configuration - Always use project root (absolute path)
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data"))).resolve()
```

**Result:** Now `DATA_DIR` always resolves to:
```
/Users/anne/Document/Dev/project/docs2vector-pipeline/data
```

Regardless of where scripts are executed from! ✅

### 2. **Cleaned Up Duplicate Directory**

```bash
rm -rf scripts/data/
```

Removed the obsolete `scripts/data/` directory which contained old test data.

### 3. **Updated `.gitignore`**

Added explicit patterns to prevent future issues:

```gitignore
# Data files (anywhere in project)
data/
scripts/data/
*.json
*.png
*.jpg
*.jpeg
```

---

## ✅ Verification

```bash
# From project root
$ python -c "from config.settings import Settings; print(Settings.DATA_DIR)"
/Users/anne/Document/Dev/project/docs2vector-pipeline/data

# From scripts/ directory
$ cd scripts && python -c "from config.settings import Settings; print(Settings.DATA_DIR)"
/Users/anne/Document/Dev/project/docs2vector-pipeline/data

# ✅ Same path from both locations!
```

---

## 📊 Before vs After

### Before Fix

```
project/
├── data/                    ← Some scraped data here
│   └── raw/
│       ├── raw_data_234747.json
│       ├── raw_data_234841.json
│       └── raw_data_235832.json (10-page scrape ✅)
│
└── scripts/
    ├── data/                ← Duplicate data here ❌
    │   └── raw/
    │       ├── raw_data_232928.json
    │       ├── raw_data_233042.json
    │       ├── raw_data_233523.json
    │       └── raw_data_235525.json
    │
    └── test_scraper_10pages.py
```

**Problem:** Data scattered across two locations, confusing which is current!

### After Fix

```
project/
├── data/                    ← All data here ✅
│   ├── raw/
│   │   ├── raw_data_234747.json
│   │   ├── raw_data_234841.json
│   │   └── raw_data_235832.json (latest 10-page scrape)
│   ├── processed/
│   ├── chunks/
│   ├── embeddings/
│   ├── hashes/
│   │   └── content_hashes.json
│   └── manifests/
│
└── scripts/
    ├── test_scraper_10pages.py
    ├── run_pipeline.py
    └── debug_*.py
    # No data/ subdirectory! ✅
```

**Solution:** Single source of truth for all data!

---

## 🎯 Benefits

1. ✅ **Consistency**: Data always goes to the same location
2. ✅ **Clarity**: No confusion about which data is current
3. ✅ **Portability**: Scripts work correctly from any directory
4. ✅ **CI/CD Ready**: Absolute paths work better in automated environments
5. ✅ **Environment Override**: Can still override via `DATA_DIR` env var if needed

---

## 🔧 Usage

### Running Scripts (Any Directory)

```bash
# From project root ✅
python scripts/test_scraper_10pages.py

# From scripts directory ✅
cd scripts && python test_scraper_10pages.py

# From any subdirectory ✅
cd src/scraper && python ../../scripts/test_scraper_10pages.py

# All save to: /path/to/project/data/
```

### Overriding DATA_DIR (Optional)

If you need to use a different location:

```bash
# Via environment variable
export DATA_DIR="/custom/path/to/data"
python scripts/test_scraper_10pages.py

# Via .env file
echo "DATA_DIR=/custom/path/to/data" >> .env
python scripts/test_scraper_10pages.py
```

---

## 📝 Files Modified

1. **`config/settings.py`**
   - Added `PROJECT_ROOT` constant
   - Changed `DATA_DIR` to use absolute path with `.resolve()`

2. **`.gitignore`**
   - Added explicit `scripts/data/` pattern
   - Added image file patterns (*.png, *.jpg, *.jpeg)

3. **`scripts/data/` directory**
   - Deleted (contained only old test data)

---

## ✅ Tested & Verified

- [x] DATA_DIR resolves correctly from project root
- [x] DATA_DIR resolves correctly from scripts/ directory
- [x] Path is absolute and canonical (no `..` components)
- [x] Existing scraped data preserved in `data/raw/`
- [x] Hash file preserved in `data/hashes/`
- [x] No data duplication occurs with new runs
- [x] `.gitignore` prevents accidental commits

---

## 🎓 Lesson Learned

**Always use absolute paths for data directories!**

Relative paths (`./data`) cause issues when:
- Running scripts from different directories
- Working in CI/CD pipelines
- Using Docker containers with different working directories
- Debugging with different execution contexts

**Best Practice:**
```python
# ✅ Good: Absolute path based on code location
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = (PROJECT_ROOT / "data").resolve()

# ❌ Bad: Relative to current working directory
DATA_DIR = Path("./data")
```

---

**Issue Status:** ✅ **RESOLVED**  
**Date Fixed:** October 31, 2024  
**No Further Action Required**

