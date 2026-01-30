"""
One-time crawl script for scheduled execution.
Designed to be called by cron, Task Scheduler, or systemd timers.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from search_engine.orchestrator import run_pipeline
from search_engine.config import setup_logging

DEFAULT_SEED = "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/"


def main():
    """Run crawl once and exit."""
    setup_logging()
    
    print(f"ST7071CEM Scheduled Crawl")
    print(f"Started: {datetime.now().isoformat()}")
    print("-" * 40)
    
    try:
        stats = run_pipeline(
            seed_url=DEFAULT_SEED,
            max_pages=100,
            delay=1.2
        )
        print(f"\nCompleted successfully!")
        print(f"Documents indexed: {stats['total_docs']}")
        print(f"Total time: {stats['total_time']:.2f}s")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
