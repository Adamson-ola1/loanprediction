"""
src/preprocess.py
==================
Data cleaning and preprocessing for the Lending Club loan dataset.
Mirrors "SECTION 2: DATA CLEANING" of notebooks/exploration.ipynb:

1. Keep only resolved loans (Fully Paid / Charged Off)
2. Remove duplicate records
3. Remove leakage / irrelevant / redundant columns
4. Handle missing values (indicators, median/mode imputation, drop high-missing cols)
5. Convert data types (dates, percentages, term)
6. Detect and treat outliers (IQR method)
7. Standardize categorical text
8. Check for invalid values

Run directly:
    python -m src.preprocess
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from src.utils import get_logger, read_csv, save_csv, dataframe_missing_report

logger = get_logger(__name__, config.LOGS_DIR / "preprocess.log")


def load_raw_data(path: Path = config.RAW_DATA_PATH) -> pd.DataFrame:
    logger.info(f"Loading raw data from {path}")
    df = read_csv(path)
    logger.info(f"Raw shape: {df.shape}")
    return df


def filter_resolved_loans(df: pd.DataFrame) -> pd.DataFrame:
    """Current loans have no final outcome yet -> drop them."""
    before = df.shape[0]
    df = df[df[config.TARGET_COLUMN].isin(config.VALID_LOAN_STATUSES)].copy()
    logger.info(f"Kept only {config.VALID_LOAN_STATUSES}: {before} -> {df.shape[0]} rows")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = df.shape[0]
    df = df.drop_duplicates()
    logger.info(f"Removed {before - df.shape[0]} duplicate rows -> shape: {df.shape}")
    return df


def drop_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop IDs/free-text/links, post-outcome leakage columns, and constant columns."""
    constant_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
    logger.info(f"Constant columns found: {constant_cols}")

    drop_cols = config.ID_TEXT_COLS + config.LEAKAGE_COLS + constant_cols
    df = df.drop(columns=drop_cols, errors="ignore")
    logger.info(f"Dropped {len(drop_cols)} columns -> shape: {df.shape}")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    report = dataframe_missing_report(df)
    logger.info(f"Missing value report (top 10):\n{report.head(10)}")

    # Missing here is itself informative (no recorded delinquency/public record)
    df["has_mths_since_last_delinq"] = df["mths_since_last_delinq"].isna().astype(int)
    df["has_mths_since_last_record"] = df["mths_since_last_record"].isna().astype(int)

    df["mths_since_last_delinq"] = df["mths_since_last_delinq"].fillna(
        df["mths_since_last_delinq"].median()
    )

    # Drop remaining columns still missing more than the threshold
    missing_pct_now = df.isnull().mean() * 100
    high_missing_cols = missing_pct_now[missing_pct_now > config.HIGH_MISSING_THRESHOLD].index.tolist()
    df = df.drop(columns=high_missing_cols)
    logger.info(
        f"Dropped {len(high_missing_cols)} columns with >{config.HIGH_MISSING_THRESHOLD}% "
        f"missing values -> shape: {df.shape}"
    )

    # Numeric: median impute. Categorical: mode impute.
    num_cols = df.select_dtypes(include=["int64", "float64"]).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    cat_cols = df.select_dtypes(include="object").columns
    for col in cat_cols:
        mode = df[col].mode()
        if not mode.empty:
            df[col] = df[col].fillna(mode.iloc[0])

    logger.info(f"Remaining missing values: {df.isnull().sum().sum()}")
    return df


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%y", errors="coerce")
    df["earliest_cr_line"] = pd.to_datetime(df["earliest_cr_line"], format="%b-%y", errors="coerce")

    for col in ["int_rate", "revol_util"]:
        df[col] = df[col].astype(str).str.replace("%", "", regex=False).astype(float)

    df["term"] = df["term"].astype(str).str.extract(r"(\d+)").astype(int)
    return df


def treat_outliers(df: pd.DataFrame) -> pd.DataFrame:
    for col in config.OUTLIER_COLS:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        before = df.shape[0]
        df = df[(df[col] >= lower) & (df[col] <= upper)]
        logger.info(
            f"{col:12s} removed {before - df.shape[0]:5d} rows outside [{lower:,.2f}, {upper:,.2f}]"
        )
    logger.info(f"Shape after outlier removal: {df.shape}")
    return df


def standardize_categorical_text(df: pd.DataFrame) -> pd.DataFrame:
    text_cols = df.select_dtypes(include="object").columns
    for col in text_cols:
        df[col] = df[col].str.strip().str.lower()
    return df


def check_invalid_values(df: pd.DataFrame) -> pd.DataFrame:
    before = df.shape[0]
    df = df[
        (df["annual_inc"] >= 0)
        & (df["loan_amnt"] >= 0)
        & (df["int_rate"] >= 0)
        & (df["dti"] >= 0)
    ]
    logger.info(f"Removed {before - df.shape[0]} rows with invalid negative values -> shape: {df.shape}")
    return df


def clean_data(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run the full cleaning pipeline and return the cleaned dataframe."""
    if df is None:
        df = load_raw_data()

    df = filter_resolved_loans(df)
    df = remove_duplicates(df)
    df = drop_irrelevant_columns(df)
    df = handle_missing_values(df)
    df = convert_data_types(df)
    df = treat_outliers(df)
    df = standardize_categorical_text(df)
    df = check_invalid_values(df)

    logger.info(f"Final cleaned shape: {df.shape}")
    return df


def run(save_path: Path = config.PROCESSED_DATA_PATH) -> pd.DataFrame:
    df = clean_data()
    save_csv(df, save_path)
    logger.info(f"Saved cleaned dataset to {save_path}")
    return df


if __name__ == "__main__":
    run()
