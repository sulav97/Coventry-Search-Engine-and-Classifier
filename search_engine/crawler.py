"""
Web crawler with BFS traversal, politeness controls, and robust error handling.
Fetches research publications from Coventry University PurePortal.
"""
import argparse
import time
import re
import logging
from collections import deque
from urllib.parse import urlparse
import urllib.robotparser as robotparser

import requests

from .config import CrawlConfig, PUBLICATIONS_JSONL, INDEX_JSON
from .storage import append_jsonl, load_jsonl, canonicalize_url
from .parser import extract_links, parse_publication_page, parse_list_page_for_publications
from .indexer import build_documents, build_inverted_index, save_index

logger = logging.getLogger(__name__)

PUB_RE = re.compile(r"/en/publications/")


def same_domain(a: str, b: str) -> bool:
    """Check if two URLs are on the same domain."""
    return urlparse(a).netloc == urlparse(b).netloc


class PoliteCrawler:
    """
    BFS crawler with politeness controls:
    - Respects robots.txt
    - Honors crawl-delay
    - Retries with exponential backoff
    - Logs all operations
    """

    def __init__(self, seed_url: str, cfg: CrawlConfig):
        self.seed_url = seed_url
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": cfg.user_agent})
        self.delay_seconds = cfg.delay_seconds

        # Parse robots.txt
        self.robots = robotparser.RobotFileParser()
        robots_url = f"{urlparse(seed_url).scheme}://{urlparse(seed_url).netloc}/robots.txt"
        self.robots.set_url(robots_url)
        try:
            resp = self.session.get(robots_url, timeout=15)
            if resp.status_code == 200:
                self.robots.parse(resp.text.splitlines())
                self.robots_ok = True
                crawl_delay = self.robots.crawl_delay(cfg.user_agent) or self.robots.crawl_delay("*")
                if crawl_delay:
                    self.delay_seconds = max(self.delay_seconds, float(crawl_delay))
                logger.info(f"Loaded robots.txt, crawl delay: {self.delay_seconds}s")
            else:
                self.robots_ok = False
                logger.warning(f"Could not load robots.txt (status {resp.status_code})")
        except Exception as e:
            self.robots_ok = False
            logger.warning(f"Failed to fetch robots.txt: {e}")

    def allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        try:
            return self.robots.can_fetch(self.cfg.user_agent, url) if self.robots_ok else True
        except Exception:
            return False

    def fetch(self, url: str) -> str:
        """
        Fetch URL with retry and exponential backoff.
        Returns HTML content or raises exception after max retries.
        """
        last_error = None
        for attempt in range(self.cfg.max_retries):
            try:
                time.sleep(self.delay_seconds)
                r = self.session.get(url, timeout=30)
                r.raise_for_status()
                return r.text
            except requests.exceptions.RequestException as e:
                last_error = e
                wait_time = self.cfg.retry_backoff_base ** attempt
                logger.warning(f"Fetch failed for {url} (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        logger.error(f"Failed to fetch {url} after {self.cfg.max_retries} attempts: {last_error}")
        raise last_error

    def crawl_bfs(self):
        """
        Perform BFS crawl starting from seed URL.
        Returns list of parsed publications.
        """
        queue = deque([self.seed_url])
        visited = set()
        publications = []

        logger.info(f"Starting crawl from {self.seed_url}, max pages: {self.cfg.max_pages}")

        while queue and len(visited) < self.cfg.max_pages:
            url = queue.popleft()
            canonical = canonicalize_url(url)
            
            if canonical in visited:
                continue
            visited.add(canonical)

            if self.cfg.same_domain_only and not same_domain(self.seed_url, url):
                continue

            if not self.allowed(url):
                logger.debug(f"Blocked by robots.txt: {url}")
                continue

            try:
                html = self.fetch(url)
            except Exception as e:
                logger.error(f"Skipping {url} due to fetch error: {e}")
                continue

            # Extract publication links from list pages
            for lp in parse_list_page_for_publications(url, html):
                pu = lp.get("publication_url")
                if pu and canonicalize_url(pu) not in visited:
                    queue.append(pu)

            # Extract publication data if it is a publication page
            if PUB_RE.search(url):
                pub = parse_publication_page(url, html)
                pub["source_url"] = url
                publications.append(pub)
                logger.info(f"Parsed publication: {pub.get('title', 'Unknown')[:50]}...")

            # Add more internal links for BFS
            for link in extract_links(url, html):
                if self.cfg.same_domain_only and not same_domain(self.seed_url, link):
                    continue
                # More robust URL pattern matching
                if any(pattern in link for pattern in ["/en/organisations/", "/en/publications/", "/en/persons/"]):
                    if canonicalize_url(link) not in visited:
                        queue.append(link)

        logger.info(f"Crawl complete. Visited {len(visited)} pages, found {len(publications)} publications")
        return publications


def merge_by_url(old, new):
    """Merge publications by URL, preferring newer data."""
    by_url = {}
    for p in old:
        url = p.get("publication_url")
        if url:
            by_url[canonicalize_url(url)] = p
    
    new_count = 0
    updated_count = 0
    for p in new:
        u = p.get("publication_url")
        if u:
            canonical = canonicalize_url(u)
            if canonical in by_url:
                by_url[canonical] = {**by_url[canonical], **p}
                updated_count += 1
            else:
                by_url[canonical] = p
                new_count += 1
    
    logger.info(f"Merge result: {new_count} new, {updated_count} updated, {len(by_url)} total")
    return list(by_url.values())


def main():
    from .config import setup_logging
    setup_logging()
    
    ap = argparse.ArgumentParser(description="Crawl Coventry University PurePortal for publications")
    ap.add_argument("--seed", required=True, help="Seed URL to start crawling")
    ap.add_argument("--max-pages", type=int, default=CrawlConfig.max_pages, help="Maximum pages to crawl")
    ap.add_argument("--delay", type=float, default=CrawlConfig.delay_seconds, help="Delay between requests")
    ap.add_argument("--user-agent", default=CrawlConfig.user_agent, help="User agent string")
    args = ap.parse_args()

    cfg = CrawlConfig(user_agent=args.user_agent, delay_seconds=args.delay, max_pages=args.max_pages)
    crawler = PoliteCrawler(args.seed, cfg)
    new_pubs = crawler.crawl_bfs()

    old = load_jsonl(PUBLICATIONS_JSONL)
    merged = merge_by_url(old, new_pubs)

    append_jsonl(PUBLICATIONS_JSONL, merged)

    docs = build_documents(merged)
    index, doc_lengths = build_inverted_index(docs)
    save_index(INDEX_JSON, docs, index, doc_lengths)

    print(f"\nCrawl finished.")
    print(f"Publications stored: {len(merged)}")
    print(f"Saved: {PUBLICATIONS_JSONL}")
    print(f"Saved: {INDEX_JSON}")


if __name__ == "__main__":
    main()
