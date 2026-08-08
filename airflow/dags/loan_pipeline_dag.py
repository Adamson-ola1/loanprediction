"""
airflow/dags/loan_pipeline_dag.py
==================================
Apache Airflow DAG that automates the loan-default ML pipeline:

    check_new_data -> preprocess -> feature_engineering -> train -> evaluate -> notify

Schedule: runs weekly by default (change `schedule` below as needed). Each task
is a PythonOperator calling straight into the project's src/ modules, so the
DAG stays a thin orchestration layer — all real logic lives in src/.

Setup:
    1. export AIRFLOW_HOME=~/airflow  (or wherever you keep it)
    2. Symlink or copy this file (and the project root) so PROJECT_ROOT below
       resolves correctly, e.g.:
           ln -s /path/to/ml-project $AIRFLOW_HOME/dags/ml-project
    3. `airflow dags list` should show `loan_default_pipeline`
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.trigger_rule import TriggerRule

# ----------------------------------------------------------------------
# Make the project importable from inside Airflow's worker process
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import config  # noqa: E402


def _check_new_data(**context) -> bool:
    """Sanity-check that the raw data file exists and is non-empty before running the pipeline."""
    from src.utils import get_logger

    logger = get_logger("airflow.check_new_data")
    if not config.RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data not found at {config.RAW_DATA_PATH}")

    size_mb = config.RAW_DATA_PATH.stat().st_size / (1024 * 1024)
    logger.info(f"Found raw data at {config.RAW_DATA_PATH} ({size_mb:.1f} MB)")
    return True


def _preprocess(**context):
    from src import preprocess
    preprocess.run()


def _feature_engineering(**context):
    from src import feature_engineering
    feature_engineering.run()


def _train(**context):
    from src import train
    best_model = train.run()
    context["ti"].xcom_push(key="best_model", value=best_model)


def _evaluate(**context):
    from src import evaluate
    metrics = evaluate.run()
    context["ti"].xcom_push(key="metrics", value=metrics)


def _summarize(**context):
    """Print a short run summary to the task logs (visible in the Airflow UI)."""
    ti = context["ti"]
    best_model = ti.xcom_pull(task_ids="train_model", key="best_model")
    metrics = ti.xcom_pull(task_ids="evaluate_model", key="metrics") or {}
    best_metrics = metrics.get(best_model, {})
    print(f"Pipeline run complete. Best model: {best_model}")
    print(f"Metrics: {best_metrics}")


default_args = {
    "owner": "ml-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="loan_default_pipeline",
    description="Automatically loads new loan data and retrains the default-prediction model",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",   # change to e.g. "0 2 * * *" for daily at 2am
    catchup=False,
    max_active_runs=1,
    tags=["ml", "loan-prediction"],
) as dag:

    check_new_data = PythonOperator(
        task_id="check_new_data",
        python_callable=_check_new_data,
    )

    preprocess_data = PythonOperator(
        task_id="preprocess_data",
        python_callable=_preprocess,
    )

    engineer_features = PythonOperator(
        task_id="engineer_features",
        python_callable=_feature_engineering,
    )

    train_model = PythonOperator(
        task_id="train_model",
        python_callable=_train,
    )

    evaluate_model = PythonOperator(
        task_id="evaluate_model",
        python_callable=_evaluate,
    )

    summarize_run = PythonOperator(
        task_id="summarize_run",
        python_callable=_summarize,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    (
        check_new_data
        >> preprocess_data
        >> engineer_features
        >> train_model
        >> evaluate_model
        >> summarize_run
    )
