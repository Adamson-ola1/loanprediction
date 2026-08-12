"""
config.py
=========
Single source of truth for paths, hyperparameters and constants used across
the whole project (src/, backend/, airflow/). Nothing here should require
importing pandas/sklearn so it stays cheap to import anywhere.
"""

from pathlib import Path

# ----------------------------------------------------------------------
# Project paths
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

RAW_DATA_PATH = RAW_DATA_DIR / "data.csv"
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "processed_data.csv"

MODELS_DIR = PROJECT_ROOT / "models"
BEST_MODEL_PATH = MODELS_DIR / "trained_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"  # kept for the requested naming convention
FEATURE_NAMES_PATH = MODELS_DIR / "feature_names.pkl"
INCOME_BINS_PATH = MODELS_DIR / "income_bins.pkl"
MODEL_COMPARISON_PATH = MODELS_DIR / "model_comparison.json"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_PLOTS_DIR = OUTPUTS_DIR / "plots"
PREDICTIONS_PATH = OUTPUTS_DIR / "predictions.csv"
METRICS_PATH = OUTPUTS_DIR / "metrics.json"

CHARTS_DIR = PROJECT_ROOT / "charts"

DOCS_DIR = PROJECT_ROOT / "docs"
LOGS_DIR = PROJECT_ROOT / "logs"

for _d in (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR, MODELS_DIR,
    OUTPUTS_DIR, OUTPUTS_PLOTS_DIR, CHARTS_DIR, DOCS_DIR, LOGS_DIR,
):
    _d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Target / task
# ----------------------------------------------------------------------
TARGET_COLUMN = "loan_status"
POSITIVE_LABEL = "Charged Off"   # maps to 1 (the loan defaulted)
NEGATIVE_LABEL = "Fully Paid"    # maps to 0 (loan fully repaid)
VALID_LOAN_STATUSES = [NEGATIVE_LABEL, POSITIVE_LABEL]

RANDOM_STATE = 42
TEST_SIZE = 0.2

# ----------------------------------------------------------------------
# Columns dropped during cleaning (mirrors notebooks/exploration.ipynb)
# ----------------------------------------------------------------------
ID_TEXT_COLS = ["id", "member_id", "url", "desc", "emp_title", "title", "zip_code"]

LEAKAGE_COLS = [
    "funded_amnt", "funded_amnt_inv",
    "out_prncp", "out_prncp_inv",
    "total_pymnt", "total_pymnt_inv", "total_rec_prncp",
    "total_rec_int", "total_rec_late_fee",
    "recoveries", "collection_recovery_fee",
    "last_pymnt_d", "last_pymnt_amnt",
    "next_pymnt_d", "last_credit_pull_d",
    "collections_12_mths_ex_med",
]

OUTLIER_COLS = ["annual_inc", "loan_amnt", "dti", "int_rate"]
HIGH_MISSING_THRESHOLD = 50.0  # percent

# ----------------------------------------------------------------------
# Feature engineering constants
# ----------------------------------------------------------------------
EMP_LENGTH_MAP = {
    "< 1 year": 0, "1 year": 1, "2 years": 2, "3 years": 3, "4 years": 4,
    "5 years": 5, "6 years": 6, "7 years": 7, "8 years": 8, "9 years": 9,
    "10+ years": 10,
}

EMPLOYMENT_CATEGORY_BINS = [-1, 2, 6, 10]
EMPLOYMENT_CATEGORY_LABELS = ["New", "Mid", "Experienced"]

INCOME_CATEGORY_QUANTILES = 3
INCOME_CATEGORY_LABELS = ["Low", "Medium", "High"]

NUMERIC_FEATURES = [
    "loan_amnt", "term", "int_rate", "installment", "annual_inc", "dti",
    "delinq_2yrs", "inq_last_6mths", "open_acc", "pub_rec", "revol_bal",
    "revol_util", "total_acc", "pub_rec_bankruptcies",
    "has_mths_since_last_delinq", "mths_since_last_delinq",
    "has_mths_since_last_record", "emp_length_years", "credit_history_years",
    "loan_income_ratio", "monthly_income", "issue_year", "issue_month",
]

CATEGORICAL_FEATURES = [
    "grade", "sub_grade", "home_ownership", "verification_status", "purpose",
    "addr_state", "employment_category", "income_category",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# ----------------------------------------------------------------------
# Model hyperparameters
# ----------------------------------------------------------------------
LOGISTIC_REGRESSION_PARAMS = dict(
    random_state=RANDOM_STATE, max_iter=1000, class_weight="balanced",
)

RANDOM_FOREST_PARAMS = dict(
    n_estimators=200, max_depth=12, min_samples_leaf=20,
    random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced_subsample",
)

XGBOOST_PARAMS = dict(
    random_state=RANDOM_STATE, eval_metric="logloss", n_estimators=300,
)

# ----------------------------------------------------------------------
# API / backend
# ----------------------------------------------------------------------
API_TITLE = "Loan Default Prediction API"
API_VERSION = "1.0.0"
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://loanprediction-frontend.onrender.com",
]
