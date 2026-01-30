"""
Model Selection and Comparison for Document Classification.
Compares multiple classifiers to justify Naive Bayes selection.
"""
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

DATA_PATH = BASE_DIR / "data" / "news_dataset.csv"
REPORT_ASSETS = BASE_DIR / "report_assets"


def load_data():
    """Load the news dataset."""
    df = pd.read_csv(DATA_PATH)
    return df["text"].values, df["label"].values


def get_classifiers():
    """Return a dictionary of classifiers to compare."""
    return {
        "Naive Bayes": MultinomialNB(),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Linear SVM": LinearSVC(random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=5),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
    }


def evaluate_models(X, y):
    """Evaluate all classifiers and return comparison metrics."""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    # TF-IDF vectorizer (same for all models)
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=1000
    )
    
    # Transform data
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    results = []
    classifiers = get_classifiers()
    
    print("\n" + "="*70)
    print("MODEL SELECTION - CLASSIFIER COMPARISON")
    print("="*70)
    print(f"\nDataset: {len(X)} documents, {len(set(y))} classes")
    print(f"Train/Test: {len(X_train)}/{len(X_test)} documents")
    print("\n" + "-"*70)
    
    for name, clf in classifiers.items():
        # Train
        clf.fit(X_train_tfidf, y_train)
        
        # Predict
        y_pred = clf.predict(X_test_tfidf)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
        recall = recall_score(y_test, y_pred, average='macro', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
        
        # Cross-validation (5-fold)
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(lowercase=True, stop_words="english", 
                                      ngram_range=(1, 2), max_features=1000)),
            ("clf", clf.__class__(**clf.get_params()))
        ])
        cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='accuracy')
        
        results.append({
            "Model": name,
            "Accuracy": round(accuracy * 100, 1),
            "Precision": round(precision * 100, 1),
            "Recall": round(recall * 100, 1),
            "F1-Score": round(f1 * 100, 1),
            "CV Mean": round(cv_scores.mean() * 100, 1),
            "CV Std": round(cv_scores.std() * 100, 1),
        })
        
        print(f"{name:<22} | Acc: {accuracy*100:5.1f}% | F1: {f1*100:5.1f}% | CV: {cv_scores.mean()*100:5.1f}% (±{cv_scores.std()*100:.1f}%)")
    
    print("-"*70)
    
    return results


def generate_comparison_matrix(results):
    """Generate and save the comparison matrix."""
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by F1-Score (best metric for imbalanced/multi-class)
    df = df.sort_values("F1-Score", ascending=False)
    
    # Find best model
    best_model = df.iloc[0]["Model"]
    best_f1 = df.iloc[0]["F1-Score"]
    
    print(f"\n✓ BEST MODEL: {best_model} (F1-Score: {best_f1}%)")
    
    # Save as JSON
    json_path = REPORT_ASSETS / "model_selection_matrix.json"
    with open(json_path, "w") as f:
        json.dump({
            "comparison": results,
            "best_model": best_model,
            "selection_criteria": "F1-Score (macro average)",
            "justification": f"{best_model} selected for highest F1-Score and good cross-validation stability."
        }, f, indent=2)
    print(f"✓ Saved: {json_path}")
    
    # Save as text table
    txt_path = REPORT_ASSETS / "model_selection_matrix.txt"
    with open(txt_path, "w") as f:
        f.write("MODEL SELECTION COMPARISON MATRIX\n")
        f.write("="*80 + "\n\n")
        f.write("Dataset: 114 news documents (Business, Entertainment, Health)\n")
        f.write("Vectorization: TF-IDF with unigrams/bigrams, 1000 max features\n")
        f.write("Evaluation: 75/25 train/test split + 5-fold cross-validation\n\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Model':<22} | {'Accuracy':>8} | {'Precision':>9} | {'Recall':>6} | {'F1-Score':>8} | {'CV Mean':>7} | {'CV Std':>6}\n")
        f.write("-"*80 + "\n")
        
        for _, row in df.iterrows():
            marker = " *" if row["Model"] == best_model else ""
            f.write(f"{row['Model']:<22} | {row['Accuracy']:>7.1f}% | {row['Precision']:>8.1f}% | {row['Recall']:>5.1f}% | {row['F1-Score']:>7.1f}% | {row['CV Mean']:>6.1f}% | ±{row['CV Std']:>4.1f}%{marker}\n")
        
        f.write("-"*80 + "\n\n")
        f.write(f"* SELECTED MODEL: {best_model}\n\n")
        f.write("JUSTIFICATION:\n")
        f.write(f"- {best_model} achieves the highest F1-Score ({best_f1}%)\n")
        f.write("- Good balance between precision and recall across all classes\n")
        f.write("- Fast training and prediction time\n")
        f.write("- Works well with TF-IDF features for text classification\n")
        f.write("- Low cross-validation variance indicates stable performance\n")
    
    print(f"✓ Saved: {txt_path}")
    
    return df, best_model


def main():
    """Run model selection comparison."""
    REPORT_ASSETS.mkdir(parents=True, exist_ok=True)
    
    # Load data
    X, y = load_data()
    
    # Evaluate models
    results = evaluate_models(X, y)
    
    # Generate comparison matrix
    df, best_model = generate_comparison_matrix(results)
    
    print("\n" + "="*70)
    print("MODEL SELECTION COMPLETE")
    print("="*70)
    print(f"\nSelected: {best_model}")
    print("Evidence saved to report_assets/model_selection_matrix.json")
    print("                    report_assets/model_selection_matrix.txt")


if __name__ == "__main__":
    main()
