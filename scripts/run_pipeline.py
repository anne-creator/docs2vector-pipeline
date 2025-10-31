#!/usr/bin/env python3
"""CLI entry point for running the pipeline."""
""" Modes: full, incremental, or auto (checks if update is needed)
    --check flag to test if update should run
    Uses PipelineOrchestrator from src/pipeline/
"""

import argparse
import sys
import logging
import logging.config
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.scheduler import Scheduler
from config.settings import Settings

# Load logging configuration
logging_config_path = Path(__file__).parent.parent / "config" / "logging.yaml"
if logging_config_path.exists():
    with open(logging_config_path, "r") as f:
        logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for pipeline execution."""
    parser = argparse.ArgumentParser(description="Run the Amazon Sellers Data Pipeline")
    parser.add_argument(
        "--mode",
        choices=["full", "incremental", "auto"],
        default="auto",
        help="Pipeline execution mode (default: auto)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if update is needed, don't run pipeline",
    )

    args = parser.parse_args()

    try:
        # Validate configuration
        if not Settings.validate():
            logger.error("Configuration validation failed. Please check your .env file.")
            sys.exit(1)

        # Ensure data directories exist
        Settings.ensure_data_directories()

        if args.check:
            # Only check if update is needed
            scheduler = Scheduler()
            result = scheduler.should_trigger_update()
            logger.info(f"Update check result: {result}")
            if result["should_update"]:
                logger.info(f"Update recommended: {result['reason']}")
                sys.exit(0)
            else:
                logger.info("No update needed")
                sys.exit(1)

        # Determine execution mode
        if args.mode == "auto":
            scheduler = Scheduler()
            check_result = scheduler.should_trigger_update()
            if check_result["should_update"]:
                mode = check_result["update_type"]
                logger.info(f"Auto mode: {mode} update triggered - {check_result['reason']}")
            else:
                logger.info("Auto mode: No update needed")
                sys.exit(0)
        else:
            mode = args.mode

        # Run pipeline
        orchestrator = PipelineOrchestrator()

        if mode == "full":
            logger.info("Starting full pipeline execution...")
            results = orchestrator.run_full_pipeline()
        elif mode == "incremental":
            logger.info("Starting incremental pipeline execution...")
            results = orchestrator.run_incremental_update()
        else:
            logger.error(f"Unknown mode: {mode}")
            sys.exit(1)

        if results.get("success"):
            logger.info("Pipeline completed successfully")
            logger.info(f"  Documents processed: {results.get('documents_processed', 0)}")
            logger.info(f"  Chunks created: {results.get('chunks_created', 0)}")
            logger.info(f"  Embeddings generated: {results.get('embeddings_generated', 0)}")
            logger.info(f"  Chunks loaded to Neo4j: {results.get('chunks_loaded', 0)}")
            sys.exit(0)
        else:
            logger.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

