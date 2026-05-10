"""Model management and training endpoints."""

from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sklearn.tree import export_text

from educast.config import RANDOM_SEED
from educast.server.services.app_state import state
from educast.server.services.model_service import (
    get_available_models,
    get_model_status,
    train_all_models,
    train_model,
)

router = APIRouter(prefix="/models", tags=["models"])


class TrainRequest(BaseModel):
    seed: int = RANDOM_SEED
    params_override: Optional[dict] = None


class TrainAllRequest(BaseModel):
    seed: int = RANDOM_SEED
    experiments: Optional[list[str]] = None


@router.get("/")
async def list_models() -> list:
    """List all available experiments with their status."""
    return get_available_models()


@router.get("/{name}/status")
async def model_status(name: str) -> dict:
    """Get training status and results for a model."""
    return get_model_status(name)


@router.post("/{name}/train")
async def train(name: str, req: TrainRequest) -> dict:
    """Train a single model (blocking, returns when done)."""
    if not state.data_loaded:
        raise HTTPException(400, "Load data first")

    result = await train_model(
        name,
        params_override=req.params_override,
        seed=req.seed,
    )
    return result


@router.post("/train-all")
async def train_all(req: TrainAllRequest) -> dict:
    """Train all (or selected) models sequentially."""
    if not state.data_loaded:
        raise HTTPException(400, "Load data first")

    results = await train_all_models(
        seed=req.seed,
        experiment_names=req.experiments,
    )
    return {"ok": True, "results": results}


@router.websocket("/{name}/train-ws")
async def train_ws(websocket: WebSocket, name: str) -> None:
    """WebSocket endpoint for training with real-time progress.

    Sends JSON messages: {"progress": 0.5, "message": "Epoch 50/100"}
    """
    await websocket.accept()

    async def send_progress(model_name: str, progress: float, message: str) -> None:
        try:
            await websocket.send_json({
                "model": model_name,
                "progress": progress,
                "message": message,
            })
        except Exception:
            pass

    try:
        result = await train_model(name, progress_callback=send_progress)
        await websocket.send_json({"done": True, **result})
    except WebSocketDisconnect:
        state.set_model_status(name, "error", error="Client disconnected")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/{name}/history")
async def get_training_history(name: str):
    """Return training loss curves for LSTM models."""
    run = state.model_runs.get(name)
    if not run or run.status != "done":
        return {"train_loss": [], "val_loss": []}
    trainer = run.trainer
    if trainer and hasattr(trainer, "history"):
        return {
            "train_loss": [float(v) for v in trainer.history.get("train_loss", [])],
            "val_loss": [float(v) for v in trainer.history.get("val_loss", [])],
        }
    return {"train_loss": [], "val_loss": []}


@router.get("/{name}/subjects")
async def get_model_subjects(name: str):
    """List subjects available in a tree-based model."""
    run = state.model_runs.get(name)
    if not run or run.status != "done" or not run.trainer:
        return {"subjects": []}
    manager = run.trainer
    if hasattr(manager, "models"):
        return {"subjects": sorted(manager.models.keys())}
    return {"subjects": []}


@router.get("/{name}/tree/{subject}")
async def get_tree_structure(name: str, subject: str):
    """Return decision tree text representation for a subject."""
    run = state.model_runs.get(name)
    if not run or run.status != "done" or not run.trainer:
        raise HTTPException(404, f"Model {name} not trained")

    manager = run.trainer
    if not hasattr(manager, "models") or subject not in manager.models:
        raise HTTPException(404, f"Subject {subject} not found in {name}")

    pipeline = manager.models[subject]
    # The fitted DecisionTreeClassifier lives inside the sklearn Pipeline
    tree_model = pipeline.pipeline.named_steps["clf"]
    if tree_model is None or not pipeline.is_fitted:
        raise HTTPException(404, f"No fitted tree for {subject}")

    # Get feature names from the pipeline's preprocessor
    feature_names: list[str] | None = None
    try:
        feature_names = pipeline.get_feature_names()
    except Exception:
        pass

    tree_text = export_text(
        tree_model, feature_names=feature_names, max_depth=10
    )

    return {
        "subject": subject,
        "tree_text": tree_text,
        "max_depth": tree_model.get_depth(),
        "n_nodes": tree_model.tree_.node_count,
        "n_leaves": tree_model.get_n_leaves(),
        "feature_names": feature_names,
    }


@router.post("/{name}/summarize/{subject}")
async def summarize_tree(name: str, subject: str):
    """Use local Ollama to summarize a decision tree's rules for a subject."""
    run = state.model_runs.get(name)
    if not run or run.status != "done" or not run.trainer:
        raise HTTPException(404, f"Model {name} not trained")

    manager = run.trainer
    if not hasattr(manager, "models") or subject not in manager.models:
        raise HTTPException(404, f"Subject {subject} not found")

    pipeline = manager.models[subject]
    tree_model = pipeline.pipeline.named_steps["clf"]
    if tree_model is None or not pipeline.is_fitted:
        raise HTTPException(404, f"No fitted tree for {subject}")

    feature_names: list[str] | None = None
    try:
        feature_names = pipeline.get_feature_names()
    except Exception:
        pass

    tree_text = export_text(
        tree_model, feature_names=feature_names, max_depth=10
    )

    # Get metrics for context
    metrics = run.per_course_df
    subject_metrics = ""
    if metrics is not None:
        col_name = "Course" if "Course" in metrics.columns else "Subject"
        row = metrics[metrics[col_name] == subject]
        if not row.empty:
            r = row.iloc[0]
            parts = []
            for col in ("Recall", "Precision", "F1"):
                val = r.get(col)
                if val is not None:
                    parts.append(f"{col}={val:.3f}")
            subject_metrics = ", ".join(parts) if parts else ""

    prompt = (
        f'You are an academic advisor analyzing a decision tree model that predicts '
        f'whether a student will enroll in the course "{subject}" next semester at a '
        f'university engineering program.\n\n'
        f'Here are the tree\'s decision rules:\n{tree_text}\n\n'
        f'Model performance: {subject_metrics}\n\n'
        f'Please provide a concise summary (3-5 bullet points) that explains:\n'
        f'1. What are the most important factors (courses/features) that predict '
        f'enrollment in {subject}?\n'
        f'2. What pattern of prior courses suggests a student WILL enroll?\n'
        f'3. What pattern suggests they WON\'T enroll?\n'
        f'4. Any interesting or unexpected rules the tree learned?\n\n'
        f'Keep it practical and useful for academic advisors. Use plain language.'
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": "llama3.2", "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "subject": subject,
                    "summary": result.get("response", ""),
                    "model_used": "llama3.2",
                    "tree_text": tree_text,
                    "metrics": subject_metrics,
                }
            else:
                raise HTTPException(502, f"Ollama returned {resp.status_code}")
    except httpx.ConnectError:
        raise HTTPException(503, "Ollama not running. Start it with: ollama serve")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
