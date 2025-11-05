# Embedding Configuration Guide

This guide explains how to configure embedding generation for the docs2vector pipeline.

## Overview

The pipeline supports three embedding providers:
1. **Sentence Transformers** - Local models (no API key needed)
2. **Ollama** - Local Ollama server (no API key needed)
3. **OpenAI-Compatible APIs** - Cloud embedding services

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template (if available)
cp .env.example .env
```

### Configuration

Edit `.env` file and set `EMBEDDING_PROVIDER`:

```bash
EMBEDDING_PROVIDER=sentence-transformers  # or ollama, or openai
```

## Provider Options

### 1. Sentence Transformers (Local)

**Best for**: Development, testing, offline usage, privacy-sensitive data

**Pros**:
- No API costs
- Works offline
- Fast for small/medium datasets
- Privacy-friendly (all data stays local)

**Cons**:
- Requires local GPU/CPU resources
- Limited to available models

**Configuration**:
```bash
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5  # 384 dimensions, high quality
# or
EMBEDDING_MODEL=all-MiniLM-L6-v2   # 384 dimensions, fast
# or
EMBEDDING_MODEL=all-mpnet-base-v2  # 768 dimensions, higher quality
EMBEDDING_BATCH_SIZE=32
```

**Available Models**:
| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `BAAI/bge-small-en-v1.5` | 384 | ⚡⚡⚡ | ⭐⭐⭐ | **Recommended default** - Best balance |
| `all-MiniLM-L6-v2` | 384 | ⚡⚡⚡ | ⭐⭐ | Fast prototyping, large datasets |
| `all-mpnet-base-v2` | 768 | ⚡⚡ | ⭐⭐⭐ | Production, better accuracy |

### 2. Ollama (Local Server)

**Best for**: Local deployment with Ollama, privacy-focused production

**Pros**:
- No API costs
- Advanced local models
- Easy model management with Ollama
- Privacy-friendly

**Cons**:
- Requires Ollama installation
- Needs sufficient local resources

**Setup**:
```bash
# 1. Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull an embedding model
ollama pull nomic-embed-text

# 3. Verify Ollama is running
curl http://localhost:11434/api/tags
```

**Configuration**:
```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text     # 768 dimensions, 8K context
# or
EMBEDDING_MODEL=mxbai-embed-large    # 1024 dimensions
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_BATCH_SIZE=16
```

**Available Models**:
| Model | Dimensions | Context | Use Case |
|-------|-----------|---------|----------|
| `nomic-embed-text` | 768 | 8192 | Long documents, high quality |
| `mxbai-embed-large` | 1024 | 512 | Best quality, shorter context |

### 3. OpenAI-Compatible API

**Best for**: Production with cloud scaling, highest quality embeddings

**Pros**:
- Highest quality embeddings
- Scalable (no local resources needed)
- Maintained and updated by provider

**Cons**:
- API costs (per token)
- Requires internet connection
- Data sent to external service

**Configuration**:
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
EMBEDDING_BATCH_SIZE=100
```

**OpenAI Models**:
| Model | Dimensions | Cost (per 1M tokens) | Use Case |
|-------|-----------|---------------------|----------|
| `text-embedding-3-small` | 1536 | $0.02 | Cost-effective production |
| `text-embedding-3-large` | 3072 | $0.13 | Maximum quality |
| `text-embedding-ada-002` | 1536 | $0.10 | Legacy (still supported) |

**Alternative APIs** (OpenAI-compatible):
- **Azure OpenAI**: Set `OPENAI_API_BASE` to your Azure endpoint
- **Local API Services**: Any OpenAI-compatible embedding API

## Usage Examples

### Running the Pipeline

```bash
# The pipeline automatically uses your configured provider
python scripts/run_pipeline.py
```

### Programmatic Usage

```python
from src.embeddings.generator import EmbeddingGenerator

# Use default provider from settings
generator = EmbeddingGenerator()

# Or specify provider explicitly
generator = EmbeddingGenerator(
    provider="ollama",
    model_name="nomic-embed-text"
)

# Generate embeddings for chunks
chunks_with_embeddings = generator.process_chunks(chunks)
```

