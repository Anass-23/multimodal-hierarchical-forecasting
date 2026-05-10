"""Random forest per subject with auto n_estimators optimization."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline

from educast.config import (
    FOREST_MAX_DEPTH,
    FOREST_MAX_FEATURES,
    FOREST_N_ESTIMATORS,
    RANDOM_SEED,
)
from educast.features.tabular import build_preprocessor


@dataclass
class SubjectForestPipeline:
    """Training pipeline for a single subject's random forest classifier."""

    subject_id: str
    y_train: np.ndarray
    y_test: np.ndarray
    numerical_features: List[str]
    categorical_features: List[str]
    n_estimators: int = FOREST_N_ESTIMATORS
    max_depth: int = FOREST_MAX_DEPTH
    max_features: str = FOREST_MAX_FEATURES
    auto_estimators: bool = False
    random_state: int = RANDOM_SEED
    pipeline: Optional[Pipeline] = field(default=None, init=False)
    is_fitted: bool = field(default=False, init=False)
    best_n_estimators: Optional[int] = field(default=None, init=False)

    def __post_init__(self) -> None:
        # Coerce labels to int32 regardless of upstream dtype (object, bool, float).
        # sklearn's type_of_target returns "unknown" for object arrays; this prevents that.
        self.y_train = np.asarray(self.y_train, dtype=np.int32)
        self.y_test = np.asarray(self.y_test, dtype=np.int32)

        preprocessor = build_preprocessor(
            self.categorical_features, self.numerical_features
        )
        clf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            max_features=self.max_features,
            oob_score=True,
            bootstrap=True,
            random_state=self.random_state,
        )
        self.pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("clf", clf),
        ])

    def _optimize_n_estimators(
        self, X_train: np.ndarray, min_n: int = 5, max_n: int = 100, step: int = 5,
    ) -> int:
        """Find optimal n_estimators by minimizing OOB error."""
        preprocessor = self.pipeline.named_steps["preprocessor"]
        X_transformed = preprocessor.fit_transform(X_train)

        best_n = self.n_estimators
        best_oob = 0.0

        for n in range(min_n, max_n + 1, step):
            rf = RandomForestClassifier(
                n_estimators=n,
                max_depth=self.max_depth,
                max_features=self.max_features,
                oob_score=True,
                bootstrap=True,
                random_state=self.random_state,
            )
            rf.fit(X_transformed, self.y_train)
            if rf.oob_score_ > best_oob:
                best_oob = rf.oob_score_
                best_n = n

        return best_n

    def fit(self, X_train: np.ndarray) -> "SubjectForestPipeline":
        """Train the pipeline, optionally auto-optimizing n_estimators."""
        if self.auto_estimators:
            self.best_n_estimators = self._optimize_n_estimators(X_train)
            clf = self.pipeline.named_steps["clf"]
            clf.set_params(n_estimators=self.best_n_estimators)

        self.pipeline.fit(X_train, self.y_train)
        self.is_fitted = True
        return self

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """Predict enrollment for this subject."""
        return self.pipeline.predict(X_test)

    def score(self, X_test: np.ndarray) -> Tuple[float, float, float]:
        """Compute recall, precision, and F1. Returns (recall, precision, f1)."""
        y_pred = self.predict(X_test)
        return (
            recall_score(self.y_test, y_pred, average="binary", zero_division=0),
            precision_score(self.y_test, y_pred, average="binary", zero_division=0),
            f1_score(self.y_test, y_pred, average="binary", zero_division=0),
        )

    def get_feature_importances(self) -> np.ndarray:
        """Get feature importances from the fitted forest."""
        return self.pipeline.named_steps["clf"].feature_importances_

    def get_feature_names(self) -> List[str]:
        """Get feature names after preprocessing."""
        preprocessor = self.pipeline.named_steps["preprocessor"]
        names = []
        if self.categorical_features:
            cat_enc = preprocessor.named_transformers_["cat"]
            names.extend(
                cat_enc.get_feature_names_out(self.categorical_features).tolist()
            )
        names.extend(self.numerical_features)
        return names


class RandomForestManager:
    """Manages multiple per-subject random forest pipelines."""

    def __init__(self) -> None:
        self.models: Dict[str, SubjectForestPipeline] = {}
        self.fitted_subjects: List[str] = []

    def add_model(self, subject_id: str, model: SubjectForestPipeline) -> None:
        """Register a subject-specific pipeline."""
        self.models[subject_id] = model

    def __getitem__(self, subject_id: str) -> SubjectForestPipeline:
        return self.models[subject_id]

    def __iter__(self):
        return iter(self.models.values())

    def fit(self, subject_list: List[str], X_train: np.ndarray) -> "RandomForestManager":
        """Train all registered subject models."""
        for subj in subject_list:
            if subj in self.models:
                self.models[subj].fit(X_train)
                self.fitted_subjects.append(subj)
        return self

    def evaluate(self, X_test: np.ndarray) -> Dict[str, Tuple[float, float, float]]:
        """Evaluate all fitted models.

        Subjects with no positive labels in the test set are skipped, as their
        metrics would be meaningless (zero_division=0 would silently return 0).
        """
        results = {}
        skipped = []
        for subj in self.fitted_subjects:
            pipeline = self.models[subj]
            if pipeline.y_test.sum() == 0:
                skipped.append(subj)
                continue
            results[subj] = pipeline.score(X_test)
        if skipped:
            print(f"  Skipped {len(skipped)} subjects with no positive test labels: {skipped}")
        return results
