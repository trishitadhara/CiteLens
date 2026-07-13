import time
import streamlit as st
from memory.session_store import append_to_session, save_paper
from memory.qdrant_store import store_paper

EXAMPLE_ABSTRACTS = {
    "Prompt sensitivity in LLMs": (
        "Large language models are highly sensitive to how prompts are phrased — "
        "semantically equivalent inputs can produce outputs that differ substantially "
        "in accuracy and reasoning quality. We study this sensitivity across multiple "
        "instruction-tuned models on reasoning and classification benchmarks, and propose "
        "a robustness evaluation framework. We find that chain-of-thought prompting "
        "significantly reduces output variance compared to zero-shot and few-shot approaches, "
        "and that smaller models are disproportionately affected by surface-level prompt changes."
    ),
    "Explainable AI for medical imaging": (
        "Black-box deep learning models have shown strong diagnostic performance on medical "
        "images but lack the interpretability required for clinical adoption. We propose a "
        "framework combining convolutional neural networks with gradient-based saliency methods "
        "to produce visual explanations for chest X-ray diagnosis. Our approach highlights "
        "clinically relevant regions for conditions including pneumonia and pleural effusion, "
        "and we evaluate whether these explanations align with radiologist judgment through "
        "a structured user study."
    ),
    "Hallucination in RAG systems": (
        "Retrieval-augmented generation improves factual grounding in language models but does "
        "not eliminate hallucination — models frequently ignore retrieved evidence or blend it "
        "with memorized misinformation. We analyze failure modes across multiple RAG architectures "
        "and propose a post-hoc verification approach using natural language inference to detect "
        "when generated claims are unsupported by the retrieved context. Our method improves "
        "faithfulness on open-domain question answering without requiring model retraining."
    ),
}


def _run_search(context: str, refinement: str = "") -> dict:
    start = time.time()
    full_query = context
    if refinement.strip():
        full_query = context + "\n\nAdditional focus: " + refinement.strip()

    status = st.empty()
    progress = st.progress(0)

    status.caption("Understanding your paper topic...")
    progress.progress(15)

    from agents.claim_extractor import extract_claims
    claims = extract_claims(full_query)

    if not claims:
        status.empty()
        progress.empty()
        return {"error": "Could not extract search queries.", "papers": [], "groups": []}

    status.caption(f"Searching across {len(claims)} topic(s)...")
    progress.progress(45)

    from agents.search_agent import search_for_claims
    search_results = search_for_claims(claims, full_query, user_id="demo_user")
    total_papers = sum(len(v) for v in search_results.values())

    status.caption("Ranking results by relevance...")
    progress.progress(80)

    from agents.synthesizer import synthesize_suggestions
    groups = synthesize_suggestions(claims, search_results, full_query)

    # Flat list is returned as single group
    flat_papers = groups[0]["papers"] if groups else []

    status.caption("Generating smart suggestions...")
    progress.progress(90)

    from agents.refiner import generate_refinements
    previous_refinements = st.session_state.get("citefind_refinements_used", [])
    suggestions = generate_refinements(context, groups, previous_refinements)

    from eval.mlflow_logger import log_citefind_run
    elapsed = round(time.time() - start, 2)
    log_citefind_run(
        abstract=full_query[:300],
        n_claims=len(claims),
        n_papers=total_papers,
        n_groups=len(flat_papers),
        latency=elapsed,
    )

    progress.progress(100)
    status.empty()
    progress.empty()

    return {
        "papers": flat_papers,
        "groups": groups,
        "claims": claims,
        "total_papers": total_papers,
        "latency_s": elapsed,
        "refinement": refinement,
        "suggestions": suggestions,
    }


def _render_results(result: dict, round_num: int):
    if "error" in result and not result.get("papers"):
        st.error(result["error"])
        return

    papers = result.get("papers", [])
    if not papers:
        st.warning("No relevant papers found. Try one of the suggestions below.")
        return

    # Stats row
    c1, c2, c3 = st.columns(3)
    c1.metric("Papers found", len(papers))
    c2.metric("Topics searched", len(result.get("claims", [])))
    c3.metric("Time", f"{result['latency_s']}s")

    st.divider()

    # Flat ranked list
    for i, paper in enumerate(papers):
        _render_paper_card(paper, i, round_num)


