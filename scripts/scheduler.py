"""
Automated scheduler for periodic crawling and indexing.
Provides a Python-based fallback for systems without cron/Task Scheduler.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

try:
    import schedule
except ImportError:
    print("Install schedule: pip install schedule")
    sys.exit(1)

import time
from datetime import datetime

from search_engine.orchestrator import run_pipeline
from search_engine.config import setup_logging

logger = logging.getLogger(__name__)

DEFAULT_SEED = "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/"


def scheduled_crawl():
    """Execute scheduled crawl job."""
    logger.info(f"Starting scheduled crawl at {datetime.now().isoformat()}")
    try:
        stats = run_pipeline(seed_url=DEFAULT_SEED, max_pages=100)
        logger.info(f"Scheduled crawl complete. {stats['total_docs']} documents indexed.")
    except Exception as e:
        logger.error(f"Scheduled crawl failed: {e}")


def main():
    """Run the scheduler."""
    import argparse
    
    setup_logging()
    
    ap = argparse.ArgumentParser(description="Python-based scheduler for crawling")
    ap.add_argument("--interval", choices=["hourly", "daily", "weekly"], default="weekly",
                    help="Crawl interval")
    ap.add_argument("--run-now", action="store_true", help="Run crawl immediately then schedule")
    args = ap.parse_args()

    print(f"ST7071CEM Crawler Scheduler")
    print(f"Interval: {args.interval}")
    print(f"Press Ctrl+C to stop\n")

    # Schedule job based on interval
    if args.interval == "hourly":
        schedule.every().hour.do(scheduled_crawl)
    elif args.interval == "daily":
        schedule.every().day.at("02:00").do(scheduled_crawl)
    else:  # weekly
        schedule.every().sunday.at("02:00").do(scheduled_crawl)
    
    # Run immediately if requested
    if args.run_now:
        scheduled_crawl()
    
    # Print next run time
    next_run = schedule.next_run()
    if next_run:
        print(f"Next scheduled run: {next_run}")
    
    # Run scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()
