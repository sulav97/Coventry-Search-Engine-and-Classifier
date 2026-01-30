import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from .orchestrator import run_pipeline

logger = logging.getLogger(__name__)

STATUS_FILE = Path("data/crawl_status.json")

def get_last_crawl_time():
    """Read keys from JSON file."""
    if not STATUS_FILE.exists():
        return 0
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_crawl_timestamp", 0)
    except Exception as e:
        logger.error(f"Error reading crawl status: {e}")
        return 0

def update_last_crawl_time():
    """Update the JSON file with current timestamp."""
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({
                "last_crawl_timestamp": time.time(),
                "last_crawl_date": datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Error updating crawl status: {e}")

def should_crawl():
    """Check if 7 days have passed since last crawl."""
    last_ts = get_last_crawl_time()
    if last_ts == 0:
        return True # First run or file missing
    
    last_date = datetime.fromtimestamp(last_ts)
    if datetime.now() - last_date > timedelta(days=7):
        return True
    
    return False

    return False

def _run_pipeline_background():
    """Helper to run pipeline in background."""
    try:
        run_pipeline(
            seed_url="https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/",
            max_pages=50
        )
    except Exception as e:
        logger.error(f"Scheduled crawl failed: {e}")

def check_and_run_crawl():
    """Run crawler if scheduled, in background."""
    if should_crawl():
        logger.info("7-day interval reached. Triggering background crawl...")
        # Update timestamp immediately to show next schedule in UI
        update_last_crawl_time()
        import threading
        t = threading.Thread(target=_run_pipeline_background, daemon=True)
        t.start()
        return True
    return False


def get_next_crawl_date():
    """Return the next scheduled crawl date as a formatted string."""
    last_ts = get_last_crawl_time()
    if last_ts == 0:
        return "Not scheduled (run manual crawl first)"
    
    last_date = datetime.fromtimestamp(last_ts)
    next_date = last_date + timedelta(days=7)
    return next_date.strftime("%B %d, %Y %I:%M %p")
