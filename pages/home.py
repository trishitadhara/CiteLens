import streamlit as st


def render():
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="padding: 3rem 0 2rem 0; text-align: center;">
    <h1 style="font-size: 3rem; font-weight: 700; margin-bottom: 0.5rem;">
        CiteLens
    </h1>
    <p style="font-size: 1.3rem; color: #888; margin-bottom: 0.5rem;">
        Find the right papers. Verify every claim.
    </p>
    <p style="font-size: 1rem; color: #666; max-width: 600px; margin: 0 auto 2rem auto; line-height: 1.6;">
        CiteLens helps researchers find missing citations and catch incorrect or 
        non-existent references — before submission.
    </p>
</div>
""", unsafe_allow_html=True)

    # ── Two feature cards ─────────────────────────────────────────────────────
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
<div style="border: 1px solid #333; border-radius: 12px; padding: 1.5rem; height: 100%;">
    <div style="font-size: 2rem; margin-bottom: 0.75rem;">🔍</div>
    <h3 style="margin-bottom: 0.5rem;">CiteFind</h3>
    <p style="color: #888; font-size: 0.95rem; line-height: 1.6;">
        Paste your abstract or paper idea. CiteLens understands your research topic,
        searches Semantic Scholar and arXiv, and returns the most relevant papers
        to cite — ranked by relevance, not by search order.
    </p>
    <ul style="color: #aaa; font-size: 0.9rem; margin-top: 1rem; padding-left: 1.2rem;">
        <li>Globally ranked by semantic relevance</li>
        <li>Iterative refinement — keep searching until you find what you need</li>
        <li>Smart suggestions when results miss the mark</li>
        <li>Each paper tagged with why it was retrieved</li>
        <li>Searches Semantic Scholar + arXiv</li>
    </ul>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
<div style="border: 1px solid #333; border-radius: 12px; padding: 1.5rem; height: 100%;">
    <div style="font-size: 2rem; margin-bottom: 0.75rem;">✓</div>
    <h3 style="margin-bottom: 0.5rem;">CiteCheck</h3>
    <p style="color: #888; font-size: 0.95rem; line-height: 1.6;">
        Upload your paper or paste your reference list. CiteLens checks whether 
        each cited paper exists and the metadata is correct — catching hallucinated 
        or mis-attributed citations before they reach a reviewer.
    </p>
    <ul style="color: #aaa; font-size: 0.9rem; margin-top: 1rem; padding-left: 1.2rem;">
        <li>Existence and metadata verification</li>
        <li>Supports BibTeX, numbered lists, APA, MLA</li>
        <li>PDF upload and full text paste</li>
        <li>CrossRef + Semantic Scholar lookup</li>
        <li style="color: #666;">🔬 Claim-level verification — coming soon</li>
    </ul>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### How it works")

    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.markdown("**1. Paste your abstract**")
        st.caption(
            "Drop in your abstract, introduction, or even just a topic description. "
            "CiteLens understands what your paper is about."
        )
    with w2:
        st.markdown("**2. Get ranked suggestions**")
        st.caption(
            "Results are ranked globally by semantic relevance — "
            "most relevant paper always appears first, regardless of which query found it."
        )
    with w3:
        st.markdown("**3. Refine iteratively**")
        st.caption(
            "Not finding what you need? CiteLens generates smart, topic-specific "
            "suggestions — not generic ones. One click refines the search."
        )
    with w4:
        st.markdown("**4. Verify your bibliography**")
        st.caption(
            "Paste your final reference list into CiteCheck. "
            "Catch any papers that don't exist or have wrong metadata before submission."
        )

    st.divider()

    # ── How CiteLens is different ─────────────────────────────────────────────
    st.markdown("### How CiteLens is different")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**vs Google Scholar**")
        st.caption(
            "Google Scholar gives you a flat list of related papers. "
            "CiteLens understands your research topic and ranks results "
            "by how relevant they are to your specific paper."
        )
    with c2:
        st.markdown("**vs CiteTrue and similar**")
        st.caption(
            "Existing tools only check if a paper exists. "
            "CiteLens verifies metadata across Semantic Scholar and CrossRef, "
            "with claim-level verification coming soon."
        )
    with c3:
        st.markdown("**vs ChatGPT**")
        st.caption(
            "LLMs confidently hallucinate citations. CiteLens only returns "
            "papers that actually exist, with direct links to verify. "
            "No fabrication, no guessing."
        )

    st.divider()

    # ── Quick start ───────────────────────────────────────────────────────────
    st.markdown("### Get started")
    q1, q2 = st.columns(2)
    with q1:
        st.markdown("**Writing a new paper?**")
        st.caption(
            "Go to CiteFind → paste your abstract → get ranked citation suggestions. "
            "Refine until you find exactly what you need."
        )
        if st.button("Open CiteFind →", key="home_citefind", use_container_width=True):
            st.session_state["nav"] = "CiteFind"
            st.rerun()
    with q2:
        st.markdown("**Checking an existing paper?**")
        st.caption(
            "Go to CiteCheck → paste your BibTeX, numbered list, or upload a PDF. "
            "We verify every reference against Semantic Scholar and CrossRef."
        )
        if st.button("Open CiteCheck →", key="home_citecheck", use_container_width=True):
            st.session_state["nav"] = "CiteCheck"
            st.rerun()

    # ── Sources ───────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Sources")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("**Currently searching:**")
        st.markdown("- **Semantic Scholar** — 200M+ papers across all fields")
        st.markdown("- **arXiv** — preprints in ML, CS, physics, math")
        st.markdown("- **CrossRef** — broad coverage for IEEE, ACM, Springer")
    with s2:
        st.markdown("**Coming soon:**")
        st.markdown("- OpenReview — NeurIPS, ICLR, ICML submissions")
        st.markdown("- IEEE Xplore — engineering and systems papers")
        st.markdown("- PubMed — biomedical literature")
        st.markdown("- Springer / Nature")