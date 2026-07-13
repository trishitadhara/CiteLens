import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

st.set_page_config(
    page_title="CiteLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Handle nav button clicks from home page
if "nav" in st.session_state:
    default_page = st.session_state.pop("nav")
else:
    default_page = "Home"

with st.sidebar:
    st.markdown("## CiteLens")
    st.divider()

    pages = ["Home", "CiteFind", "CiteCheck", "Analytics"]
    page = st.radio(
        "Navigation",
        pages,
        index=pages.index(default_page),
        label_visibility="collapsed",
    )

if page == "Home":
    from pages.home import render
    render()
elif page == "CiteFind":
    from pages.citefind import render
    render()
elif page == "CiteCheck":
    from pages.citecheck import render
    render()
elif page == "Analytics":
    from pages.dashboard import render
    render()