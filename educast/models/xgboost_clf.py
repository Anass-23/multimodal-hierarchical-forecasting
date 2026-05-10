"""XGBoost classifier: one model per subject, L1/L2 regularisation, class-imbalance handling."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from educast.config import RANDOM_SEED, TREE_MAX_DEPTH
from educast.features.tabular import build_preprocessor


@dataclass
class SubjectXGBPipeline:
    subject_id: str
    y_train: np.ndarray
    y_test: np.ndarray
    numerical_features: List[str]
    categorical_features: List[str]
    max_depth: int = TREE_MAX_DEPTH
    n_estimators: int = 200
    learning_rate: float = 0.1
    random_state: int = RANDOM_SEED
    pipeline: Optional[Pipeline] = field(default=None, init=False)
    is_fitted: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.y_train = np.asarray(self.y_train, dtype=np.int32)
        self.y_test = np.asarray(self.y_test, dtype=np.int32)

        preprocessor = build_preprocessor(
            self.categorical_features, self.numerical_features
        )
        pos = max(int(self.y_train.sum()), 1)
        neg = max(len(self.y_train) - pos, 1)
        clf = XGBClassifier(
            max_depth=self.max_depth,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            scale_pos_weight=neg / pos,
            reg_alpha=1.0,
            reg_lambda=1.0,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=self.random_state,
            verbosity=0,
        )
        self.pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("clf", clf),
        ])

    def fit(self, X_train: np.ndarray) -> "SubjectXGBPipeline":
        self.pipeline.fit(X_train, self.y_train)
        self.is_fitted = True
        return self

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        return self.pipeline.predict(X_test)

    def score(self, X_test: np.ndarray) -> Tuple[float, float, float]:
        y_pred = self.predict(X_test)
        return (
            recall_score(self.y_test, y_pred, average="binary", zero_division=0),
            precision_score(self.y_test, y_pred, average="binary", zero_division=0),
            f1_score(self.y_test, y_pred, average="binary", zero_division=0),
        )


class XGBoostManager:
    def __init__(self) -> None:
        self.models: Dict[str, SubjectXGBPipeline] = {}
        self.fitted_subjects: List[str] = []

    def add_model(self, subject_id: str, model: SubjectXGBPipeline) -> None:
        self.models[subject_id] = model

    def __getitem__(self, subject_id: str) -> SubjectXGBPipeline:
        return self.models[subject_id]

    def fit(self, subject_list: List[str], X_train: np.ndarray) -> "XGBoostManager":
        for subj in subject_list:
            if subj in self.models:
                self.models[subj].fit(X_train)
                self.fitted_subjects.append(subj)
        return self

    def evaluate(self, X_test: np.ndarray) -> Dict[str, Tuple[float, float, float]]:
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
