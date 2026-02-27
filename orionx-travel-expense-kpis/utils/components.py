import streamlit as st

def kpi_card(title, value, color="#111827"):

    with st.container():
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">{title}</div>
                <div class="kpi-value" style="color:{color};">{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )