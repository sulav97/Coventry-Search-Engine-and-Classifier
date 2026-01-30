"""
Naive Bayes classifier prediction with model caching.
Provides label prediction and confidence scores.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import joblib

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "data" / "model.joblib"

# Module-level cache - load model once
_cached_model = None


def get_model():
    """Get cached model, loading from disk if needed."""
    global _cached_model
    
    if _cached_model is None:
        if not MODEL_PATH.exists():
            logger.warning(f"Model not found at {MODEL_PATH}")
            return None
        
        logger.info(f"Loading classifier model from {MODEL_PATH}")
        _cached_model = joblib.load(MODEL_PATH)
    
    return _cached_model


def predict_label(text: str) -> Tuple[Optional[str], float]:
    """
    Predict category label for text.
    
    Args:
        text: Input text to classify
    
    Returns:
        Tuple of (label, confidence) or (None, 0.0) if model unavailable
    """
    model = get_model()
    if model is None:
        return None, 0.0
    
    try:
        # Get probabilities for all classes
        probas = model.predict_proba([text])[0]
        # Get the index of the highest probability
        max_index = probas.argmax()
        # Get the label and confidence
        label = model.classes_[max_index]
        confidence = probas[max_index]
        
        return str(label), float(confidence)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return None, 0.0


def main():
    """CLI for classification prediction."""
    import argparse
    
    ap = argparse.ArgumentParser(description="Predict category for text")
    ap.add_argument("--text", required=True, help="Text to classify")
    args = ap.parse_args()

    model = get_model()
    if model is None:
        print("Model not found. Train first: python -m classifier.train")
        return

    label, confidence = predict_label(args.text)
    print(f"Text: {args.text}")
    print(f"Predicted: {label} ({confidence:.1%} confidence)")


if __name__ == "__main__":
    main()
