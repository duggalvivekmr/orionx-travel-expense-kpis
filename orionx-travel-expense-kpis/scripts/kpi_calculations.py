import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "data" / "feature" / "expense_features.parquet"
OUTPUT_PATH = BASE_DIR / "data" / "curated" / "expense_kpis.parquet"
APPROVAL_SLA_DAYS = 7
class ExpenseKPICalculator:

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() 

    # -------------------------------
    # Build KPI summary table
    # -------------------------------
 
    def executive_summary(self):

        return pd.DataFrame([{
            "total_expense": self.total_expense(),
            "total_transactions": self.total_transactions(),
            "avg_expense": self.avg_expense(),
            "policy_risk_rate": self.policy_risk_rate(),
            "sla_breach_rate": self.approval_sla_breach_rate(),
            "avg_approval_days": self.avg_approval_days(),

            # Extract scalar values from DataFrame KPIs
            "late_submission_rate_pct":
                self.late_submission_pct()["late_submission_pct"].iloc[0],

            "fx_impact_rate_pct":
                self.fx_impact_pct()["fx_impactful_pct"].iloc[0],

            "expense_per_active_employee":
                self.expense_per_active_employee()["expense_per_active_employee"].iloc[0],

            "travel_expense_pct":
                self.travel_expense_pct()["travel_expense_pct"].iloc[0],

            "customer_expense_pct":
                self.customer_facing_pct()["customer_facing_pct"].iloc[0],

            "high_risk_expense_pct":
                self.high_risk_expense_pct()["high_risk_expense_pct"].iloc[0],
        }])

    # -----------------------------------
    # MoM Growth %
    # -----------------------------------
    def calculate_mom_growth (self):
            monthly = (
                self.df.groupby(["transaction_year", "transaction_month"])["expense_approved_amount_rpt"]
                .sum()
                .reset_index()
                .sort_values(["transaction_year", "transaction_month"])     
            )
        
            monthly["mom_growth_pct"] = (
                monthly["expense_approved_amount_rpt"].pct_change()*100
            )

            return monthly 

    # ---------------------
    # YTD Expense
    # ---------------------
    def calculate_ytd(self):
        df_sorted = self.df.sort_values(["transaction_year", "transaction_month"])

        monthly = (
            df_sorted.groupby(["transaction_year", "transaction_month"])["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
        )

        monthly["ytd_expense"] = (
            monthly.groupby("transaction_year")["expense_approved_amount_rpt"]
            .cumsum()
        )

        return monthly
    
    # -------------------------
    # Travel Expense %
    # -------------------------
    def travel_expense_pct(self):
        total = self.df['expense_approved_amount_rpt'].sum()
        travel = self.df[self.df['is_travel'] == 1]['expense_approved_amount_rpt'].sum()

        return pd.DataFrame({
        'travel_expense_pct': [(travel / total) * 100]
    })
    # -------------------------------
    # Customer-Facing Expense %
    # -------------------------------
    def customer_facing_pct(self):
        total = self.df['expense_approved_amount_rpt'].sum()
        customer = self.df[self.df['is_customer_facing'] == 1]['expense_approved_amount_rpt'].sum()

        return pd.DataFrame({
        'customer_facing_pct': [(customer / total) * 100]
    }) 

    # -------------------------------
    # Expense per Active Employee
    # -------------------------------
    def expense_per_active_employee(self):
        active_employees = self.df[self.df['active'] == 'Yes']['employee_id'].nunique()
        total = self.df['expense_approved_amount_rpt'].sum()

        return pd.DataFrame({
        'expense_per_active_employee': [total / active_employees]
    })
    # ---------------------------------
    # High-Risk Expense %
    # ---------------------------------
    def high_risk_expense_pct(self):
        total = self.df['expense_approved_amount_rpt'].sum()
        risky = self.df[self.df['is_policy_risk'] == 1]['expense_approved_amount_rpt'].sum()

        return pd.DataFrame({
        'high_risk_expense_pct': [(risky / total) * 100]
    })

    # -----------------------------------
    # Rolling 3 Months
    # -----------------------------------
    def rolling_3m(self):
        monthly = (
            self.df.groupby(['transaction_year','transaction_month'])['expense_approved_amount_rpt']
            .sum()
            .reset_index()
            .sort_values(["transaction_year", "transaction_month"])
        )

        monthly["rolling_3m"] = (
            monthly["expense_approved_amount_rpt"].rolling(3).sum()
        )
        
        return monthly
    # --------------------------------
    # Quarterly Comparison
    # --------------------------------
    def quarterly_comparison(self):
        return (
            self.df.groupby(['transaction_year','transaction_quarter'])['expense_approved_amount_rpt']
            .sum()
            .reset_index()
            .sort_values(["transaction_year","transaction_quarter"])
    )

    # -------------------------------
    # Monthly Trend KPIs
    # -------------------------------

    def monthly_trend(self):
        df = self.df.copy()
        df["year_month"] = pd.to_datetime(
                df["transaction_date"]
        ).dt.to_period("M")

        return(
            df
            .groupby("year_month")["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )

    # --------------------------------
    # Travel Dimension KPIs
    # --------------------------------

    def travel_split(self):
        return (
            self.df
            .groupby("is_travel")["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
        )

    def customer_split(self):
        return(
            self.df
            .groupby("is_customer_facing")["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
        )
    
    def travel_customer_matrix(self):
        matrix = (
            self.df
            .groupby(["is_travel", "is_customer_facing"])["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
        )

        # Ensure all 4 combinations exist
        full_index = pd.MultiIndex.from_product(
        [[False, True], [False, True]],
        names=["is_travel", "is_customer_facing"]
        )

        matrix = (
            matrix
            .set_index(["is_travel", "is_customer_facing"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )

        return matrix
    # -------------------------------
    # Category KPI
    # -------------------------------
    def category_spend(self):
        return (
            self.df
            .groupby("category")["expense_approved_amount_rpt"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
    # ------------------------
    # Top 5 Expense Types
    # ------------------------
    def top_5_expense_types(self):
        return (
            self.df.groupby('expense_type')['expense_approved_amount_rpt']
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
    )
    # ---------------------------
    # Department Spend
    # ---------------------------

    def department_spend(self):
        return (
            self.df.groupby('department_name')['expense_approved_amount_rpt']
            .sum()
            .reset_index()
            .sort_values('expense_approved_amount_rpt', ascending=False)
    )
    # ----------------------------
    # Vendor Concentration %
    # ----------------------------

    def vendor_concentration(self):
        vendor_spend = (
            self.df.groupby('vendor')['expense_approved_amount_rpt']
            .sum()
    )

        total = vendor_spend.sum()
        hhi = ((vendor_spend / total) ** 2).sum()

        return pd.DataFrame({
            'vendor_concentration_hhi': [hhi]
    })
    # -------------------------------
    # Spend by Payment Type
    # -------------------------------

    def spend_by_payment_type(self):
        return (
            self.df.groupby('payment_type')['expense_approved_amount_rpt']
            .sum()
            .reset_index()
    )

    # ----------------------------------------------
    # Approval Stage Breakdown (Bottleneck Analysis)
    # ----------------------------------------------
    def approval_stage_breakdown(self):
        return pd.DataFrame([{
            "submission_to_manager_avg":
                self.df["submission_to_manager_days"].mean(),
            "manager_to_accounting_avg":
                self.df["manager_to_accounting_days"].mean(),
        }])
    # ------------------------------
    # Approval Time by Department
    # ------------------------------
    def approval_time_by_department(self):
        return (
            self.df
            .groupby("department_name")["end_to_end_approval_days"]
            .mean()
            .reset_index()
            .sort_values("end_to_end_approval_days", ascending=False)
        )
    
    # -------------------------------
    # % Late Submission
    # -------------------------------
    def late_submission_pct(self):
        pct = self.df['is_late_submission'].mean() * 100

        return pd.DataFrame({
        'late_submission_pct': [pct]
    })
    # -------------------------------
    # Avg Approval Time
    # -------------------------------
    def avg_end_to_end_days(self):
        return pd.DataFrame({
            'avg_end_to_end_days': [self.df['end_to_end_approval_days'].mean()]
    })
    # -------------------------------
    # % FX Impactful Transactions
    # -------------------------------
    def fx_impact_pct(self):
        pct = self.df['is_fx_impactful'].mean() * 100

        return pd.DataFrame({
            'fx_impactful_pct': [pct]
    })

    # ---------------------------------
    # FX Impact Summary
    # --------------------------------
    def fx_impact_summary(self):
        return(
            self.df
            .groupby("is_fx_impactful")["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
        ) 

    # --------------------------------------
    # Travel Cost per Employee
    # --------------------------------------
    def travel_cost_per_employee(self):
        travel = self.df[self.df['is_travel'] == 1]['expense_approved_amount_rpt'].sum()
        employees = self.df['employee_id'].nunique()

        return pd.DataFrame({
        'travel_cost_per_employee': [travel / employees]
    })
    # --------------------------------------------
    # Internal Overhead Ration
    # --------------------------------------------
    def internal_overhead_ratio(self):
        total = self.df['expense_approved_amount_rpt'].sum()
        internal = self.df[self.df['is_internal'] == 1]['expense_approved_amount_rpt'].sum()

        return pd.DataFrame({
        'internal_overhead_ratio': [(internal / total) * 100]
    })


    # --------------------------------------
    # Executive KPIS
    # --------------------------------------
    def total_expense(self):
        return self.df["expense_approved_amount_rpt"].sum()
    
    def total_transactions(self):
        return len(self.df)
    
    def avg_expense(self):
        return self.df["expense_approved_amount_rpt"].mean()
    
    def policy_risk_rate(self):
        return self.df["is_policy_risk"].mean() *100    

    def avg_approval_days(self):
        return self.df["end_to_end_approval_days"].mean()

    def median_approval_days(self):
        return self.df["end_to_end_approval_days"].median()
      
    def approval_sla_breach_rate(self):
        return (
            (self.df["end_to_end_approval_days"] > APPROVAL_SLA_DAYS)
            .mean()*100
        )

    def high_risk_transactions(self):
        return self.df[self.df["is_policy_risk"]]
        
    
def main():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    
    df = pd.read_parquet(INPUT_PATH)
    print(f"Input rows: {len(df)}")

    kpi = ExpenseKPICalculator(df)

    # ---------------- Executive KPIs ----------------
    summary = kpi.executive_summary()
    mom = kpi.calculate_mom_growth()
    ytd = kpi.calculate_ytd()
    travel_pct = kpi.travel_expense_pct()
    customer_pct = kpi.customer_facing_pct()
    expense_per_active = kpi.expense_per_active_employee()
    high_risk_pct = kpi.high_risk_expense_pct()

    # ---------------- Time KPIs ----------------
    rolling_3m = kpi.rolling_3m()
    quarterly = kpi.quarterly_comparison()
    monthly_trend = kpi.monthly_trend()

    # ---------------- Spend Structure KPIs ----------------
    travel = kpi.travel_split()
    customer = kpi.customer_split()
    travel_matrix = kpi.travel_customer_matrix()
    category = kpi.category_spend()
    top5 = kpi.top_5_expense_types()
    dept_spend = kpi.department_spend()
    vendor_conc = kpi.vendor_concentration()
    payment_type = kpi.spend_by_payment_type()

    # ---------------- Risk & Approval KPIs ----------------
    approval_stage = kpi.approval_stage_breakdown()
    approval_dept = kpi.approval_time_by_department()
    late_submission = kpi.late_submission_pct()
    avg_end_to_end = kpi.avg_end_to_end_days()
    fx_pct = kpi.fx_impact_pct()
    fx_summary = kpi.fx_impact_summary()

    # ---------------- Efficiency KPIs ----------------
    travel_per_emp = kpi.travel_cost_per_employee()
    internal_ratio = kpi.internal_overhead_ratio()

    # ---------------- Create Output Folder ----------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ---------------- Save All KPIs ----------------
    summary.to_parquet(OUTPUT_PATH.parent / "kpi_executive_summary.parquet", index=False)

    mom.to_parquet(OUTPUT_PATH.parent / "kpi_mom_growth.parquet", index=False)
    ytd.to_parquet(OUTPUT_PATH.parent / "kpi_ytd.parquet", index=False)
    rolling_3m.to_parquet(OUTPUT_PATH.parent / "kpi_rolling_3m.parquet", index=False)
    quarterly.to_parquet(OUTPUT_PATH.parent / "kpi_quarterly.parquet", index=False)
    monthly_trend.to_parquet(OUTPUT_PATH.parent / "kpi_monthly_trend.parquet", index=False)

    travel_pct.to_parquet(OUTPUT_PATH.parent / "kpi_travel_pct.parquet", index=False)
    customer_pct.to_parquet(OUTPUT_PATH.parent / "kpi_customer_pct.parquet", index=False)
    expense_per_active.to_parquet(OUTPUT_PATH.parent / "kpi_expense_per_active_employee.parquet", index=False)
    high_risk_pct.to_parquet(OUTPUT_PATH.parent / "kpi_high_risk_pct.parquet", index=False)

    travel.to_parquet(OUTPUT_PATH.parent / "kpi_travel_split.parquet", index=False)
    customer.to_parquet(OUTPUT_PATH.parent / "kpi_customer_split.parquet", index=False)
    travel_matrix.to_parquet(OUTPUT_PATH.parent / "kpi_travel_customer_matrix.parquet", index=False)
    category.to_parquet(OUTPUT_PATH.parent / "kpi_category_spend.parquet", index=False)
    top5.to_parquet(OUTPUT_PATH.parent / "kpi_top5_expense_types.parquet", index=False)
    dept_spend.to_parquet(OUTPUT_PATH.parent / "kpi_department_spend.parquet", index=False)
    vendor_conc.to_parquet(OUTPUT_PATH.parent / "kpi_vendor_concentration.parquet", index=False)
    payment_type.to_parquet(OUTPUT_PATH.parent / "kpi_payment_type.parquet", index=False)

    approval_stage.to_parquet(OUTPUT_PATH.parent / "kpi_approval_stage.parquet", index=False)
    approval_dept.to_parquet(OUTPUT_PATH.parent / "kpi_approval_by_department.parquet", index=False)
    late_submission.to_parquet(OUTPUT_PATH.parent / "kpi_late_submission_pct.parquet", index=False)
    avg_end_to_end.to_parquet(OUTPUT_PATH.parent / "kpi_avg_end_to_end_days.parquet", index=False)
    fx_pct.to_parquet(OUTPUT_PATH.parent / "kpi_fx_impact_pct.parquet", index=False)
    fx_summary.to_parquet(OUTPUT_PATH.parent / "kpi_fx_summary.parquet", index=False)

    travel_per_emp.to_parquet(OUTPUT_PATH.parent / "kpi_travel_cost_per_employee.parquet", index=False)
    internal_ratio.to_parquet(OUTPUT_PATH.parent / "kpi_internal_overhead_ratio.parquet", index=False)

    print("All KPI datasets built successfully")

if __name__ == "__main__": 
    main()