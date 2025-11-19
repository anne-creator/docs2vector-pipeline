#!/usr/bin/env python3
"""Export embeddings to CSV format for RAG system ingestion.

This script demonstrates how to use the CSV exporter as the final stage
of the data pipeline to export embeddings for use in a RAG system.

Usage:
    # Export specific JSON file
    python scripts/export_embeddings_to_csv.py --input data/embeddings/embeddings_20251031_174503_20251105_020811.json
    
    # Export all embeddings in a directory
    python scripts/export_embeddings_to_csv.py --batch --input data/embeddings/
    
    # Export without embedding vectors (metadata only)
    python scripts/export_embeddings_to_csv.py --input data/embeddings/embeddings_20251031_174503_20251105_020811.json --no-embeddings
"""

import argparse
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.export.csv_exporter import CSVExporter
from config.settings import Settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def export_single_file(input_path: Path, output_dir: Path, include_embeddings: bool = True):
    """Export a single embeddings JSON file to CSV."""
    logger.info(f"Exporting single file: {input_path}")
    
    exporter = CSVExporter(output_dir=output_dir)
    output_file = exporter.export_from_json_file(
        input_path,
        include_embedding=include_embeddings
    )
    
    logger.info(f"✅ Successfully exported to: {output_file}")
    return output_file


def export_batch(input_dir: Path, output_dir: Path, include_embeddings: bool = True):
    """Export all embeddings JSON files in a directory to CSV."""
    logger.info(f"Batch exporting from directory: {input_dir}")
    
    exporter = CSVExporter(output_dir=output_dir)
    output_files = exporter.batch_export_directory(
        input_dir,
        pattern="*.json",
        include_embedding=include_embeddings
    )
    
    logger.info(f"✅ Successfully exported {len(output_files)} files")
    for output_file in output_files:
        logger.info(f"  - {output_file.name}")
    
    return output_files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export embeddings to CSV format for RAG system ingestion"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Settings.DATA_DIR / "embeddings",
        help="Input JSON file or directory (default: data/embeddings/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Settings.DATA_DIR / "csv_export",
        help="Output directory for CSV files (default: data/csv_export/)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch export all JSON files in input directory"
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Export metadata only, exclude embedding vectors"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)
    
    try:
        include_embeddings = not args.no_embeddings
        
        if args.batch:
            # Batch export
            if not args.input.is_dir():
                logger.error(f"❌ Input must be a directory for batch export: {args.input}")
                return 1
            
            export_batch(args.input, args.output, include_embeddings)
        else:
            # Single file export
            if args.input.is_dir():
                # If directory given without --batch, find latest file
                json_files = list(args.input.glob("*.json"))
                if not json_files:
                    logger.error(f"❌ No JSON files found in: {args.input}")
                    return 1
                
                # Use most recent file
                input_file = max(json_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Using latest file: {input_file.name}")
            else:
                input_file = args.input
            
            if not input_file.exists():
                logger.error(f"❌ Input file not found: {input_file}")
                return 1
            
            export_single_file(input_file, args.output, include_embeddings)
        
        logger.info("🎉 Export completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

