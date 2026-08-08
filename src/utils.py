"""
src/utils.py
============
Common helper functions shared across preprocess.py, feature_engineering.py,
train.py, evaluate.py and predict.py.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def get_logger(name: str, log_file: str | Path | None = None) -> logging.Logger:
    """Return a logger that writes to stdout (and optionally a file)."""
    logger = logging.getLogger(name)
    if logger.handlers:  # avoid duplicate handlers on re-import
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    if log_file is not None:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


def save_json(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)


def load_json(path: str | Path) -> Any:
    with open(path) as f:
        return json.load(f)


def save_joblib(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)


def load_joblib(path: str | Path) -> Any:
    return joblib.load(path)


def read_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    kwargs.setdefault("low_memory", False)
    return pd.read_csv(path, **kwargs)


def save_csv(df: pd.DataFrame, path: str | Path, index: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def dataframe_missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return a table of columns with missing values, sorted descending."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    report = (
        pd.DataFrame({"Missing": missing, "Percent": missing_pct})
        .query("Missing > 0")
        .sort_values("Missing", ascending=False)
    )
    return report
