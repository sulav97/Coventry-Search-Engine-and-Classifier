"""
Quick script to rebuild the search index from publications.jsonl.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search_engine.storage import load_jsonl
from search_engine.indexer import build_documents, build_inverted_index, save_index

# Load publications
print("Loading publications...")
pubs = load_jsonl("data/publications.jsonl")
print(f"Loaded {len(pubs)} publications")

# Build index
print("Building documents...")
docs = build_documents(pubs)
print(f"Created {len(docs)} documents")

print("Building inverted index...")
index, doc_lengths = build_inverted_index(docs)
print(f"Index contains {len(index)} unique terms")

print("Saving index...")
save_index("data/index.json", docs, index, doc_lengths)
print("✓ Index saved successfully!")

print(f"\nIndex Statistics:")
print(f"  Documents: {len(docs)}")
print(f"  Unique terms: {len(index)}")
print(f"  Average doc length: {sum(doc_lengths.values()) / len(doc_lengths):.1f} terms")
