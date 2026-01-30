"""
Central configuration for the ST7071CEM Information Retrieval system.
All magic numbers and paths are centralized here.
"""
from dataclasses import dataclass
from pathlib import Path

# =============================================================================
# Path Configuration
# =============================================================================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PUBLICATIONS_JSONL = str(DATA_DIR / "publications.jsonl")
INDEX_JSON = str(DATA_DIR / "index.json")

# Report assets directory
REPORT_ASSETS_DIR = BASE_DIR / "report_assets"


# =============================================================================
# Crawler Configuration
# =============================================================================
@dataclass(frozen=True)
class CrawlConfig:
    user_agent: str = "ST7071CEM-StudentCrawler/1.0 (+contact: your_email@example.com)"
    delay_seconds: float = 1.2
    max_pages: int = 300
    same_domain_only: bool = True
    max_retries: int = 3
    retry_backoff_base: float = 2.0  # Exponential backoff base


# =============================================================================
# Search Configuration
# =============================================================================
SEARCH_TOP_K = 50  # Maximum results to retrieve internally
RESULTS_PAGE_SIZE = 10  # Results per page in UI
USE_STEMMING = True  # Enable stemming by default for consistency


# =============================================================================
# Classification Configuration
# =============================================================================
CLASSIFICATION_MODEL_PATH = DATA_DIR / "model.joblib"
NEWS_DATASET_PATH = DATA_DIR / "news_dataset.csv"


# =============================================================================
# Logging Configuration
# =============================================================================
import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_LEVEL = logging.INFO


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
