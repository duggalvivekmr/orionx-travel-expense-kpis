import pandas as pd
from pathlib import Path

# ---------------------------------
# Paths
# ---------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT /"data" / "raw"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"

RAW_FILE_NAME = "OrionX_Labs_Travel_Expense_Final_70000.xlsx"
OUTPUT_FILE_NAME = "expense_cleaned.parquet"

# ---------------------------------
# Configuration
# ---------------------------------
DATE_COLUMNS = [
    "transaction_date",
    "first_submitted_date",
    "manager_approval_date",
    "accounting_approval_date",
]

REQUIRED_COLUMNS = [
    "employee_id",
    "department_name",
    "job_family",
    "parent_expense_type",
    "expense_type",
    "expense_approved_amount",
    "expense_approved_amount_rpt",
    "reimbursement_currency",
    "reporting_currency",
    "transaction_date",
]

VALID_PARENT_EXPENSE_TYPES = {"Travel", "Non-Travel"}
REPORTING_CURRENCY = "USD"

# ---------------------------------
# Helper Functions
# ---------------------------------
def load_raw_data () -> pd.DataFrame:
    """ Load raw expense data from Excel. """
    file_path = RAW_DATA_PATH / RAW_FILE_NAME
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    df = pd.read_excel(file_path)
    return df

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to snake_case:
     - lowercase
     - remove special characters ((), &, -, /, etc.)
     - replace spaces & symbols with underscore
     """
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    ) 
    return df

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date columns safely."""
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def validate_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required columns are present in the DataFrame."""
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
def validate_currencies(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure reporting currency is USD."""
    invalid_currency_rows = df[df["reporting_currency"] != REPORTING_CURRENCY]
    if not invalid_currency_rows.empty:
        print(
            f"Warning: {len(invalid_currency_rows)} rows have non-USD reporting currency."
        )
    return df

def validate_amounts (df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with invalid or negative amounts."""
    df = df[
        (df["expense_approved_amount"] >= 0)
        & (df["expense_approved_amount_rpt"] >= 0)
    ]
    return df

def validate_parent_expense_type(df: pd.DataFrame) -> pd.DataFrame:
    """Validate parent expense types."""
    df = df[df["parent_expense_type"].isin(VALID_PARENT_EXPENSE_TYPES)]
    return df

def derive_submission_delay(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate submission delay to ensure correctness."""
    df["submission_delay_days"] = (df["first_submitted_date"] - df["transaction_date"]).dt.days
    return df

def remove_duplicates (df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate expense entries."""
    return df.drop_duplicates()

# ----------------------------------------
# Main Pipeline
# ----------------------------------------

def main(): 
    print("Starting data cleaning pipeline...")

    df = load_raw_data()
    print(f"Raw records: {len(df)}")

    df = standardize_column_names(df)
    validate_required_columns(df)
    print(sorted(df.columns.tolist()))

    df = parse_dates(df)
    df = validate_currencies(df)
    df = validate_amounts(df)
    df = validate_parent_expense_type(df)
    df = derive_submission_delay(df)
    df = remove_duplicates(df)

    PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DATA_PATH / OUTPUT_FILE_NAME
    df.to_parquet (output_path, index=False)

    print(f"Cleaned records: {len(df)}")
    print(f"Processed data saved to: {output_path}")

if __name__ == "__main__":
    main()