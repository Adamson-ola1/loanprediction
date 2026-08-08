"""
src/train.py
============
Train the machine learning models. Mirrors "SECTION 4: MODEL TRAINING &
EVALUATION" (training half) of notebooks/exploration.ipynb:

1. Train / test split (stratified)
2. Preprocessing (median-impute + scale numeric, mode-impute + one-hot encode
   categorical) fit only on the training set, inside a sklearn Pipeline
3. Train Logistic Regression, Random Forest and XGBoost
4. Persist every trained pipeline + the best one (by ROC AUC) + supporting
   artifacts (feature_names.pkl, income_bins.pkl already saved by
   feature_engineering.py)

Run directly:
    python -m src.train
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from src.utils import get_logger, read_csv, save_joblib

logger = get_logger(__name__, config.LOGS_DIR / "train.log")


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]), config.NUMERIC_FEATURES),

            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]), config.CATEGORICAL_FEATURES),
        ]
    )


def build_models(y_train: pd.Series) -> dict:
    neg, pos = y_train.value_counts()[0], y_train.value_counts()[1]
    scale_pos_weight = neg / pos
    logger.info(f"scale_pos_weight (for XGBoost): {scale_pos_weight:.2f}")

    return {
        "LogisticRegression": LogisticRegression(**config.LOGISTIC_REGRESSION_PARAMS),
        "RandomForest": RandomForestClassifier(**config.RANDOM_FOREST_PARAMS),
        "XGBoost": XGBClassifier(scale_pos_weight=scale_pos_weight, **config.XGBOOST_PARAMS),
    }


def split_data(df: pd.DataFrame):
    X = df[config.FEATURES].copy()
    y = df[config.TARGET_COLUMN].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE, stratify=y,
    )
    logger.info(f"Train: {X_train.shape}  Test: {X_test.shape}")
    logger.info(f"Train class balance:\n{y_train.value_counts(normalize=True).round(3)}")
    return X_train, X_test, y_train, y_test


def train_all_models(X_train, y_train, X_test, y_test) -> tuple[dict, dict]:
    """Fit every model wrapped in a full Pipeline. Returns (pipelines, test_scores)."""
    preprocessor = build_preprocessor()
    models = build_models(y_train)

    trained_pipelines = {}
    test_scores = {}

    for model_name, model in models.items():
        logger.info("=" * 80)
        logger.info(f"Training {model_name}")
        pipe = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", model),
        ])
        pipe.fit(X_train, y_train)
        trained_pipelines[model_name] = pipe

        y_prob = pipe.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        test_scores[model_name] = auc
        logger.info(f"{model_name} ROC AUC on held-out test set: {auc:.4f}")

    return trained_pipelines, test_scores


def save_models(trained_pipelines: dict, test_scores: dict) -> str:
    for model_name, pipe in trained_pipelines.items():
        save_joblib(pipe, config.MODELS_DIR / f"{model_name}.pkl")
        logger.info(f"Saved {model_name}.pkl")

    best_model_name = max(test_scores, key=test_scores.get)
    best_pipeline = trained_pipelines[best_model_name]

    save_joblib(best_pipeline, config.BEST_MODEL_PATH)
    # Also persist just the fitted preprocessing step under the requested
    # "scaler.pkl" name (imputers + StandardScaler + OneHotEncoder), useful
    # for anyone who wants to transform features without the classifier.
    save_joblib(best_pipeline.named_steps["preprocessor"], config.SCALER_PATH)
    save_joblib(config.FEATURES, config.FEATURE_NAMES_PATH)

    logger.info(f"Best model: {best_model_name} (ROC AUC = {test_scores[best_model_name]:.4f})")
    logger.info(f"Saved as {config.BEST_MODEL_PATH}")
    return best_model_name


def run() -> str:
    logger.info(f"Loading feature-engineered data from {config.PROCESSED_DATA_PATH}")
    df = read_csv(config.PROCESSED_DATA_PATH, parse_dates=["issue_d", "earliest_cr_line"])

    X_train, X_test, y_train, y_test = split_data(df)
    trained_pipelines, test_scores = train_all_models(X_train, y_train, X_test, y_test)
    best_model_name = save_models(trained_pipelines, test_scores)

    # Persist the split so evaluate.py can reproduce metrics/plots without retraining
    save_joblib((X_train, X_test, y_train, y_test), config.MODELS_DIR / "train_test_split.pkl")

    return best_model_name


if __name__ == "__main__":
    run()
