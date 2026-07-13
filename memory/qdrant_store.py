"""
Long-term memory — Qdrant Cloud.
JD point 4: long-term memory, retrieval-augmented personalisation,
privacy-aware retention (TTL enforced on insert).
"""
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from functools import lru_cache
from config import cfg

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


@lru_cache(maxsize=1)
def _client() -> Optional[object]:
    if not QDRANT_AVAILABLE or not cfg.QDRANT_URL:
        return None
    try:
        return QdrantClient(url=cfg.QDRANT_URL, api_key=cfg.QDRANT_API_KEY)
    except Exception as e:
        print(f"[Qdrant] connection failed: {e}")
        return None


def _ensure_collection():
    client = _client()
    if not client:
        return
    try:
        client.get_collection(cfg.QDRANT_COLLECTION)
    except Exception:
        client.create_collection(
            collection_name=cfg.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )


def store_paper(paper: Dict, user_id: str, claim: str):
    """
    Store a paper a user cited/saved into their long-term memory.
    TTL enforced via expires_at metadata — JD point 4 retention policy.
    """
    client = _client()
    if not client:
        return

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-mpnet-base-v2")

    text = f"{paper.get('title', '')} {paper.get('abstract', '')[:500]}"
    embedding = model.encode(text, normalize_embeddings=True).tolist()

    expires_at = (datetime.utcnow() + timedelta(days=cfg.MEMORY_TTL_DAYS)).isoformat()
    point_id = hashlib.md5(f"{user_id}:{paper.get('title','')}".encode()).hexdigest()
    point_id_int = int(point_id[:8], 16)

    _ensure_collection()
    client.upsert(
        collection_name=cfg.QDRANT_COLLECTION,
        points=[PointStruct(
            id=point_id_int,
            vector=embedding,
            payload={
                "user_id": user_id,
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "year": paper.get("year"),
                "abstract": paper.get("abstract", "")[:500],
                "doi": paper.get("doi", ""),
                "claim": claim,
                "stored_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at,
            }
        )]
    )


def recall_similar(query: str, user_id: str, top_k: int = 3) -> List[Dict]:
    """
    Retrieve papers similar to query from this user's memory.
    Filters by user_id and enforces TTL check.
    """
    client = _client()
    if not client:
        return []

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-mpnet-base-v2")
        query_emb = model.encode(query, normalize_embeddings=True).tolist()

        results = client.search(
            collection_name=cfg.QDRANT_COLLECTION,
            query_vector=query_emb,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=top_k,
            with_payload=True,
        )

        now = datetime.utcnow().isoformat()
        papers = []
        for r in results:
            payload = r.payload
            # Enforce TTL
            if payload.get("expires_at", "9999") < now:
                continue
            papers.append({
                "title": payload["title"],
                "authors": payload.get("authors", []),
                "year": payload.get("year"),
                "abstract": payload.get("abstract", ""),
                "doi": payload.get("doi", ""),
                "relevance_score": round(r.score, 3),
                "source": "memory",
                "citation_count": 0,
                "venue": "",
                "pdf_url": "",
                "paper_id": "",
            })
        return papers
    except Exception as e:
        print(f"[Qdrant] recall failed: {e}")
        return []


def delete_user_memory(user_id: str):
    """Privacy: delete all papers for a given user."""
    client = _client()
    if not client:
        return
    try:
        client.delete(
            collection_name=cfg.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
        )
    except Exception as e:
        print(f"[Qdrant] delete failed: {e}")
