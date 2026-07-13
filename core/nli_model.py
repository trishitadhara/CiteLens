"""
NLI-based claim-abstract entailment model.
Uses cross-encoder/nli-deberta-v3-small — fast, accurate, free.

Verdict categories:
  supported     — abstract clearly supports the claim
  partial       — abstract is related but only partially supports
  unsupported   — abstract contradicts or is unrelated
  uncertain     — confidence below threshold, triggers Reflexion retry
"""
from functools import lru_cache
from typing import Dict
from sentence_transformers import CrossEncoder
from config import cfg

LABEL_MAP = {
    "entailment": "supported",
    "neutral": "partial",
    "contradiction": "unsupported",
}


_MODEL = None

def _load_model():
    global _MODEL
    if _MODEL is None:
        print("[NLI] loading cross-encoder model...")
        _MODEL = CrossEncoder("cross-encoder/nli-deberta-v3-small")
    return _MODEL

def check_entailment(claim: str, abstract: str) -> Dict:
    """
    Returns:
      verdict: supported | partial | unsupported | uncertain
      confidence: float 0-1
      scores: raw {entailment, neutral, contradiction}
    """
    model = _load_model()
    scores = model.predict(
        [(claim, abstract[:1024])],
        apply_softmax=True,
    )[0]

    label_names = ["contradiction", "entailment", "neutral"]
    score_dict = dict(zip(label_names, scores.tolist()))
    top_label = max(score_dict, key=score_dict.get)
    confidence = score_dict[top_label]

    verdict = LABEL_MAP.get(top_label, "uncertain")

    # Mark uncertain if confidence too low — triggers Reflexion
    if confidence < cfg.VERIFIER_THRESHOLD:
        verdict = "uncertain"

    return {
        "verdict": verdict,
        "confidence": round(confidence, 3),
        "scores": {k: round(v, 3) for k, v in score_dict.items()},
    }
