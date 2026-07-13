"""
Agent 2 — Search Agent.
For each search query, searches Semantic Scholar + arXiv sequentially.
Checks Qdrant memory first. Reranks by semantic similarity to full abstract.
"""
import time
from typing import List, Dict
from core.semantic_scholar import search_papers
from core.arxiv_search import search_arxiv
from core.reranker import rerank
from config import cfg


def search_for_claims(
    claims: List[Dict],
    user_abstract: str,
    user_id: str = "anonymous",
) -> Dict[str, List[Dict]]:
    """
    Sequential search per query — avoids rate limits and torch segfaults.
    Returns dict mapping query -> ranked papers.
    """
    results = {}

    for claim_dict in claims:
        query = claim_dict["claim"]
        reason = claim_dict.get("type", "")
        if not query:
            continue

        try:
            papers = _search_one_query(query, reason, user_abstract, user_id)
            results[query] = papers
            # Respect Semantic Scholar rate limit
            time.sleep(1.2)
        except Exception as e:
            print(f"[SearchAgent] failed for '{query}': {e}")
            results[query] = []

    return results


def _search_one_query(
    query: str,
    reason: str,
    user_abstract: str,
    user_id: str,
) -> List[Dict]:
    """Search one query across memory + SS + arXiv, rerank against full abstract."""

    # 1. Check long-term memory first
    memory_papers = _check_memory(query, user_id)

    # 2. Semantic Scholar — primary source
    ss_papers = search_papers(query, limit=6)

    # Small delay between SS and arXiv
    time.sleep(0.3)

    # 3. arXiv — good for recent/preprint work
    ax_papers = search_arxiv(query, limit=3)

    # 4. Combine — memory first for personalisation
    all_papers = memory_papers + ss_papers + ax_papers

    if not all_papers:
        return []

    # 5. Rerank using full abstract as query (not just the search term)
    # This is the key quality improvement — rerank against what the paper is ABOUT
    ranked = rerank(user_abstract, all_papers, top_k=cfg.TOP_K_PAPERS)

    # Tag memory hits
    memory_titles = {p["title"].lower() for p in memory_papers}
    for p in ranked:
        p["from_memory"] = p["title"].lower() in memory_titles

    return ranked


def _check_memory(query: str, user_id: str) -> List[Dict]:
    try:
        from memory.qdrant_store import recall_similar
        return recall_similar(query, user_id, top_k=2)
    except Exception:
        return []