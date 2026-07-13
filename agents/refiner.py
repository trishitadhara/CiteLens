"""
Refinement suggestion generator.
After results come back, analyzes what was found and what was missed,
then generates topic-specific follow-up suggestions the user can click.
"""
import json
import re
from typing import List, Dict
from config import cfg


def generate_refinements(
    original_input: str,
    groups: List[Dict],
    previous_refinements: List[str] = [],
) -> List[str]:
    """
    Given the original input and what was found so far,
    generate 3-4 specific, intelligent follow-up search suggestions.
    Returns a list of suggestion strings.
    """
    from openai import OpenAI
    client = OpenAI(api_key=cfg.OPENAI_API_KEY)

    # Summarise what was found
    found_titles = []
    for group in groups:
        for paper in group.get("papers", [])[:2]:
            found_titles.append(paper.get("title", ""))

    found_summary = (
        "Papers found so far: " + "; ".join(found_titles[:6])
        if found_titles
        else "No papers found yet."
    )

    prev_summary = (
        "Previous refinements tried: " + "; ".join(previous_refinements)
        if previous_refinements
        else ""
    )

    prompt = (
        "A researcher is looking for papers to cite. Based on their input and "
        "what has been found so far, generate 3 or 4 specific follow-up search "
        "suggestions they could use to find more relevant papers.\n\n"
        "Rules:\n"
        "- Each suggestion must be specific to THIS topic — not generic\n"
        "- Suggest specific paper names, methods, or subtopics the user might want\n"
        "- Think: what related work might they have missed? What specific methods "
        "or datasets are relevant here?\n"
        "- Keep each suggestion short (under 10 words) — it will appear as a button\n"
        "- Do NOT suggest things already found or already tried\n\n"
        "WRONG (too generic):\n"
        "- 'Find more recent papers'\n"
        "- 'Focus on a specific method'\n"
        "- 'Search for survey papers'\n\n"
        "RIGHT (specific to the topic):\n"
        "For backdoor attacks: 'DFST dynamic few-shot trojaning attacks'\n"
        "For backdoor attacks: 'frequency domain invisible backdoor attacks'\n"
        "For backdoor attacks: 'ANP adversarial neuron pruning defense'\n\n"
        f"Researcher input: {original_input}\n\n"
        f"{found_summary}\n"
        f"{prev_summary}\n\n"
        "Return ONLY a JSON array of strings:\n"
        '["suggestion 1", "suggestion 2", "suggestion 3"]'
    )

    try:
        resp = client.chat.completions.create(
            model=cfg.OPENAI_MODEL,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You are a research librarian suggesting specific search queries. Return valid JSON only."
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        raw = re.sub(r"```(?:json)?", "", resp.choices[0].message.content).strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [s for s in parsed if isinstance(s, str)][:4]
    except Exception as e:
        print(f"[Refiner] failed: {e}")

    # Fallback generic suggestions
    return [
        "Find survey papers on this topic",
        "Search for more recent work (2023-2024)",
        "Find baseline or comparison methods",
    ]