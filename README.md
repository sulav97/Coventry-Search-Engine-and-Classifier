# ST7071CEM - Intelligent Information Retrieval System

A comprehensive search engine and text classification system for Coventry University research publications.

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords')"

# Run the web application
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to access the web interface.

---

## Features

- **Vertical Search Engine** - BM25-ranked search over Coventry University research publications
- **Naive Bayes Classification** - News category prediction (Business/Entertainment/Health)
- **Web Interface** - Django-powered UI with dark theme

---

## Run Commands

### 1. Crawl and Index Publications

```powershell
# Full crawl with orchestrator (recommended)
python -m search_engine.orchestrator --max-pages 100

# Or use crawler directly
python -m search_engine.crawler --seed "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/" --max-pages 100
```

### 2. Train Classification Model

```powershell
# Collect training data (if not done)
python -m classifier.rss_collect --per-class 40

# Train Naive Bayes classifier
python -m classifier.train
```

### 3. Generate Evidence Artifacts

```powershell
# Generate all evidence for report
python scripts/generate_evidence.py
```

This creates:
- `report_assets/confusion_matrix.png`
- `report_assets/classification_metrics.json`
- `report_assets/performance_metrics.json`
- `report_assets/robustness_test_output.txt`

### 4. Run Robustness Tests

```powershell
python -m classifier.demo_robustness
```

---

## Scheduling (Automatic Updates)

### Option A: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → Name: "ST7071CEM Weekly Crawl"
3. Trigger: Weekly (Sunday 2:00 AM)
4. Action: Start a Program
   - Program: `python`
   - Arguments: `scripts/run_crawl_once.py`
   - Start in: `C:\path\to\project`

### Option B: Linux Cron

```bash
# Edit crontab
crontab -e

# Add weekly job (Sunday 2:00 AM)
0 2 * * 0 cd /path/to/project && python scripts/run_crawl_once.py >> logs/crawl.log 2>&1
```

### Option C: systemd Timer (Linux)

Create `/etc/systemd/system/st7071cem-crawl.service`:
```ini
[Unit]
Description=ST7071CEM Weekly Crawler

[Service]
Type=oneshot
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python scripts/run_crawl_once.py
```

Create `/etc/systemd/system/st7071cem-crawl.timer`:
```ini
[Unit]
Description=Run ST7071CEM crawler weekly

[Timer]
OnCalendar=Sun *-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable: `sudo systemctl enable --now st7071cem-crawl.timer`

### Option D: Python Scheduler (Fallback)

```powershell
# Run scheduler daemon
python scripts/scheduler.py --interval weekly

# Run immediately then schedule
python scripts/scheduler.py --interval weekly --run-now
```

---

## Project Structure

```
project/
├── core/                   # Django web app
│   ├── templates/          # HTML templates
│   ├── views.py            # View handlers
│   ├── cache.py            # Index/model caching
│   └── urls.py             # URL routing
├── search_engine/          # Task 1 modules
│   ├── crawler.py          # BFS crawler with retry
│   ├── indexer.py          # Inverted index builder
│   ├── search.py           # BM25 search
│   ├── preprocess.py       # NLTK-based preprocessing
│   ├── orchestrator.py     # Pipeline coordination
│   └── config.py           # Central configuration
├── classifier/             # Task 2 modules
│   ├── train.py            # Naive Bayes training
│   ├── predict.py          # Classification inference
│   └── rss_collect.py      # Data collection
├── scripts/                # Automation
│   ├── generate_evidence.py
│   ├── scheduler.py
│   └── run_crawl_once.py
├── data/                   # Data storage
│   ├── index.json          # Search index
│   ├── publications.jsonl  # Crawled publications
│   └── model.joblib        # Classification model
├── report_assets/          # Evidence for report
└── requirements.txt
```

---

## API Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/` | GET | Home/Search page |
| `/search/?q=query` | GET | Search results with pagination |
| `/classify/` | GET/POST | Classification page |

---

## Configuration

All settings are centralized in `search_engine/config.py`:

- `SEARCH_TOP_K` - Maximum search results
- `RESULTS_PAGE_SIZE` - Results per page
- `USE_STEMMING` - Enable Porter stemming

---

## Requirements

- Python 3.9+
- Django 4.2+
- scikit-learn 1.3+
- NLTK 3.8+
- matplotlib 3.7+
- See `requirements.txt` for full list
