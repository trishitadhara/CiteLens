"""
Agent 3 — Verifier Agent (CiteCheck module).
Checks whether a cited paper actually supports a specific claim.
Implements Reflexion: if confidence < threshold, re-reads and retries.

JD point 3 — self-improving loop via reflection and critique.
"""
from typing import Dict, List
from core.nli_model import check_entailment
from config import cfg
import time


VERDICT_LABELS = {
    "supported": "The paper supports this claim.",
    "partial": "The paper is related but only partially supports this claim.",
    "unsupported": "The paper does not support this claim.",
    "uncertain": "Confidence too low — retrying with focused context.",
}


def verify_citation(
    claim: str,
    paper: Dict,
    full_text_hint: str = "",
) -> Dict:
    """
    Verifies whether paper supports claim.
    Runs Reflexion loop if uncertain.

    Returns:
      verdict: supported | partial | unsupported
      confidence: float
      explanation: str
      reflexion_rounds: int
      scores: raw NLI scores
    """
    abstract = paper.get("abstract", "")
    if not abstract:
        return _no_abstract_result(paper)

    # First pass
    result = check_entailment(claim, abstract)
    reflexion_rounds = 0

    # Reflexion loop — JD point 3
    while result["verdict"] == "uncertain" and reflexion_rounds < cfg.MAX_REFLEXION_RETRIES:
        reflexion_rounds += 1
        refined_context = _refine_context(claim, abstract, full_text_hint, reflexion_rounds)
        result = check_entailment(claim, refined_context)
        time.sleep(0.1)

    # If still uncertain after retries, fall back to partial
    if result["verdict"] == "uncertain":
        result["verdict"] = "partial"

    explanation = _generate_explanation(claim, paper, result)

    return {
        "verdict": result["verdict"],
        "confidence": result["confidence"],
        "scores": result["scores"],
        "explanation": explanation,
        "reflexion_rounds": reflexion_rounds,
        "paper_title": paper.get("title", ""),
        "paper_year": paper.get("year"),
        "paper_authors": paper.get("authors", []),
        "doi": paper.get("doi", ""),
    }


def verify_batch(
    claim: str,
    papers: List[Dict],
) -> List[Dict]:
    """Verify a list of papers against a single claim."""
    return [verify_citation(claim, p) for p in papers]


def _refine_context(
    claim: str, abstract: str, hint: str, round_num: int
) -> str:
    """
    Reflexion critique: focus on the most claim-relevant part of the abstract.
    Round 1: prepend the claim as explicit context.
    Round 2: if hint (methods/results section) is available, use it.
    """
    if round_num == 1:
        return f"Claim to verify: {claim}\n\nAbstract: {abstract}"
    if hint:
        return f"Claim to verify: {claim}\n\nRelevant section: {hint[:800]}"
    # Final fallback: take abstract sentences mentioning key claim terms
    claim_words = set(claim.lower().split())
    sentences = abstract.split(". ")
    relevant = [s for s in sentences if any(w in s.lower() for w in claim_words)]
    return f"Claim: {claim}\n\nMost relevant: {'. '.join(relevant[:3])}"


def _generate_explanation(claim: str, paper: Dict, result: Dict) -> str:
    verdict = result["verdict"]
    confidence = result["confidence"]
    title = paper.get("title", "unknown paper")

    if verdict == "supported":
        return (
            f"'{title}' supports this claim with {confidence:.0%} confidence. "
            f"The abstract aligns with: '{claim[:100]}'"
        )
    elif verdict == "partial":
        return (
            f"'{title}' is related to this claim but only partially supports it "
            f"({confidence:.0%} confidence). Verify the specific finding manually."
        )
    else:
        return (
            f"'{title}' does not appear to support '{claim[:80]}' "
            f"({confidence:.0%} confidence). Consider removing or replacing this citation."
        )


def _no_abstract_result(paper: Dict) -> Dict:
    return {
        "verdict": "uncertain",
        "confidence": 0.0,
        "scores": {},
        "explanation": "No abstract available — manual verification required.",
        "reflexion_rounds": 0,
        "paper_title": paper.get("title", ""),
        "paper_year": paper.get("year"),
        "paper_authors": paper.get("authors", []),
        "doi": paper.get("doi", ""),
    }
