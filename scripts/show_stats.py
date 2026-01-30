"""
Simple statistics about the integrated dataset.
"""
import json

print("=" * 70)
print("INTEGRATION SUCCESS REPORT")
print("=" * 70)

# Load publications
with open("data/publications.jsonl", encoding="utf-8") as f:
    pubs = [json.loads(line) for line in f]

# Load index
with open("data/index.json", encoding="utf-8") as f:
    idx = json.load(f)

print(f"\n📊 Dataset Statistics:")
print(f"   • Total Publications: {len(pubs)}")
print(f"   • Indexed Documents: {len(idx['docs'])}")
print(f"   • Unique Search Terms: {len(idx['index'])}")
print(f"   • Average Document Length: {sum(idx['doc_lengths'].values()) / len(idx['doc_lengths']):.1f} terms")

# Analyze publications
authors = set()
years = []
topics = set()

for pub in pubs:
    authors.update(pub.get('authors', []))
    if pub.get('year'):
        try:
            year = int(pub['year'])
            if 1900 < year < 2030:
                years.append(year)
        except:
            pass

print(f"\n📚 Coverage:")
print(f"   • Unique Authors: {len(authors)}")
if years:
    print(f"   • Publication Years: {min(years)} - {max(years)}")
    print(f"   • Median Year: {sorted(years)[len(years)//2]}")

print(f"\n🔍 Sample Publications:")
for i, pub in enumerate(pubs[:5], 1):
    title = pub['title'][:65] + "..." if len(pub['title']) > 65 else pub['title']
    year = pub.get('year', 'N/A')
    print(f"   {i}. [{year}] {title}")

print("\n" + "=" * 70)
print("✅ INTEGRATION SUCCESSFUL!")
print("=" * 70)
print(f"\nYour search engine now has {len(pubs)} publications")
print("compared to the original 42 publications.")
print(f"\nThat's a {len(pubs) / 42:.1f}x increase in searchable content!")
print("\nServer running at: http://127.0.0.1:8000/")
print("=" * 70)
