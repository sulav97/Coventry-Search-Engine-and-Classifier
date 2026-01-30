"""
Django views for search and classification.
Uses cached index and models for performance.
"""
import time
import logging
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.core.paginator import Paginator

from search_engine.search import search as execute_search_query
from search_engine.config import RESULTS_PAGE_SIZE, USE_STEMMING

logger = logging.getLogger(__name__)


def home(request):
    """Home page with search form."""

    from search_engine.scheduler import check_and_run_crawl, get_next_crawl_date
    check_and_run_crawl()
    next_crawl = get_next_crawl_date()
    return render(request, "index.html", {"next_crawl": next_crawl})


def search(request):
    """
    Search publications with BM25 ranking.
    Includes pagination and timing instrumentation.
    """
    from core.cache import get_search_index, get_index_load_time
    
    query_string = (request.GET.get("q") or "").strip()
    enable_stemming = request.GET.get("stem") != "0"  # Default to enabled
    page_number = request.GET.get("page", 1)
    
    # Load cached index
    index_payload = get_search_index()
    
    search_results = []
    query_time = 0.0
    
    if query_string and index_payload:
        start = time.perf_counter()
        # Get more results internally for pagination
        search_results = execute_search_query(
            query_string, 
            index_payload, 
            top_k=100,  # Get more for pagination
            use_stemming=enable_stemming
        )
        query_time = time.perf_counter() - start
        logger.info(f"Search '{query_string}' returned {len(search_results)} results in {query_time:.3f}s")
    
    # Paginate results
    paginator = Paginator(search_results, RESULTS_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    
    template_context = {
        "q": query_string,
        "results": page_obj,
        "page_obj": page_obj,
        "use_stemming": enable_stemming,
        "has_index": bool(index_payload),
        "total_results": len(search_results),
        "query_time_ms": round(query_time * 1000, 2),
        "index_load_time_ms": round(get_index_load_time() * 1000, 2),
    }
    return render(request, "results.html", template_context)


def classify(request):
    """
    Naive Bayes text classification (rubric coverage).
    Uses cached model for performance.
    """
    from core.cache import get_classifier_model
    
    input_text = ""
    predicted_category = None
    confidence_score = None
    
    model = get_classifier_model()
    is_model_available = model is not None
    
    if request.method == "POST":
        input_text = (request.POST.get("text") or "").strip()
        if input_text and model:
            try:
                probas = model.predict_proba([input_text])[0]
                max_index = probas.argmax()
                predicted_category = str(model.classes_[max_index])
                confidence_score = f"{probas[max_index] * 100:.1f}%"
            except Exception as e:
                logger.error(f"Classification error: {e}")
    
    template_context = {
        "input_text": input_text,
        "predicted_category": predicted_category,
        "confidence_score": confidence_score,
        "model_ready": is_model_available,
    }
    return render(request, "classify.html", template_context)



