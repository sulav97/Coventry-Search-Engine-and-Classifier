"""
Pipeline orchestrator for crawl and index operations.
Provides atomic crawl -> merge -> index workflow.
"""
import argparse
import logging
import time
from pathlib import Path

from .config import (
    CrawlConfig, 
    PUBLICATIONS_JSONL, 
    INDEX_JSON, 
    setup_logging
)
from .storage import load_jsonl, append_jsonl
from .crawler import PoliteCrawler, merge_by_url
from .indexer import build_documents, build_inverted_index, save_index

logger = logging.getLogger(__name__)


def run_pipeline(
    seed_url: str,
    max_pages: int = 100,
    delay: float = 1.2,
    user_agent: str = CrawlConfig.user_agent
) -> dict:
    """
    Execute full crawl -> merge -> index pipeline.
    
    Args:
        seed_url: Starting URL for crawler
        max_pages: Maximum pages to crawl
        delay: Delay between requests in seconds
        user_agent: User agent string
    
    Returns:
        Dictionary with pipeline statistics
    """
    stats = {
        "start_time": time.time(),
        "old_docs": 0,
        "new_docs": 0,
        "total_docs": 0,
        "crawl_time": 0,
        "index_time": 0,
    }
    
    logger.info("=" * 60)
    logger.info("Starting crawl + index pipeline")
    logger.info(f"Seed URL: {seed_url}")
    logger.info(f"Max pages: {max_pages}")
    logger.info("=" * 60)
    
    # Load existing publications
    old_pubs = load_jsonl(PUBLICATIONS_JSONL)
    stats["old_docs"] = len(old_pubs)
    logger.info(f"Loaded {len(old_pubs)} existing publications")
    
    # Crawl new publications
    crawl_start = time.time()
    cfg = CrawlConfig(user_agent=user_agent, delay_seconds=delay, max_pages=max_pages)
    crawler = PoliteCrawler(seed_url, cfg)
    new_pubs = crawler.crawl_bfs()
    stats["crawl_time"] = time.time() - crawl_start
    stats["new_docs"] = len(new_pubs)
    
    # Merge old and new
    merged = merge_by_url(old_pubs, new_pubs)
    stats["total_docs"] = len(merged)
    
    # Save merged publications
    append_jsonl(PUBLICATIONS_JSONL, merged)
    
    # Build and save index
    index_start = time.time()
    docs = build_documents(merged)
    index, doc_lengths = build_inverted_index(docs)
    save_index(INDEX_JSON, docs, index, doc_lengths)
    stats["index_time"] = time.time() - index_start
    
    stats["total_time"] = time.time() - stats["start_time"]
    
    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    logger.info(f"Total documents: {stats['total_docs']}")
    logger.info(f"Crawl time: {stats['crawl_time']:.2f}s")
    logger.info(f"Index time: {stats['index_time']:.2f}s")
    logger.info(f"Total time: {stats['total_time']:.2f}s")
    logger.info("=" * 60)
    
    return stats


def invalidate_caches():
    """Invalidate Django caches after index update."""
    try:
        from django.core.cache import cache
        cache.clear()
        logger.info("Django cache invalidated")
    except Exception as e:
        logger.debug(f"Could not invalidate Django cache: {e}")


def main():
    setup_logging()
    
    ap = argparse.ArgumentParser(description="Run crawl + index pipeline")
    ap.add_argument(
        "--seed", 
        default="https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/",
        help="Seed URL to start crawling"
    )
    ap.add_argument("--max-pages", type=int, default=100, help="Maximum pages to crawl")
    ap.add_argument("--delay", type=float, default=1.2, help="Delay between requests")
    args = ap.parse_args()

    stats = run_pipeline(
        seed_url=args.seed,
        max_pages=args.max_pages,
        delay=args.delay
    )
    
    invalidate_caches()
    
    print(f"\n✓ Pipeline complete. {stats['total_docs']} documents indexed.")


if __name__ == "__main__":
    main()
