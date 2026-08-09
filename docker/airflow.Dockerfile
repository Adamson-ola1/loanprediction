# ==============================================================================
# docker/airflow.Dockerfile — Airflow image with the project's ML deps baked in
# so DAG tasks can `import src.train`, `import config`, etc. directly.
#
# Build from the project root:
#   docker build -f docker/airflow.Dockerfile -t loan-prediction-airflow .
# ==============================================================================
FROM apache/airflow:2.10.5-python3.11

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

USER airflow

WORKDIR /opt/loanprediction

# Install project dependencies
COPY --chown=airflow:root requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy project code required by the DAG
COPY --chown=airflow:root src/ ./src/
COPY --chown=airflow:root models/ ./models/
COPY --chown=airflow:root config.py .
COPY --chown=airflow:root airflow/ ./airflow/

# Make project importable
ENV PYTHONPATH=/opt/loanprediction

# Airflow configuration
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False

EXPOSE 8080

CMD ["airflow", "webserver"]

CMD ["airflow", "webserver"]
