"""
Semantic Scholar API wrapper.
Free, no key needed for basic usage (<100 req/5min).
"""
import httpx
import time
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,authors,year,abstract,citationCount,externalIds,openAccessPdf,venue"


def search_papers(query: str, limit: int = 6) -> List[Dict]:
    """Search papers. Returns empty list on rate limit — caller falls back to arXiv."""
    try:
        resp = httpx.get(
            f"{BASE_URL}/paper/search",
            params={"query": query, "limit": limit, "fields": FIELDS},
            timeout=15,
        )
        if resp.status_code == 429:
            print(f"[SemanticScholar] rate limited for '{query}' — falling back to arXiv")
            return []
        resp.raise_for_status()
        data = resp.json()
        papers = data.get("data", [])
        return [_normalise(p) for p in papers if p.get("abstract")]
    except Exception as e:
        print(f"[SemanticScholar] search failed for '{query}': {e}")
        return []


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def lookup_by_doi(doi: str) -> Optional[Dict]:
    """Look up a specific paper by DOI. Returns None if not found."""
    try:
        resp = httpx.get(
            f"{BASE_URL}/paper/DOI:{doi}",
            params={"fields": FIELDS},
            timeout=15,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _normalise(resp.json())
    except Exception as e:
        print(f"[SemanticScholar] DOI lookup failed for '{doi}': {e}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def lookup_by_title(title: str) -> Optional[Dict]:
    """Title lookup — returns only if title similarity is high AND abstract exists."""
    results = search_papers(title, limit=5)
    if not results:
        return None
    
    # Find best match by title similarity
    best = None
    best_score = 0
    for r in results:
        if not r.get("abstract"):
            continue  # skip papers without abstracts
        score = _title_overlap(title, r["title"])
        if score > best_score:
            best_score = score
            best = r
    
    # Only return if similarity is reasonable
    if best and best_score >= 0.4:
        return best
    
    # If nothing with abstract found, return best match regardless
    for r in results:
        score = _title_overlap(title, r["title"])
        if score >= 0.5:
            return r
    
    return None


def _title_overlap(a: str, b: str) -> float:
    """Word overlap score between two titles."""
    stops = {"a", "an", "the", "of", "in", "on", "for", "and", "or", "to", "with"}
    a_words = set(re.sub(r"[^\w\s]", "", a.lower()).split()) - stops
    b_words = set(re.sub(r"[^\w\s]", "", b.lower()).split()) - stops
    if not a_words:
        return 0
    return len(a_words & b_words) / len(a_words)


def _normalise(p: Dict) -> Dict:
    authors = [a.get("name", "") for a in p.get("authors", [])]
    doi = (p.get("externalIds") or {}).get("DOI", "")
    pdf_url = (p.get("openAccessPdf") or {}).get("url", "")
    return {
        "title": p.get("title", ""),
        "authors": authors,
        "year": p.get("year"),
        "abstract": p.get("abstract", ""),
        "citation_count": p.get("citationCount", 0),
        "venue": p.get("venue", ""),
        "doi": doi,
        "pdf_url": pdf_url,
        "source": "semantic_scholar",
        "paper_id": p.get("paperId", ""),
    }
