"""
src/evaluate.py
================
Evaluate the trained model(s) saved by src/train.py.

Produces:
- outputs/metrics.json                     summary metrics for every model
- outputs/plots/*.png                       confusion matrices, ROC curves,
                                             model comparison chart
- charts/*.png                              copy of the same charts (per the
                                             requested top-level `charts/` dir)
- outputs/predictions.csv                   predictions on the held-out test set

Run directly:
    python -m src.evaluate
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report,
)

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from src.utils import get_logger, load_joblib, save_json

logger = get_logger(__name__, config.LOGS_DIR / "evaluate.log")

sns.set_style("whitegrid")


def _savefig(fig, name: str) -> None:
    """Save a chart to both outputs/plots/ and the top-level charts/ dir."""
    plots_path = config.OUTPUTS_PLOTS_DIR / name
    charts_path = config.CHARTS_DIR / name
    fig.savefig(plots_path, dpi=200, bbox_inches="tight")
    shutil.copyfile(plots_path, charts_path)
    plt.close(fig)


def evaluate_model(model_name: str, pipe, X_test, y_test) -> dict:
    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)
    fpr, tpr, _ = roc_curve(y_test, y_prob)

    logger.info(f"[{model_name}] " + " | ".join(f"{k}={v:.4f}" for k, v in metrics.items()))

    # Confusion matrix chart
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=[config.NEGATIVE_LABEL, config.POSITIVE_LABEL],
        yticklabels=[config.NEGATIVE_LABEL, config.POSITIVE_LABEL],
        ax=ax,
    )
    ax.set_title(f"{model_name} - Confusion Matrix")
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("Actual Label")
    _savefig(fig, f"confusion_matrix_{model_name}.png")

    # ROC curve chart
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, linewidth=2, label=f"{model_name} (AUC = {metrics['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"{model_name} - ROC Curve")
    ax.legend()
    _savefig(fig, f"roc_curve_{model_name}.png")

    with open(config.OUTPUTS_DIR / f"{model_name}_classification_report.txt", "w") as f:
        f.write(report)

    return {**metrics, "confusion_matrix": cm.tolist()}


def plot_model_comparison(results_df: pd.DataFrame) -> None:
    comparison = results_df.set_index("model")
    fig, ax = plt.subplots(figsize=(12, 6))
    comparison[["accuracy", "precision", "recall", "f1_score", "roc_auc"]].plot(
        kind="bar", ax=ax
    )
    ax.set_title("Machine Learning Model Comparison")
    ax.set_ylabel("Score")
    ax.set_xticklabels(comparison.index, rotation=0)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y")
    _savefig(fig, "model_comparison.png")


def run() -> dict:
    model_files = sorted(config.MODELS_DIR.glob("*.pkl"))
    model_names = [
        f.stem for f in model_files
        if f.stem not in {"trained_model", "scaler", "feature_names", "income_bins", "train_test_split"}
    ]
    logger.info(f"Found trained models: {model_names}")

    X_train, X_test, y_train, y_test = load_joblib(config.MODELS_DIR / "train_test_split.pkl")

    all_metrics = {}
    results_rows = []
    best_pipe = None
    best_name = None
    best_auc = -1

    for model_name in model_names:
        pipe = load_joblib(config.MODELS_DIR / f"{model_name}.pkl")
        metrics = evaluate_model(model_name, pipe, X_test, y_test)
        all_metrics[model_name] = metrics
        results_rows.append({"model": model_name, **{k: v for k, v in metrics.items() if k != "confusion_matrix"}})

        if metrics["roc_auc"] > best_auc:
            best_auc = metrics["roc_auc"]
            best_pipe = pipe
            best_name = model_name

    results_df = pd.DataFrame(results_rows).sort_values("roc_auc", ascending=False).reset_index(drop=True)
    results_df.to_csv(config.OUTPUTS_DIR / "model_report.csv", index=False)
    plot_model_comparison(results_df)

    save_json({"best_model": best_name, "models": all_metrics}, config.METRICS_PATH)
    logger.info(f"Saved metrics to {config.METRICS_PATH}")

    # Predictions on the held-out test set using the best model
    test_probs = best_pipe.predict_proba(X_test)[:, 1]
    test_preds = best_pipe.predict(X_test)
    predictions_df = X_test.copy()
    predictions_df["actual"] = y_test.values
    predictions_df["predicted"] = test_preds
    predictions_df["probability_of_default"] = test_probs
    predictions_df.to_csv(config.PREDICTIONS_PATH, index=False)
    logger.info(f"Saved predictions to {config.PREDICTIONS_PATH}")

    logger.info(f"Best model: {best_name} (ROC AUC = {best_auc:.4f})")
    return all_metrics


if __name__ == "__main__":
    run()
