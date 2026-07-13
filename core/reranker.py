"""
Reranks retrieved papers using semantic similarity between
user's abstract and each candidate paper's abstract.
Uses sentence-transformers all-mpnet-base-v2.
"""
from functools import lru_cache
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import numpy as np

# Load once at module level — not per thread
_MODEL = None

def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-mpnet-base-v2")
    return _MODEL

@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer("all-mpnet-base-v2")


def rerank(query_text: str, papers: List[Dict], top_k: int = 8) -> List[Dict]:
    """
    Reranks papers by cosine similarity between query_text and each abstract.
    Adds 'relevance_score' to each paper dict.
    Deduplicates by title before ranking.
    """
    if not papers:
        return []

    model = _get_model()

    # Deduplicate by title (case-insensitive)
    seen_titles = set()
    unique_papers = []
    for p in papers:
        key = p["title"].lower().strip()
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique_papers.append(p)

    # Encode
    query_emb = model.encode(query_text, normalize_embeddings=True)
    abstracts = [p.get("abstract", "") or p["title"] for p in unique_papers]
    paper_embs = model.encode(abstracts, normalize_embeddings=True, batch_size=16)

    # Cosine similarity
    scores = np.dot(paper_embs, query_emb).tolist()

    for paper, score in zip(unique_papers, scores):
        paper["relevance_score"] = round(float(score), 3)

    ranked = sorted(unique_papers, key=lambda x: x["relevance_score"], reverse=True)
    return ranked[:top_k]
   
