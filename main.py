"""
main.py
=======
Main entry point to run the complete ML pipeline end-to-end:

    raw data -> preprocess -> feature engineering -> train -> evaluate

Usage:
    python main.py                 # run every stage
    python main.py --stage train   # run a single stage (preprocess|features|train|evaluate)
"""

from __future__ import annotations

import argparse
import time

import config
from src import preprocess, feature_engineering, train, evaluate
from src.utils import get_logger

logger = get_logger(__name__, config.LOGS_DIR / "main.log")

STAGES = ["preprocess", "features", "train", "evaluate"]


def run_preprocess():
    logger.info(">>> STAGE 1/4: preprocess")
    preprocess.run()


def run_features():
    logger.info(">>> STAGE 2/4: feature_engineering")
    feature_engineering.run()


def run_train():
    logger.info(">>> STAGE 3/4: train")
    best_model = train.run()
    logger.info(f"Best model selected: {best_model}")


def run_evaluate():
    logger.info(">>> STAGE 4/4: evaluate")
    evaluate.run()


STAGE_FUNCS = {
    "preprocess": run_preprocess,
    "features": run_features,
    "train": run_train,
    "evaluate": run_evaluate,
}


def run_pipeline(stage: str | None = None):
    start = time.time()
    stages_to_run = [stage] if stage else STAGES

    for s in stages_to_run:
        STAGE_FUNCS[s]()

    elapsed = time.time() - start
    logger.info(f"Pipeline finished in {elapsed:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the loan default prediction ML pipeline")
    parser.add_argument("--stage", choices=STAGES, default=None, help="Run only a single stage")
    args = parser.parse_args()

    run_pipeline(args.stage)
