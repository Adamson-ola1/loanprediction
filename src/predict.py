"""
src/predict.py
===============
Make predictions using the saved model. Loads the trained sklearn Pipeline
(preprocessing + classifier) and exposes a `LoanDefaultPredictor` class that
turns a *raw* loan application (fields known before a decision is made) into
a default probability. Feature engineering here mirrors src/feature_engineering.py
and notebooks/exploration.ipynb exactly, so training and inference never drift
apart.

Usage:
    from src.predict import LoanDefaultPredictor

    predictor = LoanDefaultPredictor()
    result = predictor.predict(raw_application_dict)
    print(result)

CLI:
    python -m src.predict                       # runs a demo prediction
    python -m src.predict --batch input.csv out.csv
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from src.utils import get_logger, load_joblib, read_csv, save_csv

logger = get_logger(__name__, config.LOGS_DIR / "predict.log")


class LoanDefaultPredictor:
    """Wraps a saved model pipeline + the exact feature engineering used at training time."""

    def __init__(self, model_path: Path | None = None):
        model_path = Path(model_path) if model_path else config.BEST_MODEL_PATH
        self.pipeline = load_joblib(model_path)
        self.feature_names = load_joblib(config.FEATURE_NAMES_PATH)
        self.income_bins = load_joblib(config.INCOME_BINS_PATH)
        logger.info(f"Loaded model from {model_path}")

    # ------------------------------------------------------------------
    # Parsing helpers (raw fields may arrive as strings, e.g. "13.5%")
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_term(term) -> float:
        if isinstance(term, str):
            digits = "".join(ch for ch in term if ch.isdigit())
            return int(digits) if digits else np.nan
        return float(term)

    @staticmethod
    def _parse_percent(value) -> float:
        if isinstance(value, str):
            return float(value.replace("%", "").strip())
        return float(value)

    @staticmethod
    def _parse_date(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return pd.NaT
        if isinstance(value, (pd.Timestamp, datetime)):
            return pd.Timestamp(value)
        return pd.to_datetime(value, format="%b-%y", errors="coerce")

    # ------------------------------------------------------------------
    # Feature engineering (mirrors src/feature_engineering.py)
    # ------------------------------------------------------------------
    def engineer_features(self, raw: dict) -> pd.DataFrame:
        r = dict(raw)  # shallow copy, don't mutate the caller's dict

        term = self._parse_term(r.get("term", 36))
        int_rate = self._parse_percent(r.get("int_rate", 0))
        revol_util = self._parse_percent(r.get("revol_util", 0))

        issue_d = self._parse_date(r.get("issue_d", datetime.today()))
        earliest_cr_line = self._parse_date(r.get("earliest_cr_line"))

        emp_length_raw = r.get("emp_length", "0")
        emp_length_years = config.EMP_LENGTH_MAP.get(emp_length_raw, r.get("emp_length_years", 0))
        if emp_length_years is None:
            emp_length_years = 0

        if emp_length_years <= 2:
            employment_category = "New"
        elif emp_length_years <= 6:
            employment_category = "Mid"
        else:
            employment_category = "Experienced"

        credit_history_years = 0
        if pd.notna(issue_d) and pd.notna(earliest_cr_line):
            credit_history_years = max(issue_d.year - earliest_cr_line.year, 0)

        annual_inc = float(r.get("annual_inc", 0))
        loan_amnt = float(r.get("loan_amnt", 0))
        loan_income_ratio = loan_amnt / annual_inc if annual_inc else 0
        monthly_income = annual_inc / 12

        income_category = pd.cut(
            [annual_inc], bins=self.income_bins, labels=["Low", "Medium", "High"], include_lowest=True
        )[0]
        income_category = str(income_category) if pd.notna(income_category) else "Medium"

        mths_since_last_delinq = r.get("mths_since_last_delinq")
        has_mths_since_last_delinq = int(pd.isna(mths_since_last_delinq))

        features = {
            "loan_amnt": loan_amnt,
            "term": term,
            "int_rate": int_rate,
            "installment": float(r.get("installment", 0)),
            "annual_inc": annual_inc,
            "dti": float(r.get("dti", 0)),
            "delinq_2yrs": float(r.get("delinq_2yrs", 0)),
            "inq_last_6mths": float(r.get("inq_last_6mths", 0)),
            "open_acc": float(r.get("open_acc", 0)),
            "pub_rec": float(r.get("pub_rec", 0)),
            "revol_bal": float(r.get("revol_bal", 0)),
            "revol_util": revol_util,
            "total_acc": float(r.get("total_acc", 0)),
            "pub_rec_bankruptcies": float(r.get("pub_rec_bankruptcies", 0)),
            "has_mths_since_last_delinq": has_mths_since_last_delinq,
            "mths_since_last_delinq": float(mths_since_last_delinq) if mths_since_last_delinq is not None else 0,
            "has_mths_since_last_record": int(pd.isna(r.get("mths_since_last_record"))),
            "emp_length_years": emp_length_years,
            "credit_history_years": credit_history_years,
            "loan_income_ratio": loan_income_ratio,
            "monthly_income": monthly_income,
            "issue_year": issue_d.year if pd.notna(issue_d) else datetime.today().year,
            "issue_month": issue_d.month if pd.notna(issue_d) else datetime.today().month,
            "grade": str(r.get("grade", "c")).lower(),
            "sub_grade": str(r.get("sub_grade", "c1")).lower(),
            "home_ownership": str(r.get("home_ownership", "rent")).lower(),
            "verification_status": str(r.get("verification_status", "not verified")).lower(),
            "purpose": str(r.get("purpose", "debt_consolidation")).lower(),
            "addr_state": str(r.get("addr_state", "ca")).lower(),
            "employment_category": employment_category,
            "income_category": income_category,
        }

        return pd.DataFrame([features])[self.feature_names]

    # ------------------------------------------------------------------
    def predict(self, raw: dict) -> dict:
        X = self.engineer_features(raw)
        proba_default = float(self.pipeline.predict_proba(X)[0, 1])
        prediction = config.POSITIVE_LABEL if proba_default >= 0.5 else config.NEGATIVE_LABEL

        return {
            "prediction": prediction,
            "probability_of_default": round(proba_default, 4),
            "probability_of_full_repayment": round(1 - proba_default, 4),
        }

    def predict_batch(self, raw_rows: list[dict]) -> list[dict]:
        return [self.predict(row) for row in raw_rows]


def _run_demo() -> None:
    predictor = LoanDefaultPredictor()

    sample_applications = [
        {
            "loan_amnt": 12000, "term": "36 months", "int_rate": "13.5%", "installment": 407.5,
            "annual_inc": 55000, "dti": 18.2, "delinq_2yrs": 0, "inq_last_6mths": 1,
            "open_acc": 9, "pub_rec": 0, "revol_bal": 8000, "revol_util": "45%", "total_acc": 22,
            "pub_rec_bankruptcies": 0, "grade": "c", "sub_grade": "c2", "home_ownership": "rent",
            "verification_status": "verified", "purpose": "debt_consolidation", "addr_state": "ca",
            "emp_length": "5 years", "issue_d": "Dec-11", "earliest_cr_line": "Jan-01",
        },
        {
            "loan_amnt": 30000, "term": "60 months", "int_rate": "22.8%", "installment": 837.9,
            "annual_inc": 32000, "dti": 34.5, "delinq_2yrs": 2, "inq_last_6mths": 4,
            "open_acc": 15, "pub_rec": 1, "revol_bal": 21000, "revol_util": "91%", "total_acc": 30,
            "pub_rec_bankruptcies": 1, "grade": "f", "sub_grade": "f3", "home_ownership": "rent",
            "verification_status": "verified", "purpose": "small_business", "addr_state": "fl",
            "emp_length": "< 1 year", "issue_d": "Jun-12", "earliest_cr_line": "Mar-08",
        },
    ]

    for i, application in enumerate(sample_applications, start=1):
        result = predictor.predict(application)
        print(f"Applicant {i}: {result}")


def _run_batch(input_csv: Path, output_csv: Path) -> None:
    predictor = LoanDefaultPredictor()
    df = read_csv(input_csv)
    rows = df.to_dict(orient="records")
    results = predictor.predict_batch(rows)
    results_df = pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)
    save_csv(results_df, output_csv)
    logger.info(f"Wrote batch predictions to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loan default prediction")
    parser.add_argument("--batch", nargs=2, metavar=("INPUT_CSV", "OUTPUT_CSV"), help="Run batch prediction")
    args = parser.parse_args()

    if args.batch:
        _run_batch(Path(args.batch[0]), Path(args.batch[1]))
    else:
        _run_demo()
