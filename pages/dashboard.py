"""
CiteLens Analytics — MLOps observability page.
Shows CiteFind and CiteCheck run metrics from MLflow.
No auth required — integrated into main app.
"""
import os
import streamlit as st
import pandas as pd

os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"


def _load_runs() -> pd.DataFrame:
    try:
        import mlflow
        from config import cfg
        mlflow.set_tracking_uri(cfg.MLFLOW_TRACKING_URI)
        return mlflow.search_runs(
            experiment_names=["citelens"],
            max_results=200,
            order_by=["start_time DESC"],
        )
    except Exception as e:
        print(f"[MLflow] load failed: {e}")
        return pd.DataFrame()


def render():
    st.title("Analytics")
    st.caption(
        "Every CiteFind and CiteCheck run is logged automatically. "
        "This page tracks system performance, retrieval quality, and usage over time."
    )

    runs = _load_runs()

    if runs.empty:
        st.info("No runs logged yet — try CiteFind or CiteCheck first.")
        return

    citefind_runs = runs[
        runs["tags.mlflow.runName"].str.startswith("citefind", na=False)
    ].copy()
    citecheck_runs = runs[
        runs["tags.mlflow.runName"].str.startswith("citecheck", na=False)
    ].copy()

    # ── Top-level summary ─────────────────────────────────────────────────────
    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total runs", len(runs))
    c2.metric("CiteFind runs", len(citefind_runs))
    c3.metric("CiteCheck runs", len(citecheck_runs))

    lat_col = "metrics.latency_s"
    if lat_col in runs.columns and not runs.empty:
        c4.metric("Avg latency", f"{runs[lat_col].mean():.1f}s")

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["CiteFind", "CiteCheck"])

    with tab1:
        _citefind_tab(citefind_runs)

    with tab2:
        _citecheck_tab(citecheck_runs)


def _citefind_tab(df: pd.DataFrame):
    if df.empty:
        st.info("No CiteFind runs yet.")
        return

    lat = "metrics.latency_s"
    papers = "metrics.n_papers_found"
    claims = "metrics.n_claims"

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runs", len(df))
    if lat in df.columns:
        c2.metric("Avg latency", f"{df[lat].mean():.1f}s")
        c3.metric("Best latency", f"{df[lat].min():.1f}s")
    if papers in df.columns:
        c4.metric("Avg papers / run", f"{df[papers].mean():.0f}")

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        if lat in df.columns:
            st.subheader("Latency over runs")
            st.line_chart(
                df[lat].reset_index(drop=True),
                use_container_width=True,
            )
    with col2:
        if papers in df.columns and claims in df.columns:
            st.subheader("Claims extracted vs papers found")
            chart_df = df[[claims, papers]].rename(columns={
                claims: "Claims",
                papers: "Papers found",
            }).reset_index(drop=True)
            st.bar_chart(chart_df, use_container_width=True)

    # Run log table
    st.subheader("Run log")
    _table(df, [
        "start_time",
        "metrics.n_claims",
        "metrics.n_papers_found",
        "metrics.n_groups_output",
        "metrics.latency_s",
    ])


def _citecheck_tab(df: pd.DataFrame):
    if df.empty:
        st.info("No CiteCheck runs yet.")
        return

    lat = "metrics.latency_s"
    nv = "metrics.n_verified"
    nm = "metrics.n_metadata_mismatch"
    nf = "metrics.n_not_found"
    nc = "metrics.n_citations"

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runs", len(df))
    if nc in df.columns:
        c2.metric("Total citations checked", int(df[nc].sum()))
    if nv in df.columns and nc in df.columns:
        total_v = df[nv].sum()
        total_c = df[nc].sum()
        rate = total_v / total_c if total_c else 0
        c3.metric("Overall verified rate", f"{rate:.1%}")
    if lat in df.columns:
        c4.metric("Avg latency", f"{df[lat].mean():.1f}s")

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        if lat in df.columns:
            st.subheader("Latency over runs")
            st.line_chart(
                df[lat].reset_index(drop=True),
                use_container_width=True,
            )
    with col2:
        # Verdict breakdown across all runs
        if all(c in df.columns for c in [nv, nm, nf]):
            st.subheader("Verdict breakdown (all runs)")
            breakdown = {
                "Verified": int(df[nv].sum()),
                "Metadata mismatch": int(df[nm].sum()) if nm in df.columns else 0,
                "Not found": int(df[nf].sum()),
            }
            st.bar_chart(breakdown, use_container_width=True)

    # Run log table
    st.subheader("Run log")
    _table(df, [
        "start_time",
        "metrics.n_citations",
        "metrics.n_verified",
        "metrics.n_not_found",
        "metrics.latency_s",
    ])


def _table(df: pd.DataFrame, cols: list):
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return
    display = df[existing].rename(
        columns=lambda c: c.replace("metrics.", "").replace("params.", "")
    ).reset_index(drop=True)
    st.dataframe(display, use_container_width=True, hide_index=True)