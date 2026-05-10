"""Data loading and status endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from educast.server.services.app_state import state
from educast.server.services.data_service import (
    get_courses_summary,
    load_data_from_manifest,
    load_data_legacy,
)

router = APIRouter(prefix="/data", tags=["data"])


class LoadRequest(BaseModel):
    path: Optional[str] = None  # If None, use built-in EPSEM data
    mode: str = "legacy"  # "legacy" | "manifest"


class LoadResponse(BaseModel):
    ok: bool
    errors: list[str] = []
    n_students: int = 0
    n_courses: int = 0
    n_terms: int = 0
    terms: list[str] = []


@router.post("/load", response_model=LoadResponse)
async def load_data(req: LoadRequest) -> LoadResponse:
    """Load university data (manifest-based or legacy EPSEM paths)."""
    if req.mode == "manifest" and req.path:
        result = load_data_from_manifest(Path(req.path))
    else:
        result = load_data_legacy()

    if not result["ok"]:
        return LoadResponse(ok=False, errors=result["errors"])

    return LoadResponse(
        ok=True,
        n_students=result.get("n_students", len(state.get_student_ids())),
        n_courses=result.get("n_courses", len(state.course_ids)),
        n_terms=result.get("n_terms", len(state.get_terms())),
        terms=result.get("terms", state.get_terms()),
    )


@router.get("/status")
async def data_status() -> dict:
    """Get current data loading status + summary stats."""
    return state.summary()


@router.get("/courses")
async def courses() -> list:
    """Get all courses with enrollment trends."""
    if not state.data_loaded:
        raise HTTPException(404, "No data loaded")
    return get_courses_summary()
