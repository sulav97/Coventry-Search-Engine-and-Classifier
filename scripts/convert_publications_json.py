"""
Convert publications.json to publications.jsonl format.

This script transforms the large publications.json dataset into the format
expected by the search engine system, merges it with existing publications,
and saves the result.

Usage:
    python scripts/convert_publications_json.py
    python scripts/convert_publications_json.py --validate
    python scripts/convert_publications_json.py --source path/to/publications.json
"""
import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from search_engine.storage import load_jsonl, append_jsonl, canonicalize_url

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_year(published_date: str) -> str:
    """
    Extract year from published_date field.
    
    Examples:
        "22 Apr 2022" -> "2022"
        "Aug 2012" -> "2012"
        "2013" -> "2013"
        "15 Mar 2017" -> "2017"
    """
    if not published_date:
        return ""
    
    # Try to find a 4-digit year
    match = re.search(r'\b(19|20)\d{2}\b', published_date)
    if match:
        return match.group(0)
    
    return ""


def convert_publication(pub: Dict) -> Dict:
    """
    Convert a publication from the JSON format to JSONL format.
    
    Input format:
        {
            "title": "...",
            "link": "...",
            "abstract": "...",
            "published_date": "...",
            "authors": [
                {"name": "...", "profile_url": "..."},
                ...
            ]
        }
    
    Output format:
        {
            "publication_url": "...",
            "title": "...",
            "year": "...",
            "authors": ["...", ...],
            "author_urls": ["...", ...],
            "abstract": "..."
        }
    """
    # Extract author names and URLs
    authors = []
    author_urls = []
    
    for author in pub.get("authors", []):
        if isinstance(author, dict):
            name = author.get("name", "").strip()
            profile_url = author.get("profile_url", "").strip()
            
            if name:
                authors.append(name)
            if profile_url:
                author_urls.append(profile_url)
    
    # Convert to target format
    converted = {
        "publication_url": pub.get("link", "").strip(),
        "title": pub.get("title", "").strip(),
        "year": extract_year(pub.get("published_date", "")),
        "authors": authors,
        "author_urls": author_urls,
        "abstract": pub.get("abstract", "").strip()
    }
    
    return converted


def load_publications_json(json_path: str) -> List[Dict]:
    """Load publications from the source JSON file."""
    path = Path(json_path)
    
    if not path.exists():
        logger.error(f"File not found: {json_path}")
        return []
    
    logger.info(f"Loading publications from {json_path}")
    
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    publications = data.get("publications", [])
    logger.info(f"Loaded {len(publications)} publications from JSON")
    
    return publications


def validate_conversion(original: List[Dict], converted: List[Dict]) -> bool:
    """
    Validate that the conversion was successful.
    
    Checks:
    - Number of publications matches
    - All required fields are present
    - No empty URLs (except for publications without URLs in original)
    """
    logger.info("=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)
    
    # Check counts
    logger.info(f"Original publications: {len(original)}")
    logger.info(f"Converted publications: {len(converted)}")
    
    if len(original) != len(converted):
        logger.warning("Count mismatch!")
    
    # Check required fields
    required_fields = ["publication_url", "title", "year", "authors", "author_urls", "abstract"]
    missing_fields = []
    
    for i, pub in enumerate(converted):
        for field in required_fields:
            if field not in pub:
                missing_fields.append((i, field))
    
    if missing_fields:
        logger.error(f"Missing fields: {missing_fields[:5]} (showing first 5)")
        return False
    else:
        logger.info("✓ All required fields present")
    
    # Check URLs
    empty_urls = sum(1 for pub in converted if not pub.get("publication_url"))
    logger.info(f"Publications with empty URLs: {empty_urls}")
    
    # Check authors
    pubs_with_authors = sum(1 for pub in converted if pub.get("authors"))
    logger.info(f"Publications with authors: {pubs_with_authors}/{len(converted)}")
    
    # Sample output
    logger.info("\n" + "=" * 60)
    logger.info("SAMPLE CONVERTED PUBLICATION")
    logger.info("=" * 60)
    if converted:
        sample = converted[0]
        logger.info(f"Title: {sample['title'][:80]}...")
        logger.info(f"Year: {sample['year']}")
        logger.info(f"Authors: {sample['authors'][:3]}")
        logger.info(f"URL: {sample['publication_url'][:80]}...")
        logger.info(f"Abstract length: {len(sample['abstract'])} chars")
    
    logger.info("=" * 60)
    logger.info("✓ Validation complete")
    logger.info("=" * 60)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Convert publications.json to JSONL format")
    parser.add_argument(
        "--source",
        default="publications.json",
        help="Path to source publications.json file"
    )
    parser.add_argument(
        "--output",
        default="data/publications.jsonl",
        help="Path to output JSONL file"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate conversion without saving"
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Don't merge with existing publications, replace entirely"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup of existing publications.jsonl (default: True)"
    )
    
    args = parser.parse_args()
    
    # Load source JSON
    original_pubs = load_publications_json(args.source)
    
    if not original_pubs:
        logger.error("No publications loaded. Exiting.")
        return 1
    
    # Convert publications
    logger.info("Converting publications...")
    converted_pubs = [convert_publication(pub) for pub in original_pubs]
    
    # Remove publications without URLs
    converted_pubs = [pub for pub in converted_pubs if pub.get("publication_url")]
    logger.info(f"Converted {len(converted_pubs)} publications with valid URLs")
    
    # Validate
    if not validate_conversion(original_pubs, converted_pubs):
        logger.error("Validation failed!")
        if not args.validate:
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1
    
    # Stop here if validate-only mode
    if args.validate:
        logger.info("Validation mode - not saving files")
        return 0
    
    # Backup existing file
    output_path = Path(args.output)
    if args.backup and output_path.exists():
        backup_path = output_path.with_suffix('.jsonl.bak')
        import shutil
        shutil.copy2(output_path, backup_path)
        logger.info(f"Backed up existing file to {backup_path}")
    
    # Load existing publications if merging
    existing_pubs = []
    if not args.no_merge and output_path.exists():
        existing_pubs = load_jsonl(args.output)
        logger.info(f"Loaded {len(existing_pubs)} existing publications")
    
    # Merge publications
    all_pubs = existing_pubs + converted_pubs
    logger.info(f"Total publications before deduplication: {len(all_pubs)}")
    
    # Save merged publications (append_jsonl handles deduplication)
    append_jsonl(args.output, all_pubs)
    
    # Load back to get final count
    final_pubs = load_jsonl(args.output)
    
    logger.info("=" * 60)
    logger.info("CONVERSION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Original publications in JSON: {len(original_pubs)}")
    logger.info(f"Converted publications: {len(converted_pubs)}")
    logger.info(f"Existing publications: {len(existing_pubs)}")
    logger.info(f"Final publications (after deduplication): {len(final_pubs)}")
    logger.info(f"Output file: {args.output}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
