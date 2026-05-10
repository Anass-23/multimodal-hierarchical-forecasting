"""Export experiment results to CSV + JSON with full metadata."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from educast.config import RESULTS_DIR


def export_results(
    experiment_name: str,
    metrics: Dict[str, float],
    per_course_df: pd.DataFrame,
    metadata: Optional[Dict[str, Any]] = None,
    output_dir: Path = RESULTS_DIR,
    timestamp: Optional[str] = None,
) -> tuple:
    """Save experiment results as JSON + CSV. Returns (json_path, csv_path)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    result = {
        "experiment_name": experiment_name,
        "timestamp": ts,
        "metrics": metrics,
        "metadata": metadata or {},
    }

    json_path = output_dir / f"{experiment_name}_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    csv_path = output_dir / f"{experiment_name}_{ts}_per_course.csv"
    per_course_df.to_csv(csv_path, index=False)

    return json_path, csv_path


def build_experiment_metadata(
    model_name: str,
    transform_name: str,
    hyperparams: Dict[str, Any],
    seed: int,
    train_samples: int = 0,
    test_samples: int = 0,
    split_info: str = "",
) -> Dict[str, Any]:
    """Build standardized metadata dict for an experiment."""
    return {
        "model": model_name,
        "transform": transform_name,
        "hyperparameters": hyperparams,
        "random_seed": seed,
        "train_samples": train_samples,
        "test_samples": test_samples,
        "split_info": split_info,
    }
