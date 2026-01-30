"""
Naive Bayes classifier training with evaluation artifacts.
Generates confusion matrix and classification report for evidence.
"""
import json
import logging
from pathlib import Path

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    classification_report, 
    accuracy_score, 
    confusion_matrix,
    ConfusionMatrixDisplay
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = BASE_DIR / "data" / "news_dataset.csv"
MODEL_PATH = BASE_DIR / "data" / "model.joblib"
REPORT_ASSETS_DIR = BASE_DIR / "report_assets"


def main():
    """Train classifier and generate evaluation artifacts."""
    from search_engine.config import setup_logging
    setup_logging()
    
    if not DATASET_PATH.exists():
        print(f"Dataset not found at {DATASET_PATH}")
        print("Run: python -m classifier.rss_collect --per-class 40")
        return

    # Create output directories
    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(DATASET_PATH)
    X = df["text"].astype(str)
    y = df["label"].astype(str)
    
    print(f"Loaded {len(X)} documents with {len(y.unique())} classes")
    print(f"Classes: {list(y.unique())}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Create and train pipeline
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True, 
            stop_words="english", 
            ngram_range=(1, 2),
            max_features=1000
        )),
        ("nb", MultinomialNB()),
    ])

    print("Training model...")
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    # Calculate metrics
    acc = accuracy_score(y_test, pred)
    report = classification_report(y_test, pred, output_dict=True)
    report_text = classification_report(y_test, pred)
    
    print(f"\nAccuracy: {acc:.3f}")
    print(report_text)

    # Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n✓ Model saved: {MODEL_PATH}")

    # Generate confusion matrix image
    cm = confusion_matrix(y_test, pred, labels=model.classes_)
    fig, ax = plt.subplots(figsize=(8, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
    disp.plot(ax=ax, cmap='Blues', colorbar=True)
    ax.set_title('Naive Bayes Classification - Confusion Matrix')
    plt.tight_layout()
    
    cm_path = REPORT_ASSETS_DIR / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Confusion matrix saved: {cm_path}")

    # Save metrics as JSON
    metrics = {
        "accuracy": round(acc, 4),
        "classes": list(model.classes_),
        "test_size": len(y_test),
        "train_size": len(y_train),
        "per_class_metrics": {
            cls: {
                "precision": round(report[cls]["precision"], 4),
                "recall": round(report[cls]["recall"], 4),
                "f1-score": round(report[cls]["f1-score"], 4),
                "support": report[cls]["support"]
            }
            for cls in model.classes_
        },
        "macro_avg": {
            "precision": round(report["macro avg"]["precision"], 4),
            "recall": round(report["macro avg"]["recall"], 4),
            "f1-score": round(report["macro avg"]["f1-score"], 4),
        }
    }
    
    metrics_path = REPORT_ASSETS_DIR / "classification_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    print(f"✓ Metrics saved: {metrics_path}")
    
    # Save classification report as text
    report_path = REPORT_ASSETS_DIR / "classification_report.txt"
    report_path.write_text(f"Classification Report\n{'='*50}\n\nAccuracy: {acc:.4f}\n\n{report_text}")
    print(f"✓ Report saved: {report_path}")


if __name__ == "__main__":
    main()
