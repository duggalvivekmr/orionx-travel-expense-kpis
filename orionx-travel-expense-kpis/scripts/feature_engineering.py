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
# Expense classification mapping
# -------------------------------

EXPENSE_CLASSIFICATION_MAP = {

    # --------------------------------------------------
    # AIRFARE (Travel)
    # --------------------------------------------------
    "Airfare – Company Event": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Airfare"
    },
    "Airfare – Conference": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Airfare"
    },
    "Airfare – Customer Facing": {
        "is_travel": True,
        "is_customer_facing": True,
        "category": "Airfare"
    },
    "Airfare – Internal": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Airfare"
    },
    "Airfare – Offsite": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Airfare"
    },

    # --------------------------------------------------
    # HOTEL (Travel)
    # --------------------------------------------------
    "Hotel – Conference": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Hotel"
    },
    "Hotel – Customer Facing": {
        "is_travel": True,
        "is_customer_facing": True,
        "category": "Hotel"
    },
    "Hotel – Internal": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Hotel"
    },

    # --------------------------------------------------
    # MEALS (Travel)
    # --------------------------------------------------
    "Meal – Conference": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Meal"
    },
    "Meal – Customer Facing": {
        "is_travel": True,
        "is_customer_facing": True,
        "category": "Meal"
    },
    "Meal – Internal": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Meal"
    },

    # --------------------------------------------------
    # GROUND / TRANSPORTATION (Travel)
    # --------------------------------------------------
    "Ground Transportation – Customer Facing": {
        "is_travel": True,
        "is_customer_facing": True,
        "category": "Ground Transport"
    },
    "Transportation – Internal": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Ground Transport"
    },
    "Car – Internal": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Ground Transport"
    },
    "Fuel / Gas Charges": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Ground Transport"
    },
    "Mileage – Personal Car": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Ground Transport"
    },
    "Parking and Tolls": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Ground Transport"
    },

    # --------------------------------------------------
    # NON-TRAVEL EXPENSES
    # --------------------------------------------------
    "Bank / FX Fees": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Financial Charges"
    },
    "Computer/Laptop Accessories": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "IT Equipment"
    },
    "Donation": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Other"
    },
    "Education": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Training"
    },
    "Entertainment": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Entertainment"
    },
    "Gifts": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Other"
    },
    "Internet": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Utilities"
    },
    "Office Expense": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Office"
    },
    "Relocation Expense": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "HR"
    },
    "Seminars, & Conferences": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Training"
    },
    "Software and Software Subscription": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "Software"
    },
    "Taxable Award": {
        "is_travel": False,
        "is_customer_facing": False,
        "category": "HR"
    },

    # --------------------------------------------------
    # TRAVEL UTILITIES (Travel)
    # --------------------------------------------------
    "Travel Internet": {
        "is_travel": True,
        "is_customer_facing": False,
        "category": "Travel Utility"
    }
}

# ----------------------------------------------------------
# Expense classification function
# ----------------------------------------------------------

def apply_expense_classification(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df["is_travel"] = True
    df["is_customer_facing"] = True
    df["expense_category"] = "Other"

    for expense_type, rules in EXPENSE_CLASSIFICATION_MAP.items():
        mask = df["expense_type"] == expense_type

        if "is_travel" in rules:
            df.loc[mask, "is_travel"] = rules["is_travel"]

        if "is_customer_facing" in rules:
            df.loc[mask, "is_customer_facing"] = rules["is_customer_facing"]

        if "category" in rules:
            df.loc[mask, "expense_category"] = rules["category"]
    return df
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
        bins=[-1, 7, 11, np.inf],
        labels=["0-7 days", "8-11 days", "12+ days"],   
    )

    df["is_late_submission"] = (
        df["submission_delay_days"] > LATE_SUBMISSION_DAYS
    )

    # -----------------------------------------------------------
    # Spend semantics (mapping - driven)
    # -----------------------------------------------------------

    # Spend semantics (mapping - driven)
    df = apply_expense_classification(df)
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
    
    print("Feature engineering completed")
    return df
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