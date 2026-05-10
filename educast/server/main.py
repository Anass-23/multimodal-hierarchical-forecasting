"""FastAPI application entry point.

Run with:
    python -m educast.server
    # or
    uvicorn educast.server.main:app --port 8765
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from educast.server.routers import data, evaluation, forecast, models, students


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    yield


app = FastAPI(
    title="educast API",
    description="Backend for the educast desktop app: student enrollment prediction",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow Electron renderer (localhost with any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data.router)
app.include_router(students.router)
app.include_router(models.router)
app.include_router(evaluation.router)
app.include_router(forecast.router)


@app.get("/")
async def root() -> dict:
    """Health check."""
    return {"status": "ok", "app": "educast", "version": "0.1.0"}
