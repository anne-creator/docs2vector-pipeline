"""Run the FastAPI server for pipeline API."""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from src.api.server import app


def main():
    """Run the API server."""
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    print("=" * 70)
    print("🚀 Starting Docs2Vector Pipeline API Server")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   API URL: http://{host}:{port}")
    print(f"   API Docs: http://{host}:{port}/docs")
    print("=" * 70)
    
    # Run server
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

