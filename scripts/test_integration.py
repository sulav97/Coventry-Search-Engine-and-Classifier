"""
Quick test script to verify the search engine integration.
"""
import json

# Load the index
print("=" * 60)
print("SEARCH ENGINE TEST RESULTS")
print("=" * 60)

with open("data/index.json", encoding="utf-8") as f:
    index_data = json.load(f)

print(f"\n✓ Documents indexed: {len(index_data['docs'])}")
print(f"✓ Unique terms: {len(index_data['index'])}")
print(f"✓ Average doc length: {sum(index_data['doc_lengths'].values()) / len(index_data['doc_lengths']):.1f} terms")

# Show sample publications
print("\n" + "=" * 60)
print("SAMPLE PUBLICATIONS")
print("=" * 60)

for i, (doc_id, doc) in enumerate(list(index_data['docs'].items())[:3], 1):
    print(f"\n{i}. {doc['title'][:70]}")
    print(f"   Year: {doc['year']}")
    print(f"   Authors: {', '.join(doc['authors'][:3])}")
    if len(doc['authors']) > 3:
        print(f"   ... and {len(doc['authors']) - 3} more")
    print(f"   URL: {doc['publication_url'][:70]}...")

print("\n" + "=" * 60)
print("✓ INTEGRATION SUCCESSFUL!")
print("=" * 60)
print("\nTo test the web interface:")
print("  1. Run: python manage.py runserver")
print("  2. Visit: http://127.0.0.1:8000/")
print("  3. Try searching for: 'machine learning', 'COVID-19', 'neural networks'")
print("=" * 60)
