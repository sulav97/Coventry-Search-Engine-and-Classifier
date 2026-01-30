"""
Text preprocessing module with NLTK-based stemming and stopwords.
Provides consistent preprocessing for indexing, querying, and ML pipelines.
"""
import re
from typing import List, Iterable

# Use NLTK's standard English stopwords (179 words) instead of custom list
try:
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words('english'))
except LookupError:
    # Fallback if NLTK data not downloaded
    import nltk
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words('english'))

# Use NLTK's Porter Stemmer instead of custom suffix stripping
from nltk.stem import PorterStemmer
_stemmer = PorterStemmer()

TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> List[str]:
    """Split text into lowercase alphanumeric tokens."""
    if not text:
        return []
    return TOKEN_RE.findall(text.lower())


def normalize_tokens(tokens: Iterable[str]) -> List[str]:
    """Remove single-character tokens and stopwords."""
    out = []
    for t in tokens:
        if len(t) <= 1:
            continue
        if t in STOPWORDS:
            continue
        out.append(t)
    return out


def stem(token: str) -> str:
    """Apply Porter stemming to a token."""
    return _stemmer.stem(token)


def preprocess(text: str, use_stemming: bool = True) -> List[str]:
    """
    Full preprocessing pipeline: tokenize -> normalize -> stem.
    
    Args:
        text: Raw text to preprocess
        use_stemming: Whether to apply stemming (default True for consistency)
    
    Returns:
        List of processed tokens
    """
    terms = normalize_tokens(tokenize(text))
    if use_stemming:
        terms = [stem(t) for t in terms]
    return terms
