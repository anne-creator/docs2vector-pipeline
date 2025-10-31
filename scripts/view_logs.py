#!/usr/bin/env python3
"""Interactive log viewer for pipeline components."""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="View component-specific logs",
        epilog="Example: python scripts/view_logs.py scraper --lines 100"
    )
    parser.add_argument(
        "component",
        choices=["scraper", "processor", "chunker", "embeddings", "storage", "pipeline", "all"],
        help="Which component logs to view"
    )
    parser.add_argument(
        "--lines", "-n",
        type=int,
        default=50,
        help="Number of lines to show (default: 50, use 0 for all)"
    )
    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Filter by log level"
    )
    parser.add_argument(
        "--search", "-s",
        help="Search for specific text in logs"
    )
    parser.add_argument(
        "--follow", "-f",
        action="store_true",
        help="Follow log file (like tail -f)"
    )
    
    args = parser.parse_args()
    
    # Determine log file path
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "logs"
    
    if args.component == "all":
        log_file = logs_dir / "pipeline.log"
    else:
        log_file = logs_dir / f"{args.component}.log"
    
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        print(f"   Run the pipeline first to generate logs.")
        sys.exit(1)
    
    # Print header
    print("=" * 80)
    print(f"📋 Viewing: {log_file.name}")
    if args.level:
        print(f"   Level filter: {args.level}")
    if args.search:
        print(f"   Search filter: '{args.search}'")
    print("=" * 80)
    print()
    
    # Handle follow mode
    if args.follow:
        try:
            import time
            print("[Following log file... Press Ctrl+C to stop]")
            print()
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    # Apply filters
                    if args.level and f"[{args.level}]" not in line:
                        continue
                    if args.search and args.search.lower() not in line.lower():
                        continue
                    
                    print(line, end='')
        except KeyboardInterrupt:
            print("\n[Stopped following log]")
            sys.exit(0)
    
    # Read and display log file
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        sys.exit(1)
    
    # Apply filters
    if args.level:
        lines = [l for l in lines if f"[{args.level}]" in l]
    
    if args.search:
        lines = [l for l in lines if args.search.lower() in l.lower()]
    
    # Show last N lines
    if args.lines > 0:
        lines = lines[-args.lines:]
    
    # Display lines
    for line in lines:
        print(line, end='')
    
    # Print footer
    print()
    print("=" * 80)
    print(f"Showing {len(lines)} lines from {log_file.name}")
    if args.lines > 0 and len(lines) == args.lines:
        print(f"(Last {args.lines} lines shown. Use --lines 0 to show all)")
    print("=" * 80)

if __name__ == "__main__":
    main()

