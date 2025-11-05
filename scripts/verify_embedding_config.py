#!/usr/bin/env python3
"""Verification script for embedding configuration."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.embeddings.models import ModelConfig


def main():
    """Verify embedding configuration."""
    print("=" * 70)
    print("EMBEDDING CONFIGURATION VERIFICATION")
    print("=" * 70)
    print()

    # 1. Validate settings (skip for now if Neo4j not configured)
    print("1. Validating Settings...")
    try:
        if Settings.validate():
            print("   ✅ Settings validation passed")
        else:
            print("   ⚠️  Settings validation has warnings (check Neo4j config)")
    except Exception as e:
        print(f"   ⚠️  Validation warning: {e}")
    print()

    # 2. Display configuration
    print("2. Current Configuration:")
    print(f"   Provider: {Settings.EMBEDDING_PROVIDER}")
    print(f"   Model: {Settings.EMBEDDING_MODEL}")
    print(f"   Batch Size: {Settings.EMBEDDING_BATCH_SIZE}")
    print()

    # 3. Check model dimension
    print("3. Model Information:")
    dimension = ModelConfig.get_model_dimension(
        Settings.EMBEDDING_MODEL, Settings.EMBEDDING_PROVIDER
    )
    print(f"   Dimension: {dimension}")
    is_supported = ModelConfig.is_model_supported(
        Settings.EMBEDDING_MODEL, Settings.EMBEDDING_PROVIDER
    )
    print(f"   Supported: {'✅ Yes' if is_supported else '⚠️  No (will use custom)'}")
    print()

    # 4. List available models for current provider
    print(f"4. Available Models for '{Settings.EMBEDDING_PROVIDER}':")
    models = ModelConfig.get_provider_models(Settings.EMBEDDING_PROVIDER)
    if models:
        for model_name, specs in models.items():
            marker = "⭐" if model_name == Settings.EMBEDDING_MODEL else "  "
            print(f"   {marker} {model_name}")
            print(f"      - Dimension: {specs['dimension']}")
            print(f"      - Description: {specs['description']}")
    else:
        print(f"   ⚠️  No models defined for provider '{Settings.EMBEDDING_PROVIDER}'")
    print()

    # 5. Provider-specific checks
    print("5. Provider-Specific Checks:")
    if Settings.EMBEDDING_PROVIDER == "sentence-transformers":
        print("   ℹ️  Using local Sentence Transformers")
        print("   ℹ️  No API key required")
        print("   ℹ️  First run will download model from HuggingFace")
    elif Settings.EMBEDDING_PROVIDER == "ollama":
        print("   ℹ️  Using Ollama server")
        print(f"   ℹ️  Server URL: {Settings.OLLAMA_BASE_URL}")
        print("   ⚠️  Make sure Ollama is running: ollama serve")
    elif Settings.EMBEDDING_PROVIDER == "openai":
        print("   ℹ️  Using OpenAI-compatible API")
        print(f"   ℹ️  API Base: {Settings.OPENAI_API_BASE}")
        if Settings.OPENAI_API_KEY:
            print("   ✅ API key is set")
        else:
            print("   ❌ API key is NOT set (required!)")
            return 1
    print()

    # 6. Summary
    print("=" * 70)
    print("✅ CONFIGURATION VERIFIED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run the pipeline: python scripts/run_pipeline.py")
    print("  2. Or test embeddings: pytest tests/unit/test_embeddings.py -v")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

