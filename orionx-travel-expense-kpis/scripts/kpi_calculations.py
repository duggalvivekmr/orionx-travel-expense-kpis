import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "data" / "feature" / "expense_features.parquet"
OUTPUT_PATH = BASE_DIR / "data" / "curated" / "expense_kpis.parquet"

class ExpenseKPICalculator:

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()    

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
        return self.df["is_policy_risk"].mean()
    
    # ----------------------------------------
    # Travel Dimension KPIs
    # ----------------------------------------

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
    
    # ----------------------------------------------
    # Category KPI
    # ----------------------------------------------

    def category_spend(self):
        return (
            self.df
            .groupby("category")["expense_approved_amount_rpt"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
    
    # ------------------------------------------------
    # Policy / Risk KPIs
    # ------------------------------------------------

    def high_risk_transactions(self):
        return self.df[self.df["is_policy_risk"]]

    def fx_impact_summary(self):
        return(
            self.df
            .groupby("is_fx_impactful")["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
        ) 

    # ------------------------------------------------
    # Trend KPIs
    # ------------------------------------------------

    def monthly_trend(self):
        self.df["year_month"] = pd.to_datetime(
            self.df["transaction_date"]
        ).dt.to_period("M")

        return(
            self.df
            .groupby("year_month")["expense_approved_amount_rpt"]
            .sum()
            .reset_index()
            .sort_values("year_month")
        )

    # ----------------------------------------------------
    # Build KPI summary table
    # ----------------------------------------------------

    def executive_summary(self):
        return pd.DataFrame([{
            "total_expense": self.total_expense(),
            "total_transactions": self.total_transactions(),
            "avg_expense": self.avg_expense(),
            "policy_risk_rate": self.policy_risk_rate()
        }])
    

def main():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    
    df = pd.read_parquet(INPUT_PATH)
    print(f"Input rows: {len(df)}")

    kpi = ExpenseKPICalculator(df)

    # Example outputs
    summary = kpi.executive_summary()
    travel = kpi.travel_split()
    customer = kpi.customer_split()
    travel_matrix = kpi.travel_customer_matrix()
    category = kpi.category_spend()
    trend = kpi.monthly_trend()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save executive summary
    summary.to_parquet(OUTPUT_PATH.parent / "kpi_summary.parquet", index=False)
    travel.to_parquet(OUTPUT_PATH.parent / "kpi_travel_split.parquet", index=False)
    customer.to_parquet(OUTPUT_PATH.parent / "kpi_customer_split.parquet", index=False)
    travel_matrix.to_parquet(OUTPUT_PATH.parent / "kpi_travel_customer_matrix.parquet", index=False)
    category.to_parquet(OUTPUT_PATH.parent / "kpi_category.parquet", index=False)
    trend.to_parquet(OUTPUT_PATH.parent / "kpi_monthly_trend.parquet", index=False)


    print("All KPI datasets built successfully")


if __name__ == "__main__":
    main()