"""
Regression tests for CiteCheck against the golden set.
JD point 2: end-to-end testing, regression analysis.
Run with: pytest tests/test_citecheck.py -v
"""
import pytest
from eval.golden_set import get_golden_set


@pytest.fixture(scope="module")
def golden_results():
    """Run verifier on full golden set once, reuse across tests."""
    from agents.verifier_agent import verify_citation
    from core.semantic_scholar import lookup_by_doi, lookup_by_title

    results = []
    for item in get_golden_set():
        doi = item.get("doi", "")
        title = item.get("title", "")
        claim = item["claim"]

        paper = None
        if doi:
            paper = lookup_by_doi(doi)
        if not paper and title:
            paper = lookup_by_title(title)

        if not paper:
            verdict = "not_found"
            confidence = 0.0
        else:
            result = verify_citation(claim, paper)
            verdict = result["verdict"]
            confidence = result["confidence"]

        results.append({
            "expected": item["expected_verdict"],
            "actual": verdict,
            "confidence": confidence,
            "claim": claim,
            "title": title,
        })
    return results


def test_overall_accuracy(golden_results):
    correct = sum(1 for r in golden_results if r["actual"] == r["expected"])
    accuracy = correct / len(golden_results)
    print(f"\nAccuracy: {accuracy:.1%} ({correct}/{len(golden_results)})")
    assert accuracy >= 0.70, f"Accuracy {accuracy:.1%} below 70% threshold"


def test_no_supported_papers_flagged_unsupported(golden_results):
    """Supported papers should not be flagged as unsupported."""
    false_negatives = [
        r for r in golden_results
        if r["expected"] == "supported" and r["actual"] == "unsupported"
    ]
    assert len(false_negatives) == 0, (
        f"False negatives (supported→unsupported): {false_negatives}"
    )


def test_unsupported_papers_not_flagged_supported(golden_results):
    """Unsupported papers should not be flagged as supported."""
    false_positives = [
        r for r in golden_results
        if r["expected"] == "unsupported" and r["actual"] == "supported"
    ]
    rate = len(false_positives) / max(1, sum(1 for r in golden_results if r["expected"] == "unsupported"))
    assert rate <= 0.30, f"False positive rate {rate:.1%} exceeds 30%"


def test_confidence_above_threshold(golden_results):
    """Correct predictions should have reasonable confidence."""
    correct = [r for r in golden_results if r["actual"] == r["expected"]]
    avg_conf = sum(r["confidence"] for r in correct) / max(1, len(correct))
    assert avg_conf >= 0.55, f"Average confidence {avg_conf:.2f} below 0.55"