def _render_paper_card(paper: dict, idx: int, round_num: int):
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            title = paper.get("title", "Unknown title")
            authors = paper.get("authors", [])
            year = paper.get("year", "?")
            venue = paper.get("venue", "")
            citations = paper.get("citation_count", 0)
            score = paper.get("relevance_score", 0)
            from_memory = paper.get("from_memory", False)
            found_via = paper.get("found_via", "")

            author_str = ", ".join(authors[:3])
            if len(authors) > 3:
                author_str += " et al."

            st.markdown(f"**{title}**")

            meta_parts = [p for p in [author_str, str(year), venue] if p and p != "?"]
            meta = " · ".join(meta_parts)
            if citations:
                meta += f" · {citations:,} citations"
            meta += f" · relevance: {score:.2f}"
            if from_memory:
                meta += " · 📚 from your library"
            st.caption(meta)

            # Found via tag
            if found_via:
                st.caption(f"🔍 Found via: _{found_via}_")

            note = paper.get("relevance_note", "")
            if note:
                st.caption(f"_{note}_")

            doi = paper.get("doi", "")
            pdf = paper.get("pdf_url", "")
            ss_id = paper.get("paper_id", "")
            links = []
            if doi:
                links.append(f"[DOI](https://doi.org/{doi})")
            if pdf:
                links.append(f"[PDF]({pdf})")
            if ss_id and paper.get("source") == "semantic_scholar":
                links.append(
                    f"[Semantic Scholar](https://www.semanticscholar.org/paper/{ss_id})"
                )
            if links:
                st.markdown(" · ".join(links))

        with col2:
            btn_key = f"save_{round_num}_{hash(title + str(idx))}"
            if st.button("Save", key=btn_key):
                save_paper(paper, found_via)
                store_paper(paper, "demo_user", found_via)
                st.success("Saved!")

        st.markdown("---")


def render():
    st.title("CiteFind")
    st.caption("Paste your abstract — get citation suggestions ranked by relevance.")

    col1, col2 = st.columns([3, 1])
    with col2:
        st.caption("Load example:")
        for label, abstract in EXAMPLE_ABSTRACTS.items():
            if st.button(label, key=f"ex_{label}", use_container_width=True):
                st.session_state["citefind_abstract"] = abstract
                st.session_state["citefind_history"] = []
                st.session_state["citefind_refinements_used"] = []
                st.rerun()

    with col1:
        abstract = st.text_area(
            "Your abstract or paper topic",
            value=st.session_state.get("citefind_abstract", ""),
            height=160,
            placeholder="Paste your abstract, or type a title/topic for a quick search...",
            label_visibility="collapsed",
            key="abstract_input",
        )
        if abstract:
            wc = len(abstract.split())
            if wc < 30:
                st.caption(f"💡 {wc} words — will search directly. Paste a full abstract for better results.")
            elif wc < 100:
                st.caption(f"💡 {wc} words — adding more context will improve results.")
            else:
                st.caption(f"✓ {wc} words")

    search = st.button("Find citations", type="primary")

    if "citefind_history" not in st.session_state:
        st.session_state["citefind_history"] = []
    if "citefind_refinements_used" not in st.session_state:
        st.session_state["citefind_refinements_used"] = []

    if search and abstract.strip():
        st.session_state["citefind_abstract"] = abstract
        st.session_state["citefind_history"] = []
        st.session_state["citefind_refinements_used"] = []
        result = _run_search(abstract)
        st.session_state["citefind_history"].append({
            "round": 1,
            "refinement": "",
            "result": result,
        })

    history = st.session_state.get("citefind_history", [])

    for entry in history:
        round_num = entry["round"]
        refinement = entry["refinement"]
        result = entry["result"]

        if round_num == 1:
            st.subheader("Results — ranked by relevance")
        else:
            st.subheader(f"Refined results — round {round_num}")
            if refinement:
                st.caption(f"Additional focus: _{refinement}_")

        _render_results(result, round_num)

    # Refinement section
    if not history:
        return

    last_result = history[-1]["result"]
    has_papers = bool(last_result.get("papers"))
    suggestions = last_result.get("suggestions", [])

    st.divider()
    st.markdown("#### Not finding what you need?")

    if suggestions:
        st.caption("CiteLens suggests:")
        sug_cols = st.columns(min(len(suggestions), 2))
        for i, suggestion in enumerate(suggestions):
            col = sug_cols[i % 2]
            if col.button(
                f"🔎 {suggestion}",
                key=f"sug_{i}_{hash(suggestion)}",
                use_container_width=True,
            ):
                st.session_state["refinement_input"] = suggestion

    st.caption("Or describe what you're looking for:")
    refinement = st.text_input(
        "Add context",
        value=st.session_state.pop("refinement_input", ""),
        placeholder="e.g. 'DFST dynamic few-shot trojaning' or 'find pruning-based defenses'",
        label_visibility="collapsed",
        key="refinement_text",
    )

    refine_col, reset_col = st.columns([4, 1])
    with refine_col:
        refine_btn = st.button(
            "Search with this focus", type="primary", use_container_width=True
        )
    with reset_col:
        if st.button("Start over", use_container_width=True, key="start_over"):
            st.session_state["citefind_history"] = []
            st.session_state["citefind_abstract"] = ""
            st.session_state["citefind_refinements_used"] = []
            st.rerun()

    if refine_btn and refinement.strip():
        original_abstract = st.session_state.get("citefind_abstract", "")
        round_num = len(history) + 1
        used = st.session_state.get("citefind_refinements_used", [])
        used.append(refinement)
        st.session_state["citefind_refinements_used"] = used
        result = _run_search(original_abstract, refinement)
        st.session_state["citefind_history"].append({
            "round": round_num,
            "refinement": refinement,
            "result": result,
        })
        st.rerun()

    append_to_session({
        "abstract": st.session_state.get("citefind_abstract", "")[:100],
        "rounds": len(history),
    })