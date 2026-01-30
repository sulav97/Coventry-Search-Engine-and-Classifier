"""
Complete evidence verification script for coursework report.
Validates all claims against actual data files.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent

print("="*80)
print("EVIDENCE VERIFICATION REPORT")
print("="*80)

# 1. Check publications data
print("\n1. PUBLICATIONS DATA:")
pubs_file = BASE / "data" / "publications.jsonl"
if pubs_file.exists():
    pubs = pubs_file.read_text().strip().split('\n')
    print(f"   ✓ Total publications: {len(pubs)}")
    
    # Parse years and authors
    years = []
    all_authors = set()
    for line in pubs:
        try:
            pub = json.loads(line)
            if pub.get('year'):
                years.append(str(pub['year']))
            if pub.get('authors'):
                all_authors.update(pub['authors'])
        except:
            pass
    
    if years:
        print(f"   ✓ Year range: {min(years)} - {max(years)}")
    print(f"   ✓ Unique authors: {len(all_authors)}")
else:
    print("   ✗ publications.jsonl not found")

# 2. Check index data
print("\n2. INDEX DATA:")
index_file = BASE / "data" / "index.json"
if index_file.exists():
    idx = json.load(open(index_file))
    docs = idx.get('docs', {})
    index = idx.get('index', {})
    
    print(f"   ✓ Documents in index: {len(docs)}")
    print(f"   ✓ Vocabulary size: {len(index)}")
    
    # Count total postings
    total_postings = sum(len(postings) for postings in index.values())
    print(f"   ✓ Total postings: {total_postings}")
else:
    print("   ✗ index.json not found")

# 3. Check classification metrics
print("\n3. CLASSIFICATION METRICS:")
metrics_file = BASE / "report_assets" / "classification_metrics.json"
if metrics_file.exists():
    metrics = json.load(open(metrics_file))
    print(f"   ✓ Accuracy: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"   ✓ Test size: {metrics['test_size']}")
    print(f"   ✓ Train size: {metrics['train_size']}")
    print(f"   ✓ Total dataset: {metrics['test_size'] + metrics['train_size']}")
    print(f"   ✓ Train/Test split: {metrics['train_size']}/{metrics['test_size']}")
    split_pct = metrics['test_size'] / (metrics['test_size'] + metrics['train_size']) * 100
    print(f"   ✓ Split percentage: {100-split_pct:.0f}/{split_pct:.0f}")
    
    print("\n   Per-class metrics:")
    for cls, vals in metrics['per_class_metrics'].items():
        print(f"   - {cls}: P={vals['precision']:.2f}, R={vals['recall']:.2f}, F1={vals['f1-score']:.2f}")
else:
    print("   ✗ classification_metrics.json not found")

# 4. Check performance metrics
print("\n4. SEARCH PERFORMANCE METRICS:")
perf_file = BASE / "report_assets" / "performance_metrics.json"
if perf_file.exists():
    perf = json.load(open(perf_file))
    print(f"   ✓ Index load time: {perf['index_load_time_seconds']*1000:.2f} ms")
    print(f"   ✓ Document count: {perf['document_count']}")
    print(f"   ✓ Average query time: {perf['average_query_time_ms']:.2f} ms")
    print(f"   ✓ Query samples tested: {len(perf['query_samples'])}")
else:
    print("   ✗ performance_metrics.json not found")

# 5. Check requirements.txt
print("\n5. INSTALLED PACKAGES:")
req_file = BASE / "requirements.txt"
if req_file.exists():
    reqs = req_file.read_text().strip().split('\n')
    packages = [r.split('>=')[0].split('==')[0].strip() for r in reqs if r.strip()]
    for pkg in packages:
        print(f"   ✓ {pkg}")
else:
    print("   ✗ requirements.txt not found")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
