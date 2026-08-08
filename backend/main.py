"""
backend/main.py
================
FastAPI application exposing the loan default prediction model.

Run:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Docs available at /docs (Swagger) and /redoc.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
from src.predict import LoanDefaultPredictor
from src.utils import get_logger, load_json
from backend.schema import (
    LoanApplication,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
)

logger = get_logger(__name__, config.LOGS_DIR / "backend.log")

app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=(
        "Predicts the probability that a loan will default (be Charged Off) "
        "based on borrower and loan characteristics known at application time."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor: LoanDefaultPredictor | None = None
BEST_MODEL_NAME = "unknown"


@app.on_event("startup")
def load_model() -> None:
    global predictor, BEST_MODEL_NAME
    try:
        predictor = LoanDefaultPredictor()
        if config.METRICS_PATH.exists():
            BEST_MODEL_NAME = load_json(config.METRICS_PATH).get("best_model", "unknown")
        logger.info("Model loaded successfully on startup")
    except FileNotFoundError as e:
        logger.error(f"Model artifacts not found: {e}. Run `python main.py` to train first.")
        predictor = None


def _get_predictor() -> LoanDefaultPredictor:
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Train the pipeline first (`python main.py`).",
        )
    return predictor


@app.get("/", tags=["Root"])
def root():
    return {"message": config.API_TITLE, "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    return HealthResponse(
        status="ok" if predictor is not None else "model_not_loaded",
        model_loaded=predictor is not None,
        model_path=str(config.BEST_MODEL_PATH),
    )


@app.get("/model-info", response_model=ModelInfoResponse, tags=["Model Info"])
def model_info():
    if not config.METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="metrics.json not found. Run evaluation first.")
    metrics = load_json(config.METRICS_PATH)
    return ModelInfoResponse(
        best_model=metrics.get("best_model", "unknown"),
        metrics=metrics.get("models", {}),
        feature_count=len(config.FEATURES),
        numeric_features=config.NUMERIC_FEATURES,
        categorical_features=config.CATEGORICAL_FEATURES,
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(application: LoanApplication):
    p = _get_predictor()
    try:
        result = p.predict(application.model_dump())
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")
    return PredictionResponse(**result, model_used=BEST_MODEL_NAME)


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
def predict_batch(request: BatchPredictionRequest):
    p = _get_predictor()
    try:
        results = [
            PredictionResponse(**p.predict(app_.model_dump()), model_used=BEST_MODEL_NAME)
            for app_ in request.applications
        ]
    except Exception as e:
        logger.exception("Batch prediction failed")
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {e}")
    return BatchPredictionResponse(results=results)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
