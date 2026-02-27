import pandas as pd
import streamlit as st

@st.cache_data
def load_summary():
    return pd.read_parquet("../data/curated/kpi_summary.parquet")

@st.cache_data
def load_monthly():
    return pd.read_parquet("../data/curated/kpi_monthly_trend.parquet")

@st.cache_data
def load_department():
    return pd.read_parquet("../data/curated/kpi_department_spend.parquet")

@st.cache_data
def load_mom_growth():
    return pd.read_parquet("../data/curated/kpi_mom_growth.parquet")