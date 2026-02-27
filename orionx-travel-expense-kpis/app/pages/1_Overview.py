import streamlit as st
from utils.data_loader import load_summary, load_mom_growth
from utils.components import kpi_card
import plotly.graph_objects as go
import pandas as pd
import calendar

st.markdown("## Executive Overview")
st.caption("Strategic snapshot of organizational spend performance and allocation trends")
st.markdown("""
<style>

.kpi-card {
    background: linear-gradient(145deg, #ffffff, #f5f7fc);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    transition: all 0.2s ease-in-out;
    display: block;
    width: 100%;
}

.kpi-card:hover {
    transform: translateY(-3px);
}

.kpi-title {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 26px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


col1, col2, col3, col4, col5 = st.columns(5)

# ---- Load Summary ----
summary = load_summary()
# ----- Load MOM Growth -----
mom = load_mom_growth()
mom["month_num"] = mom["transaction_month"].apply(
    lambda x: list(calendar.month_name).index(x)
)
mom = mom.sort_values(["transaction_year", "month_num"])
latest_mom = mom["mom_growth_pct"].iloc[-1]

# ------- Formatter ----------------
def format_money(x):
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    elif abs(x) >= 1_000:
        return f"${x/1_000:.1f}K"
    return f"${x:.2f}"

# ---- KPI ROW -----------------------
with col1:
    kpi_card("Total Expense", format_money(summary['total_expense'][0]),
        color="#111827"
    )

with col2:
    kpi_card("Total Transactions", f"{summary['total_transactions'][0]:,}",
        color="#111827"
    )
with col3:
    kpi_card("Average Expense", f"${summary['avg_expense'][0]:,.2f}",
        color="#111827"        
    )

with col4:
    kpi_card("Policy Risk Rate", f"{summary['policy_risk_rate'][0]:.2%}",
        color="#111827"         
    )

with col5:
    delta_symbol = "▲" if latest_mom >= 0 else "▼"
    delta_color = "#16a34a" if latest_mom >= 0 else "#dc2626"

    kpi_card(
        "MoM Growth",
        f"{delta_symbol} {latest_mom:.2f}%",
        color=delta_color
    )

st.divider()
left, right = st.columns(2)

# ---------------- LEFT: Monthly Trend ----------------
with left:
    st.markdown("#### Monthly Spend Performance")
    monthly = pd.read_parquet("../data/curated/kpi_monthly_trend.parquet")
    if str(monthly["year_month"].dtype).startswith("period"):
        monthly["year_month"] = monthly["year_month"].dt.to_timestamp()

    monthly =  monthly.sort_values("year_month")

# Rolling 3-month average
    monthly["rolling_3m"] = (
        monthly["expense_approved_amount_rpt"]
        .rolling(3)
        .mean()
    )
# ----------------- MONTHLY TREND FIGURE --------------
    fig = go.Figure()

    primary = "rgba(79, 114, 205, 1)"
    fill = "rgba(79, 114, 205, 0.08)"

    # --- Total Spend (Area) ---
    fig.add_trace(go.Scatter(
        x=monthly["year_month"],
        y=monthly["expense_approved_amount_rpt"],
        mode="lines",
        name="Total Spend",
        line=dict(color=primary, width=3, shape="spline"),
        fill="tozeroy",
        fillcolor=fill
    ))

    # --- Rolling 3M Average (Line) ---
    fig.add_trace(go.Scatter(
        x=monthly["year_month"],
        y=monthly["rolling_3m"],
        mode="lines",
        name="3-Month Average",
        line=dict(color="#7A869A", width=2, dash="dash")
    ))

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=20, b=10),
        font=dict(
            family="Inter, sans-serif",
            size=13
        ),
        xaxis=dict(
            tickformat="%b %Y",
            showgrid=False
        ),
        yaxis=dict(
            tickformat=".2s",
            gridcolor="rgba(0,0,0,0.06)",
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            y=1.05,
            x=1,
            xanchor="right"
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- RIGHT: Department Spend ----------------
with right:
    st.markdown("#### Spend by Department")

    dept = pd.read_parquet("../data/curated/kpi_department_spend.parquet")

    # Sort descending for executive readability
    dept = dept.sort_values("expense_approved_amount_rpt", ascending=True)
    
    total_spend = dept["expense_approved_amount_rpt"].sum()
    dept["pct_total"] = dept["expense_approved_amount_rpt"] / total_spend

    
    fig_dept = go.Figure()
    
    fig_dept.add_trace(go.Bar(
        x=dept["expense_approved_amount_rpt"],
        y=dept["department_name"],
        orientation="h",
        marker=dict(
            color="rgba(79, 114, 205, 0.85)",   # Professional blue
            line=dict(color="rgba(37, 99, 235, 1)", width=1)
        ),
        text=[f"${v/1_000_000:.1f}M" for v in dept["expense_approved_amount_rpt"]],
        textposition="inside",
        textfont=dict(
            color="white",
            size=12
        ),
        hovertemplate="<b>%{y}</b><br>Spend: $%{x:,.0f}<extra></extra>"
    ))

    fig_dept.update_layout(
        height=420,
        template="plotly_white",
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(
            tickformat="$,.2s",
            showgrid=False,
            title=None
        ),
        yaxis=dict(
            title=None,
            categoryorder="total ascending"
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig_dept, use_container_width=True)


