"""
Agent 1 — Claim Extractor (semantic understanding version).
Generates dynamic number of search queries based on input length.
"""
import json
import re
from typing import List, Dict
from config import cfg


def extract_claims(text: str) -> List[Dict]:
    word_count = len(text.strip().split())
    
    # Short input — use directly as search query, no LLM needed
    if word_count <= 30:
        return [{"claim": text.strip(), "type": "direct search"}]
    
    # Full abstract — use LLM to extract semantic queries
    return _extract_openai(text)


def _extract_openai(text: str) -> List[Dict]:
    from openai import OpenAI
    client = OpenAI(api_key=cfg.OPENAI_API_KEY)

    prompt = _build_prompt(text)
    resp = client.chat.completions.create(
        model=cfg.OPENAI_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a research librarian helping a researcher find papers to cite. "
                    "You deeply understand academic literature and know how to search for relevant work. "
                    "Always return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=400,
    )
    return _parse_response(resp.choices[0].message.content)


def _build_prompt(text: str) -> str:
    word_count = len(text.split())

    if word_count < 50:
        n_min, n_max = 1, 2
    elif word_count < 150:
        n_min, n_max = 2, 3
    else:
        n_min, n_max = 3, 5

    instruction = f"Generate between {n_min} and {n_max} search queries"

    prompt = (
        "A researcher has written this text. " + instruction + " to find "
        "the most relevant papers they should cite.\n\n"
        "Think like a senior researcher doing a literature review:\n"
        "- What is the core problem this paper addresses?\n"
        "- What methods or techniques does it use or build upon?\n"
        "- What prior work would reviewers expect to see cited?\n\n"
        "Each query should be:\n"
        "- A specific research concept or method name (NOT a literal phrase from the text)\n"
        "- Specific enough to find relevant papers (not generic like 'deep learning')\n"
        "- Something a researcher would actually type into Google Scholar\n\n"
        "WRONG (too literal, contains metrics, too generic):\n"
        "- 'AUC above 0.91 classification'\n"
        "- 'deep learning framework'\n"
        "- 'dataset benchmark evaluation'\n\n"
        "RIGHT (specific research concepts):\n"
        "- 'Grad-CAM visual explanation convolutional networks'\n"
        "- 'chest X-ray pneumonia detection deep learning'\n"
        "- 'clinical interpretability saliency maps medical imaging'\n\n"
        "Text:\n"
        + text[:1200]
        + "\n\nReturn ONLY a JSON array:\n"
        "[\n"
        '  {"query": "specific search query here", "reason": "one sentence why this is relevant to cite"},\n'
        "  ...\n"
        "]"
    )
    return prompt


def _parse_response(raw: str) -> List[Dict]:
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            results = []
            for item in parsed:
                if isinstance(item, dict):
                    query = item.get("query") or item.get("claim", "")
                    reason = item.get("reason") or item.get("type", "")
                    if query:
                        results.append({
                            "claim": query,
                            "type": reason,
                        })
            return results[:5]
    except Exception:
        pass

    # Fallback: extract JSON array substring
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            return [
                {
                    "claim": i.get("query") or i.get("claim", ""),
                    "type": i.get("reason", ""),
                }
                for i in parsed if isinstance(i, dict)
            ][:5]
        except Exception:
            pass

    return [{"claim": raw[:100], "type": "related work"}]