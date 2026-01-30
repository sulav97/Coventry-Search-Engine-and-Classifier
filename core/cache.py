"""
Caching layer for search index and models.
Loads heavy resources once and caches in memory.
"""
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache

from django.conf import settings

logger = logging.getLogger(__name__)

# Paths
INDEX_FILE_PATH = settings.BASE_DIR / "data" / "index.json"
CLASSIFIER_MODEL_PATH = settings.BASE_DIR / "data" / "model.joblib"

# Module-level cache
_index_cache: Optional[Dict] = None
_index_load_time: float = 0.0
_classifier_cache: Optional[Any] = None


def get_search_index() -> Dict:
    """
    Get cached search index. Loads from disk only once.
    Returns empty dict if index not found.
    """
    global _index_cache, _index_load_time
    
    if _index_cache is None:
        from search_engine.storage import load_json
        
        start = time.perf_counter()
        _index_cache = load_json(str(INDEX_FILE_PATH))
        _index_load_time = time.perf_counter() - start
        
        doc_count = len(_index_cache.get("docs", {}))
        logger.info(f"Search index loaded: {doc_count} docs in {_index_load_time:.3f}s")
    
    return _index_cache


def get_index_load_time() -> float:
    """Get the time taken to load the index (for metrics)."""
    global _index_load_time
    return _index_load_time


def invalidate_index_cache():
    """Invalidate the cached index (call after re-indexing)."""
    global _index_cache, _index_load_time
    _index_cache = None
    _index_load_time = 0.0
    logger.info("Index cache invalidated")


def get_classifier_model():
    """
    Get cached Naive Bayes classifier model.
    Returns None if model not found.
    """
    global _classifier_cache
    
    if _classifier_cache is None:
        if not CLASSIFIER_MODEL_PATH.exists():
            logger.warning("Classifier model not found")
            return None
        
        import joblib
        start = time.perf_counter()
        _classifier_cache = joblib.load(CLASSIFIER_MODEL_PATH)
        load_time = time.perf_counter() - start
        logger.info(f"Classifier model loaded in {load_time:.3f}s")
    
    return _classifier_cache


def invalidate_all_caches():
    """Invalidate all caches."""
    global _index_cache, _index_load_time, _classifier_cache
    _index_cache = None
    _index_load_time = 0.0
    _classifier_cache = None
    logger.info("All caches invalidated")

