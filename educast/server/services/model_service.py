"""Service layer: model training, plugin discovery, experiment execution."""

from __future__ import annotations

import asyncio
import traceback
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from educast.config import RANDOM_SEED
from educast.experiments.registry import EXPERIMENTS, list_experiments
from educast.experiments.runner import run_experiment
from educast.server.services.app_state import ModelRun, state


def get_available_models() -> List[Dict[str, Any]]:
    """List all experiments from the registry with their config."""
    models = []
    for name in list_experiments():
        config = EXPERIMENTS[name]
        run = state.model_runs.get(name)
        models.append({
            "name": name,
            "model_type": config["model"],
            "transform": config["transform"],
            "params": config["params"],
            "status": run.status if run else "idle",
            "metrics": run.metrics if run else {},
        })
    return models


def get_model_status(name: str) -> Dict[str, Any]:
    """Get current status + results for a single model."""
    run = state.get_model_run(name)
    result: Dict[str, Any] = {
        "name": name,
        "status": run.status,
        "progress": run.progress,
        "metrics": run.metrics,
        "error": run.error,
        "metadata": run.metadata,
    }
    if run.per_course_df is not None:
        result["per_course"] = run.per_course_df.to_dict(orient="records")
    return result


async def train_model(
    name: str,
    params_override: Optional[Dict[str, Any]] = None,
    seed: int = RANDOM_SEED,
    progress_callback: Optional[Callable[[str, float, str], None]] = None,
) -> Dict[str, Any]:
    """Train a model by name (runs in a thread to not block the event loop)."""
    if name not in EXPERIMENTS:
        return {"ok": False, "error": f"Unknown experiment: {name}"}

    state.set_model_status(name, "training", progress=0.0, error=None)

    if progress_callback:
        progress_callback(name, 0.0, f"Starting {name}...")

    def _run() -> Dict[str, Any]:
        try:
            metrics, per_course_df, trainer = run_experiment(
                name, seed=seed, save_results=True
            )
            state.set_model_status(
                name,
                "done",
                progress=1.0,
                metrics=metrics,
                per_course_df=per_course_df,
                metadata={"seed": seed},
                trainer=trainer,
            )

            return {
                "ok": True,
                "name": name,
                "metrics": metrics,
                "per_course": per_course_df.to_dict(orient="records"),
            }
        except Exception as e:
            state.set_model_status(name, "error", error=str(e))
            return {"ok": False, "name": name, "error": str(e), "traceback": traceback.format_exc()}

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run)

    if progress_callback:
        progress_callback(name, 1.0, f"Finished {name}")

    return result


async def train_all_models(
    seed: int = RANDOM_SEED,
    experiment_names: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Train all (or selected) experiments sequentially."""
    names = experiment_names or list_experiments()
    results = {}
    for name in names:
        results[name] = await train_model(name, seed=seed)
    return results


def get_comparison_data() -> Optional[Dict[str, Any]]:
    """Build comparison data across all completed model runs.

    Returns dict ready for the evaluation page charts.
    """
    completed = {
        name: run for name, run in state.model_runs.items()
        if run.status == "done" and run.per_course_df is not None
    }
    if not completed:
        return None

    # Global metrics table
    metrics_table = []
    for name, run in completed.items():
        row = {"model": name, **run.metrics}
        metrics_table.append(row)

    # Per-course MAE heatmap data (courses x models)
    course_labels = [
        state.course_label_map.get(i, cid)
        for i, cid in enumerate(state.course_ids)
    ]

    per_course_mae: Dict[str, Dict[str, float]] = {}
    for name, run in completed.items():
        df = run.per_course_df
        if df is not None and "Course" in df.columns and "MAE" in df.columns:
            for _, row in df.iterrows():
                course = row["Course"]
                if course not in per_course_mae:
                    per_course_mae[course] = {}
                per_course_mae[course][name] = float(row["MAE"])

    return {
        "metrics_table": metrics_table,
        "per_course_mae": per_course_mae,
        "model_names": list(completed.keys()),
        "course_labels": course_labels,
    }


