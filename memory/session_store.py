"""
Short-term session memory using Streamlit session state.
JD point 4: short-term context — no external DB needed.
"""
import streamlit as st
from typing import List, Dict, Optional


def get_session_history(key: str = "cite_history") -> List[Dict]:
    if key not in st.session_state:
        st.session_state[key] = []
    return st.session_state[key]


def append_to_session(entry: Dict, key: str = "cite_history"):
    history = get_session_history(key)
    history.append(entry)
    st.session_state[key] = history[-20:]  # Keep last 20


def get_saved_papers(key: str = "saved_papers") -> List[Dict]:
    if key not in st.session_state:
        st.session_state[key] = []
    return st.session_state[key]


def save_paper(paper: Dict, claim: str, key: str = "saved_papers"):
    saved = get_saved_papers(key)
    # Deduplicate by title
    titles = {p["title"] for p in saved}
    if paper["title"] not in titles:
        saved.append({**paper, "saved_for_claim": claim})
        st.session_state[key] = saved


def clear_session(key: str = "cite_history"):
    st.session_state[key] = []
