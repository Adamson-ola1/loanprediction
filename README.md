# Loan Default Prediction — End-to-End ML Project

Predicts the probability that a loan will **default (Charged Off)** based on
borrower and loan characteristics known **at application time**, built from
the analysis in `notebooks/exploration.ipynb`.

**Pipeline:** Preprocess → Feature Engineering → Train → Evaluate → Serve (API) → Visualize (React dashboard)

---

## Project structure

```
ml-project/
├── backend/            FastAPI app (main.py, schema.py)
├── charts/              PNG charts copied from src/evaluate.py
├── data/
│   ├── raw/              data.csv (original, never modified)
│   ├── processed/        processed_data.csv (cleaned + engineered)
│   └── external/         room for external/enrichment data
├── docs/                 deployment guide, model card, technical report
├── frontend/             React (Vite) dashboard
├── notebooks/            exploration.ipynb (source of truth for the analysis)
├── models/               trained_model.pkl, scaler.pkl, feature_names.pkl, income_bins.pkl
├── outputs/              predictions.csv, metrics.json, plots/
├── airflow/dags/         loan_pipeline_dag.py (automated retraining)
├── src/
│   ├── preprocess.py
│   ├── feature_engineering.py
│   ├── train.py
│   ├── evaluate.py
│   ├── predict.py
│   └── utils.py
├── config.py
├── requirements.txt
├── main.py               entry point: runs the full pipeline
└── README.md
```

## Quickstart

### 1. Install dependencies
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the full ML pipeline
```bash
python main.py                  # preprocess -> features -> train -> evaluate
python main.py --stage train    # or run a single stage
```
This populates `data/processed/`, `models/`, `outputs/`, and `charts/`.

### 3. Serve predictions via the API
```bash
uvicorn backend.main:app --reload --port 8000
```
Open `http://localhost:8000/docs` for interactive Swagger docs.

Example request:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
        "loan_amnt": 12000, "term": "36 months", "int_rate": "13.5%",
        "installment": 407.5, "annual_inc": 55000, "dti": 18.2,
        "grade": "C", "sub_grade": "C2", "home_ownership": "RENT",
        "verification_status": "Verified", "purpose": "debt_consolidation",
        "addr_state": "CA", "emp_length": "5 years",
        "issue_d": "Dec-11", "earliest_cr_line": "Jan-01"
      }'
```

### 4. Run the frontend dashboard
```bash
cd frontend
npm install
npm run dev
```
Configure the API base URL in `frontend/.env` (`VITE_API_BASE_URL`).

### 5. Automate retraining with Airflow
```bash
export AIRFLOW_HOME=~/airflow
airflow db init
ln -s $(pwd) $AIRFLOW_HOME/dags/ml-project
airflow standalone   # or: airflow scheduler / airflow webserver -p 8080
```
The `loan_default_pipeline` DAG (in `airflow/dags/loan_pipeline_dag.py`) runs
`check_new_data → preprocess → feature_engineering → train → evaluate → summarize`
on a weekly schedule by default.

## Model

Three classifiers are trained and compared by ROC AUC: Logistic Regression,
Random Forest, and XGBoost — all wrapped in a single `sklearn.Pipeline`
(imputation + scaling/one-hot-encoding + classifier) so preprocessing can
never drift between training and inference. See `docs/model_card.md` for
details and `docs/technical_report.md` for the full methodology.

## Docker & CI/CD

```
.github/workflows/ci.yml   Lints + tests the backend, smoke-tests the ML
                            pipeline end-to-end, lints + builds the frontend,
                            builds both Docker images, and (on `main`) pushes
                            them to GHCR.
Dockerfile                 Multi-stage build for the FastAPI backend/API.
.dockerignore
docker/
├── docker-compose.yml     Full stack: Postgres + API + frontend + Airflow.
├── .env.example           Connection settings — copy to docker/.env and
│                           fill in real DB/Airflow credentials (git-ignored).
├── frontend.Dockerfile    Builds the React app, serves it via nginx.
├── airflow.Dockerfile     Airflow image with the project's src/ baked in.
└── nginx.conf             Frontend nginx config (SPA routing + /api proxy).
```

Run the whole stack locally:
```bash
cp docker/.env.example docker/.env      # then edit docker/.env with real credentials
docker compose -f docker/docker-compose.yml --env-file docker/.env up --build
```
- API → http://localhost:8000 (docs at `/docs`)
- Frontend → http://localhost:5173
- Airflow UI → http://localhost:8080

Or build/run just the API image:
```bash
docker build -t loan-prediction-api .
docker run -p 8000:8000 -v $(pwd)/models:/app/models loan-prediction-api
```

## Documentation

- [`docs/technical_report.md`](docs/technical_report.md) — data cleaning, EDA findings, feature engineering, modeling methodology, results
- [`docs/model_card.md`](docs/model_card.md) — intended use, performance, limitations, ethical considerations
- [`docs/deployment_guide.md`](docs/deployment_guide.md) — how to deploy the API + frontend + Airflow in production
