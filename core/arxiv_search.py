"""
arXiv API wrapper — free, no key needed.
Complements Semantic Scholar for preprints.
"""
import arxiv
from typing import List, Dict


def search_arxiv(query: str, limit: int = 6) -> List[Dict]:
    """Search arXiv and return normalised paper dicts."""
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        results = []
        for r in client.results(search):
            results.append({
                "title": r.title,
                "authors": [str(a) for a in r.authors],
                "year": r.published.year if r.published else None,
                "abstract": r.summary,
                "citation_count": 0,
                "venue": "arXiv",
                "doi": r.doi or "",
                "pdf_url": r.pdf_url or "",
                "source": "arxiv",
                "paper_id": r.entry_id,
            })
        return results
    except Exception as e:
        print(f"[arXiv] search failed for '{query}': {e}")
        return []
