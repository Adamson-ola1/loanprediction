"""
src/feature_engineering.py
===========================
Feature creation and selection. Mirrors "SECTION 3: FEATURE ENGINEERING"
of notebooks/exploration.ipynb:

1. Encode the target (loan_status) as binary: fully paid = 0, charged off = 1
2. Employment length -> numeric years (+ employment_category bucket)
3. Credit history length (issue_d - earliest_cr_line, in years)
4. Loan-to-income ratio & monthly income
5. Income category (Low / Medium / High, via qcut)
6. Extract issue year / month

Run directly:
    python -m src.feature_engineering
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from src.utils import get_logger, read_csv, save_csv, save_joblib

logger = get_logger(__name__, config.LOGS_DIR / "feature_engineering.log")


def encode_target(df: pd.DataFrame) -> pd.DataFrame:
    df[config.TARGET_COLUMN] = df[config.TARGET_COLUMN].map(
        {"fully paid": 0, "charged off": 1}
    )
    return df


def add_employment_features(df: pd.DataFrame) -> pd.DataFrame:
    df["emp_length_years"] = df["emp_length"].map(config.EMP_LENGTH_MAP)
    df["emp_length_years"] = df["emp_length_years"].fillna(df["emp_length_years"].median())

    df["employment_category"] = pd.cut(
        df["emp_length_years"],
        bins=config.EMPLOYMENT_CATEGORY_BINS,
        labels=config.EMPLOYMENT_CATEGORY_LABELS,
    ).astype(str)
    return df


def add_credit_history_length(df: pd.DataFrame) -> pd.DataFrame:
    df["credit_history_years"] = df["issue_d"].dt.year - df["earliest_cr_line"].dt.year
    df["credit_history_years"] = df["credit_history_years"].clip(lower=0)
    df["credit_history_years"] = df["credit_history_years"].fillna(
        df["credit_history_years"].median()
    )
    return df


def add_income_features(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    df["loan_income_ratio"] = df["loan_amnt"] / df["annual_inc"].replace(0, np.nan)
    df["loan_income_ratio"] = df["loan_income_ratio"].fillna(df["loan_income_ratio"].median())

    df["monthly_income"] = df["annual_inc"] / 12

    df["income_category"], income_bins = pd.qcut(
        df["annual_inc"],
        q=config.INCOME_CATEGORY_QUANTILES,
        labels=config.INCOME_CATEGORY_LABELS,
        retbins=True,
    )
    df["income_category"] = df["income_category"].astype(str)
    logger.info(f"Income bin edges (for consistent use at inference time): {income_bins}")
    return df, income_bins


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    df["issue_year"] = df["issue_d"].dt.year
    df["issue_month"] = df["issue_d"].dt.month
    return df


def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Run the full feature engineering pipeline. Returns (df, income_bins)."""
    df = encode_target(df)
    df = add_employment_features(df)
    df = add_credit_history_length(df)
    df, income_bins = add_income_features(df)
    df = add_date_features(df)

    missing_features = [c for c in config.FEATURES if c not in df.columns]
    assert not missing_features, f"Missing engineered columns: {missing_features}"

    logger.info(
        f"{len(config.NUMERIC_FEATURES)} numeric + {len(config.CATEGORICAL_FEATURES)} "
        f"categorical = {len(config.FEATURES)} total features"
    )
    return df, income_bins


def run(
    input_path: Path = config.PROCESSED_DATA_PATH,
    output_path: Path = config.PROCESSED_DATA_PATH,
) -> pd.DataFrame:
    logger.info(f"Loading cleaned data from {input_path}")
    df = read_csv(input_path, parse_dates=["issue_d", "earliest_cr_line"])

    df, income_bins = engineer_features(df)

    save_joblib(income_bins, config.INCOME_BINS_PATH)
    logger.info(f"Saved income_bins.pkl to {config.INCOME_BINS_PATH}")

    save_csv(df, output_path)
    logger.info(f"Saved feature-engineered dataset to {output_path} -> shape {df.shape}")
    return df


if __name__ == "__main__":
    run()
