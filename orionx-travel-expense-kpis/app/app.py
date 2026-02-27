import sys
from pathlib import Path
import streamlit as st

# =====================================================
# PAGE CONFIG  (MUST BE FIRST STREAMLIT COMMAND)
# =====================================================
st.set_page_config(
    page_title="OrionX Travel Expense Dashboard",
    page_icon="📊",
    layout="wide",
)

# =====================================================
# PROJECT ROOT PATH
# =====================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# =====================================================
# GLOBAL STYLING
# =====================================================
st.markdown("""
<style>

/* App background */
[data-testid="stAppViewContainer"] {
    background-color: #f6f8fb;
}

/* Remove default container background */
section[data-testid="stHorizontalBlock"] > div {
    background-color: transparent !important;
}

div[data-testid="stVerticalBlock"] > div {
    background-color: transparent !important;
}

/* Cleaner spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Sidebar style */
[data-testid="stSidebar"] {
    background-color: #ffffff;
}

/* Section headings */
h2, h3, h4 {
    font-weight: 600;
    color: #1f2937;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# MAIN HEADER
# =====================================================
st.title("OrionX Travel Expense Dashboard")
st.caption("Enterprise KPI Monitoring | Version 1.1")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.markdown("### Navigation")
st.sidebar.markdown("Use the menu above to switch pages")
st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit")
