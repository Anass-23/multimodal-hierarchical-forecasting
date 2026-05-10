"""Global application state: loaded data, trained models, cached results."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class ModelRun:
    """Result of a single model training + evaluation run."""

    name: str
    status: str = "idle"  # idle | training | done | error
    progress: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    per_course_df: Optional[pd.DataFrame] = None
    predictions: Optional[np.ndarray] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    trainer: Any = None  # cached fitted model (e.g. MicroLSTMTrainer)


class AppState:
    """Shared server-side state. Thread-safe for concurrent API requests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        self.data_loaded: bool = False
        self.manifest: Dict[str, Any] = {}
        self.data_dir: Optional[Path] = None
        self.university_data: Optional[dict] = None

        self.course_ids: List[str] = []
        self.course_to_idx: Dict[str, int] = {}
        self.idx_to_course: Dict[int, str] = {}
        self.course_label_map: Dict[int, str] = {}

        self.id_to_acronym: Dict[int, str] = {}
        self.acronym_to_id: Dict[str, int] = {}
        self.subject_names: Dict[str, str] = {}  # acronym -> full name

        self.df_macro: Optional[pd.DataFrame] = None
        self.tabular_datasets: Dict[str, pd.DataFrame] = {}

        self.X_all: Optional[np.ndarray] = None
        self.y_all: Optional[np.ndarray] = None
        self.meta_all: Optional[list] = None

        self.model_runs: Dict[str, ModelRun] = {}

    def get_student_ids(self) -> List[str]:
        if self.university_data is None:
            return []
        students = self.university_data.get("students", [])
        if isinstance(students, list):
            return sorted(s.get("student_id", "") for s in students)
        return sorted(students.keys())

    def get_student(self, student_id: str) -> Optional[dict]:
        if self.university_data is None:
            return None
        students = self.university_data.get("students", [])
        if isinstance(students, list):
            for s in students:
                if s.get("student_id") == student_id:
                    return s
            return None
        return students.get(student_id)

    def get_terms(self) -> List[str]:
        if self.df_macro is None:
            return []
        return list(self.df_macro.index)

    def get_model_run(self, name: str) -> ModelRun:
        with self._lock:
            if name not in self.model_runs:
                self.model_runs[name] = ModelRun(name=name)
            return self.model_runs[name]

    def set_model_status(self, name: str, status: str, **kwargs: Any) -> None:
        with self._lock:
            run = self.model_runs.setdefault(name, ModelRun(name=name))
            run.status = status
            for k, v in kwargs.items():
                setattr(run, k, v)

    def summary(self) -> Dict[str, Any]:
        return {
            "data_loaded": self.data_loaded,
            "n_students": len(self.get_student_ids()),
            "n_courses": len(self.course_ids),
            "n_terms": len(self.get_terms()),
            "terms": self.get_terms(),
            "models_run": {
                name: {"status": run.status, "metrics": run.metrics}
                for name, run in self.model_runs.items()
            },
        }


state = AppState()
