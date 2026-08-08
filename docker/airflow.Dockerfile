# ==============================================================================
# docker/airflow.Dockerfile — Airflow image with the project's ML deps baked in
# so DAG tasks can `import src.train`, `import config`, etc. directly.
#
# Build from the project root:
#   docker build -f docker/airflow.Dockerfile -t loan-prediction-airflow .
# ==============================================================================
FROM apache/airflow:2.9.3-python3.12

USER root
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

WORKDIR /opt/airflow

COPY requirements.txt /tmp/requirements.txt
# apache-airflow itself is already provided by the base image.
RUN grep -vi "^apache-airflow" /tmp/requirements.txt > /tmp/requirements.project.txt \
    && pip install --no-cache-dir -r /tmp/requirements.project.txt

# Project code the DAG imports (config.py, src/) plus the DAG itself.
COPY config.py ./config.py
COPY src/ ./src/
COPY airflow/dags/ ./dags/
