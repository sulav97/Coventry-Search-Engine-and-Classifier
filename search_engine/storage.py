"""
Storage utilities for JSON/JSONL data persistence.
Includes URL canonicalization for deduplication.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    """
    Normalize URL for deduplication.
    - Lowercase scheme and netloc
    - Remove trailing slash
    - Sort query parameters
    - Remove fragment
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.lower().strip())
        # Sort query parameters for consistency
        query = urlencode(sorted(parse_qsl(parsed.query)))
        # Remove trailing slash from path
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        # Reconstruct without fragment
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            '',  # params
            query,
            ''   # fragment
        ))
    except Exception:
        return url.lower().strip().rstrip('/')


def append_jsonl(path: str, records: Iterable[Dict]) -> None:
    """
    Write records to JSONL file (overwrites existing).
    Uses canonicalized URLs for deduplication.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    # Deduplicate by canonicalized URL
    seen_urls = set()
    unique_records = []
    for r in records:
        url = r.get("publication_url", "")
        canonical = canonicalize_url(url)
        if canonical and canonical not in seen_urls:
            seen_urls.add(canonical)
            unique_records.append(r)
        elif not canonical:
            unique_records.append(r)  # Keep records without URL
    
    with p.open("w", encoding="utf-8") as f:
        for r in unique_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    logger.info(f"Saved {len(unique_records)} records to {path}")


def load_jsonl(path: str) -> List[Dict]:
    """Load records from JSONL file."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def save_json(path: str, obj: Dict) -> None:
    """Save dictionary to JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Saved JSON to {path}")


def load_json(path: str) -> Dict:
    """Load dictionary from JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))
