"""
Mem0 integration for summarization and forgetting policies.
JD point 4: summarization, compression, forgetting policies.
Falls back to no-op if Mem0 unavailable.
"""
from config import cfg
from typing import List, Dict

try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = bool(cfg.MEM0_API_KEY)
except ImportError:
    MEM0_AVAILABLE = False


def _client():
    if not MEM0_AVAILABLE:
        return None
    return MemoryClient(api_key=cfg.MEM0_API_KEY)


def store_search_summary(user_id: str, abstract: str, top_papers: List[Dict]):
    """Summarise a CiteFind session into Mem0 for long-term recall."""
    client = _client()
    if not client:
        return
    summary = (
        f"User searched for citations for: {abstract[:200]}. "
        f"Top papers found: {', '.join(p['title'] for p in top_papers[:3])}"
    )
    try:
        client.add(summary, user_id=user_id)
    except Exception as e:
        print(f"[Mem0] store failed: {e}")


def recall_past_searches(user_id: str, query: str) -> List[str]:
    """Retrieve past search summaries relevant to query."""
    client = _client()
    if not client:
        return []
    try:
        results = client.search(query, user_id=user_id, limit=3)
        return [r["memory"] for r in results]
    except Exception:
        return []


def forget_user(user_id: str):
    """Privacy: delete all Mem0 entries for user."""
    client = _client()
    if not client:
        return
    try:
        client.delete_all(user_id=user_id)
    except Exception as e:
        print(f"[Mem0] forget failed: {e}")
