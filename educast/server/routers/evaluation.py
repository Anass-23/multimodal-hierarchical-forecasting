"""Evaluation and comparison endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from educast.server.services.eval_service import (
    get_all_metrics,
    get_heatmap_data,
    get_per_course_results,
)
from educast.server.services.model_service import get_comparison_data

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/metrics")
async def all_metrics() -> list:
    """Global metrics for all completed models."""
    return get_all_metrics()


@router.get("/metrics/{model_name}")
async def model_metrics(model_name: str) -> dict:
    """Per-course results for a specific model."""
    results = get_per_course_results(model_name)
    if results is None:
        raise HTTPException(404, f"No results for model: {model_name}")
    return {"model": model_name, "per_course": results}


@router.get("/heatmap")
async def heatmap() -> dict:
    """Per-course MAE heatmap data (courses x models)."""
    return get_heatmap_data()


@router.get("/compare")
async def compare() -> dict:
    """Full comparison data across all completed models."""
    data = get_comparison_data()
    if data is None:
        raise HTTPException(404, "No models have been trained yet")
    return data
