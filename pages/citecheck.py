"""
CiteCheck — citation metadata verification.
Checks whether cited papers exist and metadata is correct.
Supports: BibTeX, numbered [1], APA, MLA, PDF upload, full text paste.

Claim-level verification (NLI) — coming soon.
"""
import re
import time
import streamlit as st


# ── Text cleaning ─────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    text = re.sub(r"(\w+)-\s{1,3}([a-z])", r"\1\2", text)
    text = re.sub(r" {2,}", " ", text)
    return text


# ── BibTeX parser ─────────────────────────────────────────────────────────────

def _parse_bibtex(text: str) -> list[dict]:
    entries = re.findall(r"@\w+\s*\{[^@]+", text, re.DOTALL)
    parsed = []
    for entry in entries:
        title = _bibtex_field(entry, "title")
        author = _bibtex_field(entry, "author")
        year = _bibtex_field(entry, "year")
        doi = _bibtex_field(entry, "doi")
        journal = (
            _bibtex_field(entry, "journal")
            or _bibtex_field(entry, "booktitle")
            or _bibtex_field(entry, "publisher")
        )
        if not title:
            continue
        authors = []
        if author:
            for p in re.split(r"\s+and\s+", author, flags=re.IGNORECASE):
                authors.append(p.strip().rstrip(","))
        parsed.append({
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "venue": journal,
            "raw": entry[:200].strip(),
            "format": "bibtex",
        })
    return parsed


