#!/usr/bin/env python3
"""Environment setup helper script."""

"""
Checks for .env file
Validates configuration settings
Creates data directories
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings


def main():
    """Validate and set up environment."""
    print("Checking environment setup...")

    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("WARNING: .env file not found. Copy .env.example to .env and configure it.")
        print("  cp .env.example .env")
        return False

    # Validate settings
    if not Settings.validate():
        print("ERROR: Configuration validation failed.")
        print("Please check your .env file and ensure all required settings are present:")
        print("  - NEO4J_URI")
        print("  - NEO4J_USERNAME")
        print("  - NEO4J_PASSWORD")
        return False

    # Ensure data directories exist
    print("Ensuring data directories exist...")
    Settings.ensure_data_directories()

    print("Environment setup complete!")
    print(f"Data directory: {Settings.DATA_DIR}")
    print(f"Neo4j URI: {Settings.NEO4J_URI}")
    print(f"Neo4j Database: {Settings.NEO4J_DATABASE}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

