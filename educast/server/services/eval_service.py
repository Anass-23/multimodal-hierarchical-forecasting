"""Service layer: evaluation metrics, comparison builders."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from educast.server.services.app_state import state


def get_per_course_results(model_name: str) -> Optional[List[Dict[str, Any]]]:
    """Get per-course results for a single model."""
    run = state.model_runs.get(model_name)
    if run is None or run.per_course_df is None:
        return None
    return run.per_course_df.to_dict(orient="records")


def get_all_metrics() -> List[Dict[str, Any]]:
    """Get global metrics for all completed models."""
    results = []
    for name, run in state.model_runs.items():
        if run.status == "done":
            results.append({
                "model": name,
                "status": run.status,
                **run.metrics,
            })
    return results


def get_heatmap_data() -> Dict[str, Any]:
    """Build per-course MAE heatmap: courses (rows) x models (cols).

    Returns JSON-serializable dict with:
      - courses: list of course acronyms
      - models: list of model names
      - values: 2D list (n_courses x n_models) of MAE values (null if missing)
    """
    completed = {
        name: run for name, run in state.model_runs.items()
        if run.status == "done" and run.per_course_df is not None
    }
    if not completed:
        return {"courses": [], "models": [], "values": []}

    model_names = sorted(completed.keys())

    # Collect all courses across all model results
    all_courses: List[str] = []
    course_mae: Dict[str, Dict[str, Optional[float]]] = {}

    for mname, run in completed.items():
        df = run.per_course_df
        if df is None:
            continue
        # Unified format: all DataFrames have "Course" column
        course_col = "Course" if "Course" in df.columns else "Subject"
        # Prefer MAE for heatmap; fall back to F1 if MAE is all NaN
        mae_col = "MAE"
        if mae_col not in df.columns or df[mae_col].dropna().empty:
            mae_col = "F1" if "F1" in df.columns else df.columns[1]

        for _, row in df.iterrows():
            course = str(row.get(course_col, ""))
            if course not in course_mae:
                course_mae[course] = {}
                all_courses.append(course)
            val = row.get(mae_col)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                course_mae[course][mname] = float(val)

    # Build 2D matrix
    values = []
    for course in all_courses:
        row = []
        for mname in model_names:
            row.append(course_mae.get(course, {}).get(mname))
        values.append(row)

    return {
        "courses": all_courses,
        "models": model_names,
        "values": values,
    }


def get_forecast_data() -> Dict[str, Any]:
    """Get per-course predictions from all trained models.

    For time-series models: uses per_course_df with MAE data.
    For tree models: uses per_course_df with classification metrics.

    Returns dict of {courses, models, model_data: {model: {metric_name: [...]}}}
    """
    completed = {
        name: run for name, run in state.model_runs.items()
        if run.status == "done" and run.per_course_df is not None
    }
    if not completed:
        return {"courses": [], "models": [], "model_data": {}}

    model_data: Dict[str, Dict[str, List]] = {}
    all_courses_set: List[str] = []

    for mname, run in completed.items():
        df = run.per_course_df
        if df is None:
            continue

        course_col = "Course" if "Course" in df.columns else "Subject"
        courses_in_model = df[course_col].tolist()

        if not all_courses_set:
            all_courses_set = courses_in_model

        entry: Dict[str, List] = {"courses": courses_in_model}
        for col in df.columns:
            if col != course_col:
                vals = df[col].tolist()
                entry[col] = [
                    float(v) if v is not None and not (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else None
                    for v in vals
                ]
        model_data[mname] = entry

    return {
        "courses": all_courses_set,
        "models": list(completed.keys()),
        "model_data": model_data,
    }
