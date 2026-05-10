"""Forecast endpoints: model results and per-course predictions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from educast.server.services.app_state import state
from educast.server.services.eval_service import get_forecast_data

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/results")
async def forecast_results() -> dict:
    """Get per-course results from all trained models."""
    if not state.data_loaded:
        raise HTTPException(400, "Load data first")

    data = get_forecast_data()
    if not data["models"]:
        raise HTTPException(404, "No models trained yet")

    return data


@router.get("/terms")
async def available_terms() -> dict:
    """List available terms."""
    return {
        "terms": state.get_terms(),
        "n_terms": len(state.get_terms()),
    }


@router.get("/enrollment-history")
async def enrollment_history() -> dict:
    """Return the full enrollment history matrix (courses x terms) for heatmap display.

    Returns the actual enrollment counts and course labels/term labels.
    """
    if not state.data_loaded or state.df_macro is None:
        raise HTTPException(400, "Load data first")

    df = state.df_macro
    # Transpose: df is (terms x courses), frontend needs (courses x terms)
    return {
        "terms": df.index.tolist(),
        "course_ids": df.columns.tolist(),
        "values": df.values.T.astype(int).tolist(),
        "course_labels": {
            cid: state.course_label_map.get(i, cid)
            for i, cid in enumerate(state.course_ids)
            if cid in df.columns
        },
    }
