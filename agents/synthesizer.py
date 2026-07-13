"""
Agent 4 — Synthesizer (fast, no LLM call).
Returns a single flat list of papers sorted by relevance score globally.
Each paper tagged with which query found it and why.
No grouping — most relevant paper always appears first.
"""
from typing import Dict, List

RELEVANCE_THRESHOLD = 0.35


def synthesize_suggestions(
    claims: List[Dict],
    search_results: Dict[str, List],
    user_abstract: str,
) -> List[Dict]:
    """
    Returns one flat sorted list instead of groups.
    Each paper has a 'found_via' tag showing which query retrieved it.
    """
    seen_titles = set()
    all_papers = []

    for claim_dict in claims:
        query = claim_dict["claim"]
        reason = claim_dict.get("type", "")
        papers = search_results.get(query, [])

        for p in papers:
            title_key = p.get("title", "").lower().strip()
            if not title_key or title_key in seen_titles:
                continue
            if p.get("relevance_score", 0) < RELEVANCE_THRESHOLD:
                continue

            seen_titles.add(title_key)

            # Abstract snippet
            abstract = p.get("abstract", "")
            sentences = abstract.split(". ")
            snippet = ". ".join(sentences[:2]).strip()
            if len(snippet) > 180:
                snippet = snippet[:180] + "..."

            all_papers.append({
                **p,
                "relevance_note": snippet or "",
                "found_via": query,
                "found_reason": reason,
            })

    # Sort globally by relevance score
    all_papers = sorted(
        all_papers,
        key=lambda x: x.get("relevance_score", 0),
        reverse=True,
    )

    # Return as a single group so citefind.py doesn't need big changes
    if not all_papers:
        return []

    return [{
        "claim": "All suggestions — ranked by relevance",
        "claim_type": f"{len(all_papers)} papers found",
        "papers": all_papers,
        "flat": True,
    }]