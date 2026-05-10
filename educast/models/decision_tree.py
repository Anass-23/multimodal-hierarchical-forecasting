"""Decision tree classifier: one tree per subject, configurable depth + pruning."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from educast.config import RANDOM_SEED, TREE_MAX_DEPTH
from educast.features.tabular import build_preprocessor


@dataclass
class SubjectTreePipeline:
    """Training pipeline for a single subject's decision tree classifier."""

    subject_id: str
    y_train: np.ndarray
    y_test: np.ndarray
    numerical_features: List[str]
    categorical_features: List[str]
    max_depth: int = TREE_MAX_DEPTH
    ccp_alpha: float = 0.0
    random_state: int = RANDOM_SEED
    pipeline: Optional[Pipeline] = field(default=None, init=False)
    is_fitted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        # Coerce labels to int32 regardless of upstream dtype (object, bool, float).
        # sklearn's type_of_target returns "unknown" for object arrays; this prevents that.
        self.y_train = np.asarray(self.y_train, dtype=np.int32)
        self.y_test = np.asarray(self.y_test, dtype=np.int32)

        preprocessor = build_preprocessor(
            self.categorical_features, self.numerical_features
        )
        clf = DecisionTreeClassifier(
            max_depth=self.max_depth,
            ccp_alpha=self.ccp_alpha,
            random_state=self.random_state,
        )
        self.pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("clf", clf),
        ])

    def fit(self, X_train: np.ndarray) -> "SubjectTreePipeline":
        """Train the pipeline on the full feature set with this subject's labels."""
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


class DecisionTreeManager:
    """Manages multiple per-subject decision tree pipelines."""

    def __init__(self) -> None:
        self.models: Dict[str, SubjectTreePipeline] = {}
        self.fitted_subjects: List[str] = []

    def add_model(self, subject_id: str, model: SubjectTreePipeline) -> None:
        """Register a subject-specific pipeline."""
        self.models[subject_id] = model

    def __getitem__(self, subject_id: str) -> SubjectTreePipeline:
        return self.models[subject_id]

    def __iter__(self):
        return iter(self.models.values())

    def fit(self, subject_list: List[str], X_train: np.ndarray) -> "DecisionTreeManager":
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
