import pandas as pd
import numpy as np
from pathlib import Path

# -------------------------------
# Paths
# -------------------------------

INPUT_PATH = Path("data/processed/expense_cleaned.parquet")
OUTPUT_PATH = Path("data/feature/expense_features.parquet")

# -------------------------------
# Business thresholds
# -------------------------------
HIGH_AMOUNT_THRESHOLD = 2200  #reporting currency
VERY_HIGH_AMOUNT_THRESHOLD = 3000 # reporting currency
LATE_SUBMISSION_DAYS = 12
FX_IMPACT_THRESHOLD = 0.44   # ~90th percentile of abs fx variance

# -------------------------------
# Expense mapping logic
# -------------------------------
EXPENSE_CLASSIFICATION_MAP = {
    # Airfare
    "Airfare – Company Event": {"is_customer_facing": False},
    "Airfare – Conference": {"is_customer_facing": False},
    "Airfare – Customer Facing": {"is_customer_facing": True},
    "Airfare – Internal": {"is_customer_facing": False},
    "Airfare – Offsite": {"is_customer_facing": False},

    # Hotel
    "Hotel – Conference": {"is_customer_facing": False},
    "Hotel – Customer Facing": {"is_customer_facing": True},
    "Hotel – Internal": {"is_customer_facing": False},

    # Meals
    "Meal – Conference": {"is_customer_facing": False},
    "Meal – Customer Facing": {"is_customer_facing": True},
    "Meal – Internal": {"is_customer_facing": False},

    # Ground / Transportation
    "Ground Transportation – Customer Facing": {"is_customer_facing": True},
    "Transportation – Internal": {"is_customer_facing": False},
    "Car – Internal": {"is_customer_facing": False},
    "Fuel / Gas Charges": {"is_customer_facing": False},
    "Mileage – Personal Car": {"is_customer_facing": False},
    "Parking and Tolls": {"is_customer_facing": False},

    # Other non-travel
    "Bank / FX Fees": {"is_customer_facing": False},
    "Computer/Laptop Accessories": {"is_customer_facing": False},
    "Donation": {"is_customer_facing": False},
    "Education": {"is_customer_facing": False},
    "Entertainment": {"is_customer_facing": False},
    "Gifts": {"is_customer_facing": False},
    "Internet": {"is_customer_facing": False},
    "Office Expense": {"is_customer_facing": False},
    "Relocation Expense": {"is_customer_facing": False},
    "Seminars, & Conferences": {"is_customer_facing": False},
    "Software and Software Subscription": {"is_customer_facing": False},
    "Taxable Award": {"is_customer_facing": False},

    # Travel utilities
    "Travel Internet": {"is_customer_facing": False}
}


# --------------------------------
# Feature engineering logic
# --------------------------------
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    print("Starting feature engineering(finance aligned)...")
    
    unmapped = set(df["expense_type"].unique()) - set(EXPENSE_CLASSIFICATION_MAP.keys())
    if unmapped:
        print("WARNING: Unmapped expense_type values detected:")
        for u in unmapped:
            print(f"  - {u}")
    
    # -------------------------------------------------------
    # Ensure datetime types safely
    # -------------------------------------------------------
    date_cols = [
        "transaction_date",
        "first_submitted_date",
        "manager_approval_date",
        "accounting_approval_date",
    ]
    
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # --------------------------------------------------------
    # Approval cycle times
    # --------------------------------------------------------
    df["submission_to_manager_days"] = (
        df["manager_approval_date"] - df["first_submitted_date"]
    ).dt.days

    df["manager_to_accounting_days"] = (
        df["accounting_approval_date"] - df["manager_approval_date"]
    ).dt.days

    df["end_to_end_approval_days"] = (
        df["accounting_approval_date"] - df["first_submitted_date"]
    ).dt.days

    # -----------------------------------------------------------
    # Submission delay interpretation 
    # -----------------------------------------------------------
    df["submission_delay_bucket"] = pd.cut(
        df["submission_delay_days"],
        bins=[-1, 7, 14, np.inf],
        labels=["0-7 days", "8-11 days", "12-14 days"],   
    )

    df["is_late_submission"] = (
        df["submission_delay_days"] > LATE_SUBMISSION_DAYS
    )

    # -----------------------------------------------------------
    # Spend semantics (mapping - driven)
    # -----------------------------------------------------------
 
    # Travel vs Non-Travel (system-controlled)
    df["is_travel_expense"] = (
        df["parent_expense_type"].str.strip().str.lower() == "travel"
    )

    # Customer-facing vs Internal (explicit mapping)
    df["is_customer_facing"] = df["expense_type"].map(
        lambda x: EXPENSE_CLASSIFICATION_MAP.get(
            x, {"is_customer_facing": False}
        )["is_customer_facing"]
    )

    # Internal = not customer-facing
    df["is_internal"] = ~df["is_customer_facing"]

    # ---------------------------------------------
    # FX Insights
    # ---------------------------------------------
    df["fx_variance"] = (
        df["expense_approved_amount_rpt"]
        - df["expense_approved_amount"]
    )

    df["fx_variance_pct"] = np.where(
        df["expense_approved_amount_rpt"] != 0,
        df["fx_variance"] / df["expense_approved_amount_rpt"],
        0,
    )

    df["is_fx_impactful"] = (
        df["fx_variance_pct"].abs() > FX_IMPACT_THRESHOLD
    )

    print("Feature engineering completed")
    return df

    # -------------------------------------------
    # Policy Risk Indicator
    # -------------------------------------------
    df["is_high_amount"] = (
        df["expense_approved_amount_rpt"] > HIGH_AMOUNT_THRESHOLD
    )

    df["is_very_high_amount"] = (
        df["expense_approved_amount_rpt"] > VERY_HIGH_AMOUNT_THRESHOLD
    )

    df["is_policy_risk"] = (
        df["is_late_submission"] | df["is_high_amount"] | df["is_fx_impactful"]
    )
# -----------------------------------------------
# Runner
# -----------------------------------------------
def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
        
    df = pd.read_parquet(INPUT_PATH)
    print(f"Input rows: {len(df)}")


    df_features =  feature_engineering(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_parquet(OUTPUT_PATH, index=False)

    print(f"Feature file written to: {OUTPUT_PATH}")
    print(f"Output rows: {len(df_features)}")

if __name__ == "__main__" :
    main()