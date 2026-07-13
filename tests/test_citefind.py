"""
Unit tests for CiteFind pipeline components.
"""
import pytest


def test_claim_extraction_returns_list():
    from agents.claim_extractor import extract_claims
    abstract = "We propose a backdoor defense using lottery ticket hypothesis pruning on CIFAR-10."
    claims = extract_claims(abstract)
    assert isinstance(claims, list)
    assert len(claims) >= 1
    assert all("claim" in c for c in claims)


def test_claim_extraction_short_text():
    from agents.claim_extractor import extract_claims
    claims = extract_claims("attention is all you need")
    assert isinstance(claims, list)


def test_semantic_scholar_search():
    from core.semantic_scholar import search_papers
    results = search_papers("lottery ticket hypothesis pruning", limit=3)
    assert isinstance(results, list)
    if results:
        assert "title" in results[0]
        assert "abstract" in results[0]


def test_arxiv_search():
    from core.arxiv_search import search_arxiv
    results = search_arxiv("backdoor defense neural network", limit=3)
    assert isinstance(results, list)


def test_reranker_deduplicates():
    from core.reranker import rerank
    papers = [
        {"title": "Paper A", "abstract": "About pruning", "citation_count": 0, "venue": "", "doi": "", "pdf_url": "", "paper_id": "", "source": "test", "authors": [], "year": 2020},
        {"title": "Paper A", "abstract": "About pruning", "citation_count": 0, "venue": "", "doi": "", "pdf_url": "", "paper_id": "", "source": "test", "authors": [], "year": 2020},
        {"title": "Paper B", "abstract": "About backdoors", "citation_count": 0, "venue": "", "doi": "", "pdf_url": "", "paper_id": "", "source": "test", "authors": [], "year": 2021},
    ]
    ranked = rerank("pruning defense", papers, top_k=5)
    titles = [p["title"] for p in ranked]
    assert len(titles) == len(set(titles)), "Duplicates not removed"


def test_nli_returns_valid_verdict():
    from core.nli_model import check_entailment
    result = check_entailment(
        "Pruning reduces model accuracy",
        "We show that magnitude pruning significantly reduces clean accuracy on CIFAR-10."
    )
    assert result["verdict"] in ["supported", "partial", "unsupported", "uncertain"]
    assert 0.0 <= result["confidence"] <= 1.0