def _bibtex_field(entry: str, field: str) -> str:
    pattern = rf"{field}\s*=\s*[{{\"](.*?)[}}\"]\s*[,}}]"
    match = re.search(pattern, entry, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().replace("\n", " ").replace("  ", " ")
    return ""


# ── Reference list parser ─────────────────────────────────────────────────────

def _parse_reference_list(text: str) -> list[dict]:
    text = _clean_text(text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    refs = []
    current = []
    for line in lines:
        is_new = (
            bool(re.match(r"^\[?\d+[\]\.]\s", line)) or
            bool(re.match(r"^[A-Z][a-z]+,?\s[A-Z]", line))
        )
        if is_new and current:
            refs.append(" ".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        refs.append(" ".join(current))

    parsed = []
    for raw in refs:
        if len(raw) < 20:
            continue
        parsed.append({
            "title": _extract_title(raw),
            "authors": _extract_authors(raw),
            "year": _extract_year(raw),
            "doi": _extract_doi(raw),
            "venue": "",
            "raw": raw[:300],
            "format": "numbered",
        })
    return [p for p in parsed if p["title"] and len(p["title"]) > 10]


def _extract_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """Extract reference list from PDF and return as citations."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)
        full_text = _clean_text(full_text)
        refs_section = _find_refs_section(full_text)
        if not refs_section:
            return []
        return _parse_reference_list(refs_section)
    except ImportError:
        st.error("Run: pip install pymupdf")
        return []
    except Exception as e:
        st.error(f"PDF parsing error: {e}")
        return []


def _find_refs_section(text: str) -> str:
    for pattern in [
        r"(?i)\n\s*references\s*\n",
        r"(?i)\n\s*bibliography\s*\n",
        r"(?i)\n\s*works cited\s*\n",
    ]:
        match = re.search(pattern, text)
        if match:
            return text[match.start():]
    return ""


def _detect_and_parse(text: str) -> list[dict]:
    text = text.strip()
    if any(k in text for k in ["@article", "@book", "@inproceedings", "@misc", "@phdthesis"]):
        results = _parse_bibtex(text)
        if results:
            return results
    return _parse_reference_list(text)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_title(ref: str) -> str:
    ref = re.sub(r"(\w+)-\s*\n?\s*([a-z])", r"\1\2", ref)
    quoted = re.findall(r'"([^"]{10,120})"', ref)
    if quoted:
        return quoted[0]
    clean = re.sub(r"^\[?\d+[\]\.)\s]\s*", "", ref).strip()
    match = re.search(r"\.\s+([A-Z][^.]{15,150}?)(?:\.|$)", clean)
    if match:
        candidate = match.group(1).strip().rstrip(".")
        if (len(candidate) > 15
                and not re.match(r"^[A-Z][a-z]+,\s", candidate)
                and not re.match(r"^In\s+Proc", candidate, re.IGNORECASE)):
            return candidate
    match = re.search(r"\(\d{4}\)[.,]?\s*(.+?)[\.\?!]", clean)
    if match:
        c = match.group(1).strip()
        if 10 < len(c) < 200:
            return c
    parts = re.split(r"[,;]", clean)
    for p in parts[1:]:
        p = p.strip()
        if 15 < len(p) < 200 and not re.match(r"^\d", p):
            return p
    return clean[:100].strip()


def _extract_authors(ref: str) -> list[str]:
    return re.findall(r"([A-Z][a-z]+(?:,?\s[A-Z]\.?)+)", ref)[:4]


def _extract_year(ref: str) -> str:
    m = re.search(r"\b(19|20)\d{2}\b", ref)
    return m.group() if m else ""


def _extract_doi(ref: str) -> str:
    m = re.search(r"10\.\d{4,}/\S+", ref)
    return m.group().rstrip(".,)") if m else ""


def _title_similar(a: str, b: str) -> bool:
    if not a or not b:
        return False
    stops = {"a", "an", "the", "of", "in", "on", "for", "and", "or", "to", "with", "from"}
    a_words = set(re.sub(r"[^\w\s]", "", a.lower()).split()) - stops
    b_words = set(re.sub(r"[^\w\s]", "", b.lower()).split()) - stops
    if not a_words:
        return False
    return len(a_words & b_words) / len(a_words) >= 0.5


# ── CrossRef fallback ─────────────────────────────────────────────────────────

def _crossref_lookup(title: str, year: str = "") -> dict | None:
    import httpx
    try:
        params = {"query.title": title, "rows": 3, "select": "title,author,published,DOI"}
        resp = httpx.get(
            "https://api.crossref.org/works",
            params=params,
            timeout=10,
            headers={"User-Agent": "CiteLens/1.0 (mailto:research@citelens.app)"},
        )
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
        for item in items:
            cr_title = item.get("title", [""])[0]
            if not _title_similar(title, cr_title):
                continue
            authors = []
            for a in item.get("author", []):
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    authors.append(name)
            pub_year = None
            date_parts = item.get("published", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                pub_year = date_parts[0][0]
            return {
                "title": cr_title,
                "authors": authors,
                "year": pub_year,
                "abstract": "",
                "citation_count": 0,
                "venue": "",
                "doi": item.get("DOI", ""),
                "pdf_url": "",
                "source": "crossref",
                "paper_id": "",
            }
        return None
    except Exception as e:
        print(f"[CrossRef] lookup failed: {e}")
        return None


# ── Existence check ───────────────────────────────────────────────────────────

def _existence_check(citations: list[dict], progress_bar=None) -> list[dict]:
    from core.semantic_scholar import lookup_by_doi, lookup_by_title

    results = []
    for i, cit in enumerate(citations):
        if progress_bar:
            progress_bar.progress(
                (i + 1) / len(citations),
                text=f"Checking [{i+1}/{len(citations)}]: {cit['title'][:50]}..."
            )

        paper = None
        if cit.get("doi"):
            paper = lookup_by_doi(cit["doi"])
        if not paper and cit.get("title"):
            paper = lookup_by_title(cit["title"])
            time.sleep(0.5)
        if not paper and cit.get("title"):
            paper = _crossref_lookup(cit["title"], cit.get("year", ""))

        if not paper:
            results.append({
                **cit,
                "verdict": "not_found",
                "verdict_label": "Not found",
                "color": "red",
                "icon": "?",
                "explanation": (
                    "Not found in Semantic Scholar or CrossRef. "
                    "May be paywalled, very old, or title slightly differs."
                ),
                "matched_title": "",
                "matched_year": "",
                "matched_authors": [],
            })
            continue

        mismatches = []
        if not _title_similar(cit["title"], paper["title"]):
            mismatches.append(f"Title mismatch — found: '{paper['title'][:80]}'")
        if cit.get("year") and paper.get("year"):
            if str(cit["year"]) != str(paper["year"]):
                mismatches.append(f"Year mismatch — found: {paper['year']}")

        if mismatches:
            results.append({
                **cit,
                "verdict": "metadata_mismatch",
                "verdict_label": "Metadata mismatch",
                "color": "orange",
                "icon": "~",
                "explanation": " · ".join(mismatches),
                "matched_title": paper["title"],
                "matched_year": paper.get("year", ""),
                "matched_authors": paper.get("authors", []),
                "doi": paper.get("doi") or cit.get("doi", ""),
            })
        else:
            results.append({
                **cit,
                "verdict": "verified",
                "verdict_label": "Verified",
                "color": "green",
                "icon": "✓",
                "explanation": "Paper found with matching metadata.",
                "matched_title": paper["title"],
                "matched_year": paper.get("year", ""),
                "matched_authors": paper.get("authors", []),
                "doi": paper.get("doi") or cit.get("doi", ""),
            })
        # Log to MLflow
    # Log to MLflow
    try:
        from eval.mlflow_logger import log_citecheck_run
        verdicts = [r["verdict"] for r in results]
        log_citecheck_run(
            n_citations=len(results),
            verdicts=verdicts,
            latency=0,
        )
    except Exception as e:
        print(f"[MLflow] logging failed: {e}")

    return results


# ── Result renderer ───────────────────────────────────────────────────────────

def _render_results(results: list[dict]):
    st.divider()
    st.subheader("Results")

    verdicts = [r["verdict"] for r in results]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Checked", len(results))
    c2.metric("✓ Verified", verdicts.count("verified"))
    c3.metric("~ Metadata mismatch", verdicts.count("metadata_mismatch"))
    c4.metric("? Not found", verdicts.count("not_found"))

    st.divider()

    for r in results:
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{r['title'][:120]}**")
                authors = ", ".join(r.get("authors", [])[:3])
                year = r.get("year", "")
                venue = r.get("venue", "")
                meta = " · ".join(p for p in [authors, str(year), venue] if p)
                if meta:
                    st.caption(meta)
                if r["verdict"] == "metadata_mismatch":
                    st.caption(
                        f"💡 Suggested correction: _{r.get('matched_title', '')[:80]}_"
                    )
                elif r["verdict"] == "verified":
                    matched = r.get("matched_title", "")
                    if matched:
                        st.caption(f"Matched: _{matched[:80]}_")
            with col2:
                st.markdown(f":{r['color']}[**{r['icon']} {r['verdict_label']}**]")

            st.markdown(f"_{r['explanation']}_")
            doi = r.get("doi", "")
            if doi:
                st.markdown(f"[View paper →](https://doi.org/{doi})")
            st.markdown("---")

    import json
    st.download_button(
        "Download results (JSON)",
        data=json.dumps(results, indent=2, default=str),
        file_name="citecheck_results.json",
        mime="application/json",
    )


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    st.title("CiteCheck")
    st.caption(
        "Verify your citations — check whether cited papers exist "
        "and metadata is correct. Supports BibTeX, numbered lists, APA, PDF, and plain text."
    )

    # Coming soon banner
    st.info(
        "🔬 **Claim-level verification coming soon** — "
        "CiteLens will check whether each cited paper actually supports "
        "the specific claim you're making. Currently verifying metadata only.",
        icon=None,
    )

    tab_refs, tab_pdf, tab_text = st.tabs([
        "📋 Paste references",
        "📄 Upload PDF",
        "📝 Paste full text",
    ])

    # ── Tab 1: paste reference list ───────────────────────────────────────────
    with tab_refs:
        st.caption(
            "Paste your bibliography in **any format** — "
            "BibTeX, numbered `[1]`, APA, or MLA."
        )
        ref_text = st.text_area(
            "Reference list",
            height=240,
            placeholder=(
                "Paste in any format, e.g.:\n\n"
                "@article{codd1970relational,\n"
                "  title  = {A Relational Model of Data for Large Shared Data Banks},\n"
                "  author = {Codd, E. F.},\n"
                "  year   = {1970},\n"
                "  doi    = {10.1145/362384.362685}\n"
                "}\n\n"
                "OR\n\n"
                "[1] Frankle, J. and Carlin, M. The Lottery Ticket Hypothesis. ICLR 2019.\n"
                "[2] Simonyan, K. and Zisserman, A. Very Deep Convolutional Networks. ICLR 2015."
            ),
            label_visibility="collapsed",
            key="tab_refs_input",
        )

        if st.button("Check references", type="primary", key="btn_refs"):
            if not ref_text.strip():
                st.error("Paste your reference list above.")
            else:
                with st.spinner("Parsing references..."):
                    citations = _detect_and_parse(ref_text)

                if not citations:
                    st.error(
                        "Could not parse references. "
                        "Try BibTeX or a numbered list like: `[1] Author. Title. Year.`"
                    )
                else:
                    st.success(f"Parsed {len(citations)} references.")
                    with st.expander("Preview — check these look right before verifying"):
                        for c in citations:
                            st.markdown(f"**{c['title'][:100]}**")
                            meta = " · ".join(p for p in [
                                ", ".join(c.get("authors", [])[:2]),
                                c.get("year", ""),
                                c.get("doi", ""),
                                c.get("format", ""),
                            ] if p)
                            st.caption(meta)
                            st.markdown("---")

                    progress = st.progress(0)
                    results = _existence_check(citations, progress)
                    progress.empty()
                    _render_results(results)

    # ── Tab 2: PDF upload ─────────────────────────────────────────────────────
    with tab_pdf:
        st.caption(
            "Upload your paper PDF. We extract the references section "
            "and verify each citation."
        )
        uploaded = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            key="tab_pdf_upload",
            label_visibility="collapsed",
        )

        if uploaded:
            with st.spinner("Extracting references from PDF..."):
                citations = _extract_from_pdf(uploaded.read())

            if not citations:
                st.warning(
                    "Could not find a References section in this PDF. "
                    "Make sure the PDF has a section titled 'References' or 'Bibliography'. "
                    "Try the 'Paste full text' tab instead."
                )
            else:
                st.success(f"Found {len(citations)} references.")
                with st.expander("Preview extracted references"):
                    for c in citations:
                        st.markdown(f"**{c['title'][:100]}**")
                        meta = " · ".join(p for p in [
                            ", ".join(c.get("authors", [])[:2]),
                            c.get("year", ""),
                        ] if p)
                        if meta:
                            st.caption(meta)
                        st.markdown("---")
                    if len(citations) > 15:
                        st.caption(f"Showing first 15 of {len(citations)}")

                limit = st.number_input(
                    "Max references to verify",
                    min_value=1,
                    max_value=len(citations),
                    value=min(15, len(citations)),
                    key="pdf_limit",
                )

                if st.button("Verify references", type="primary", key="btn_pdf"):
                    progress = st.progress(0)
                    results = _existence_check(citations[:int(limit)], progress)
                    progress.empty()
                    _render_results(results)

    # ── Tab 3: paste full text ────────────────────────────────────────────────
    with tab_text:
        st.caption(
            "Paste your paper text. We find the References section "
            "and verify each citation."
        )
        full_text_input = st.text_area(
            "Full paper text",
            height=280,
            placeholder=(
                "Paste your full paper here — body and references section.\n\n"
                "Works best when your text ends with a References or Bibliography section."
            ),
            label_visibility="collapsed",
            key="tab_text_input",
        )

        if st.button("Extract and verify", type="primary", key="btn_text"):
            if not full_text_input.strip():
                st.error("Paste your paper text above.")
            else:
                cleaned = _clean_text(full_text_input)
                refs_section = _find_refs_section(cleaned)

                if refs_section:
                    with st.spinner("Parsing references section..."):
                        citations = _parse_reference_list(refs_section)
                else:
                    # No clear references section — try parsing whole text
                    with st.spinner("Parsing text as reference list..."):
                        citations = _parse_reference_list(cleaned)

                if not citations:
                    st.warning(
                        "Could not find or parse a references section. "
                        "Make sure your text includes a section titled 'References' "
                        "and uses numbered `[1]` or author-year citations."
                    )
                else:
                    st.success(f"Found {len(citations)} references.")
                    with st.expander("Preview before verifying"):
                        for c in citations[:15]:
                            st.markdown(f"**{c['title'][:100]}**")
                            meta = " · ".join(p for p in [
                                ", ".join(c.get("authors", [])[:2]),
                                c.get("year", ""),
                            ] if p)
                            if meta:
                                st.caption(meta)
                            st.markdown("---")

                    limit = st.number_input(
                        "Max references to verify",
                        min_value=1,
                        max_value=len(citations),
                        value=min(15, len(citations)),
                        key="text_limit",
                    )

                    if st.button("Verify", type="primary", key="btn_text_verify"):
                        progress = st.progress(0)
                        results = _existence_check(citations[:int(limit)], progress)
                        progress.empty()
                        _render_results(results)