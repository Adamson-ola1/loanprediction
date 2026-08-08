# Deployment Guide

This guide covers deploying the three moving parts of the project: the
**ML pipeline** (training/retraining), the **FastAPI backend**, and the
**React frontend**, plus optional **Airflow** orchestration.

## 1. Environment setup

```bash
git clone <repo-url> ml-project && cd ml-project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Place the raw dataset at `data/raw/data.csv` (never modified in place).

## 2. Train the model

```bash
python main.py                # full pipeline: preprocess -> features -> train -> evaluate
```

Artifacts produced:
- `models/trained_model.pkl`, `models/scaler.pkl`, `models/feature_names.pkl`, `models/income_bins.pkl`
- `outputs/metrics.json`, `outputs/predictions.csv`, `outputs/plots/*.png`
- `charts/*.png`

Verify before deploying:
```bash
python -m src.predict     # runs 2 demo predictions and prints results
```

## 3. Deploy the backend (FastAPI)

### Local / staging
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Production (Docker)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```
```bash
docker build -t loan-prediction-api .
docker run -p 8000:8000 -v $(pwd)/models:/app/models loan-prediction-api
```
Mounting `models/` as a volume lets you retrain and redeploy new models
without rebuilding the image.

### Health & readiness checks
- `GET /health` → `{"status": "ok", "model_loaded": true}` once the model is loaded at startup.
- `GET /model-info` → returns the champion model name and its evaluation metrics.
- Configure your load balancer / orchestrator (k8s, ECS, etc.) to probe `/health`.

### Environment variables / config
All paths and hyperparameters live in `config.py`. For containerized
deployments, either bake `config.py` into the image or override
`CORS_ORIGINS` / `API_PORT` via environment-driven config if you extend
`config.py` to read from `os.environ`.

## 4. Deploy the frontend (React / Vite)

```bash
cd frontend
npm install
```

Set the API base URL in `frontend/.env`:
```
VITE_API_BASE_URL=https://api.your-domain.com
```

### Development
```bash
npm run dev
```

### Production build
```bash
npm run build        # outputs static assets to frontend/dist/
```
Serve `frontend/dist/` with any static host (Nginx, Vercel, Netlify, S3+CloudFront).
Example Nginx config:
```nginx
server {
    listen 80;
    root /var/www/loan-frontend/dist;
    location / {
        try_files $uri /index.html;
    }
    location /api/ {
        proxy_pass http://backend:8000/;
    }
}
```

## 5. Automated retraining (Apache Airflow)

```bash
export AIRFLOW_HOME=~/airflow
pip install apache-airflow
airflow db init
airflow users create --username admin --password admin --firstname A --lastname B --role Admin --email a@b.com

# Make the DAG visible to Airflow
ln -s $(pwd) $AIRFLOW_HOME/dags/ml-project

airflow standalone     # starts webserver + scheduler for local testing
```
Open the Airflow UI (default `http://localhost:8080`), enable the
`loan_default_pipeline` DAG. It runs weekly by default
(`schedule="@weekly"` in `airflow/dags/loan_pipeline_dag.py`) and executes:
`check_new_data → preprocess_data → engineer_features → train_model → evaluate_model → summarize_run`.

For production Airflow, use the `LocalExecutor`/`CeleryExecutor` with a
proper metadata DB (Postgres) instead of the SQLite default, and point
`PROJECT_ROOT` resolution in the DAG file at wherever the repo is checked
out on your workers.

## 6. Monitoring & retraining triggers

- Drop new data into `data/raw/data.csv` (append or replace) — the next
  Airflow run (or a manual `python main.py`) will retrain on it.
- Track `outputs/metrics.json` over time (e.g. commit it to git, or push to
  a metrics store) to watch for model drift.
- Consider adding a model registry (MLflow, Weights & Biases) if you need
  full experiment tracking and rollback across model versions.

## 7. Rollback

Every trained model per algorithm is kept (`models/LogisticRegression.pkl`,
`models/RandomForest.pkl`, `models/XGBoost.pkl`) in addition to the
selected champion (`models/trained_model.pkl`). To roll back, copy the
desired `models/<Model>.pkl` over `models/trained_model.pkl` and restart
the backend (or point `LoanDefaultPredictor(model_path=...)` at the
specific file).
