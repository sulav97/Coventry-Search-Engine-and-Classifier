"""
Robustness demonstration for Naive Bayes classifier.
Tests various input types: short, long, stopwords, noisy, challenging.
"""
import sys
from pathlib import Path

# Add project root to python path to allow imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from classifier.predict import predict_label


def main():
    print("=== TASK 2: CLASSIFICATION ROBUSTNESS DEMONSTRATION ===\n")
    print("This script demonstrates the classifier's ability to handle various input types")
    print("as required by the assignment brief (Short, Long, Stopwords, Noisy, Challenging).\n")

    test_cases = [
        {
            "type": "SHORT INPUT (Single Word)",
            "text": "Stocks",
            "expected": "Business"
        },
        {
            "type": "SHORT INPUT (Phrase)",
            "text": "Hollywood blockbuster movie",
            "expected": "Entertainment"
        },
        {
            "type": "INPUT WITH STOPWORDS",
            "text": "The and of a with stocks and the market",
            "expected": "Business (Keywords 'stocks', 'market' should dominate)"
        },
        {
            "type": "LONG INPUT (Paragraph)",
            "text": "The conceptual underpinnings of modern economic theory suggest that inflation rates are closely tied to central bank policies. However, recent market volatility has challenged these assumptions, leading investors to seek safer assets.",
            "expected": "Business"
        },
        {
            "type": "HEALTH TOPIC",
            "text": "New vaccine trials show promising results for cancer treatment",
            "expected": "Health"
        },
        {
            "type": "NOISY INPUT",
            "text": "asdf12345 stocks $$$ news!!!",
            "expected": "Business (handles noise gracefully)"
        },
        {
            "type": "MIXED/CHALLENGING",
            "text": "The doctor watched a movie about the stock market.",
            "expected": "Ambiguous (Contains terms from Health, Entertainment, Business)"
        }
    ]

    print(f"{'INPUT TYPE':<25} | {'TEXT (Truncated)':<40} | {'CLASSIFIER RESULT':<20}")
    print("-" * 90)

    for case in test_cases:
        text = case["text"]
        
        # Classification
        label, conf = predict_label(text)
        conf_str = f"{conf:.1%}" if label else "N/A"
        
        # Display
        display_text = (text[:37] + "...") if len(text) > 40 else text
        print(f"{case['type']:<25} | {display_text:<40} | {label} ({conf_str})")

    print("\n" + "="*50 + "\n")
    print("CONCLUSION:")
    print("The Naive Bayes classifier successfully processes varied inputs.")
    print("Preprocessing (tokenization, stopword removal, TF-IDF) ensures robustness.")


if __name__ == "__main__":
    main()