### Switching Providers

Simply update `.env` and restart:

```bash
# Switch from local to OpenAI
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your-key

# Or switch to Ollama
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
```

**Important**: When switching providers, ensure your Neo4j vector index dimension matches:

```python
from src.storage.neo4j_client import Neo4jClient
from src.embeddings.models import ModelConfig

# Get dimension for new model
dimension = ModelConfig.get_model_dimension("text-embedding-3-small", "openai")

# Recreate vector index
client = Neo4jClient()
client.create_vector_index(dimension=dimension)
```

## Troubleshooting

### Sentence Transformers

**Issue**: Model download fails
```bash
# Solution: Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
```

**Issue**: Out of memory
```bash
# Solution: Reduce batch size
EMBEDDING_BATCH_SIZE=8
```

### Ollama

**Issue**: Connection refused
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

**Issue**: Model not found
```bash
# Pull the model
ollama pull nomic-embed-text
```

### OpenAI

**Issue**: Authentication failed
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Issue**: Rate limiting
```bash
# Solution: Reduce batch size
EMBEDDING_BATCH_SIZE=50
```

## Performance Comparison

| Provider | Speed | Cost | Quality | Offline | Privacy |
|----------|-------|------|---------|---------|---------|
| Sentence Transformers | ⚡⚡⚡ | Free | ⭐⭐⭐ | ✅ | ✅ |
| Ollama | ⚡⚡ | Free | ⭐⭐⭐ | ✅ | ✅ |
| OpenAI | ⚡⚡⚡⚡ | $$$ | ⭐⭐⭐⭐ | ❌ | ⚠️ |

## Best Practices

1. **Development**: Use Sentence Transformers with BGE-small (fast, free, easy)
2. **Production (Local)**: Use Ollama with `nomic-embed-text`
3. **Production (Cloud)**: Use OpenAI `text-embedding-3-small`
4. **High Quality Needs**: Use OpenAI `text-embedding-3-large` or Ollama `mxbai-embed-large`
5. **Privacy-Critical**: Use Sentence Transformers or Ollama only

## Advanced Configuration

### Custom Embedding Dimension

Override auto-detection:
```bash
EMBEDDING_DIMENSION=1536
```

### Multiple Configurations

Use different `.env` files:
```bash
# Development
cp .env.dev .env
python scripts/run_pipeline.py

# Production
cp .env.prod .env
python scripts/run_pipeline.py
```

## Environment Variables Reference

### Common Settings
```bash
EMBEDDING_PROVIDER=sentence-transformers  # sentence-transformers, ollama, or openai
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5   # Model name (provider-specific)
EMBEDDING_BATCH_SIZE=32                   # Batch size for processing
EMBEDDING_DIMENSION=                      # Optional: Override dimension
```

### Ollama Settings
```bash
OLLAMA_BASE_URL=http://localhost:11434    # Ollama server URL
```

### OpenAI Settings
```bash
OPENAI_API_KEY=                          # Required for OpenAI provider
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_ORG_ID=                           # Optional: Organization ID
```

## Support

For issues or questions:
- Check logs: `logs/pipeline.log`
- Validate config: `python -c "from config.settings import Settings; Settings.validate()"`
- Test embedding: `pytest tests/unit/test_embeddings.py -v`
- Report issues: [GitHub Issues](your-repo-url)

## Migration Guide

### Upgrading from Previous Versions

If you were using the old single-provider system:

1. **No code changes required** - The default provider is `sentence-transformers` with `BAAI/bge-small-en-v1.5`
2. **Update `.env` file** - Add `EMBEDDING_PROVIDER=sentence-transformers` explicitly
3. **Test your setup** - Run tests to ensure embeddings work correctly
4. **Consider upgrading model** - BGE-small-en-v1.5 offers better quality than MiniLM

### Switching Between Providers

When changing providers:

1. Update `.env` with new provider settings
2. Run a test to verify the new provider works
3. Consider recreating your Neo4j vector index if dimensions changed
4. Document your provider choice in your deployment notes

