"""Metrics: MAE, MAE+, MAE-, accuracy, precision, recall, F1, per-course breakdown."""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
)


def compute_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Compute global Mean Absolute Error."""
    return mean_absolute_error(actual.ravel(), predicted.ravel())


def compute_mae_positive(actual: np.ndarray, predicted: np.ndarray) -> float:
    """MAE+: mean error for over-predictions (predicted > actual)."""
    diff = predicted - actual
    over = diff[diff > 0]
    return float(np.mean(over)) if len(over) > 0 else 0.0


def compute_mae_negative(actual: np.ndarray, predicted: np.ndarray) -> float:
    """MAE-: mean error for under-predictions (predicted < actual)."""
    diff = actual - predicted
    under = diff[diff > 0]
    return float(np.mean(under)) if len(under) > 0 else 0.0


def compute_r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Compute R-squared score."""
    return r2_score(actual.ravel(), predicted.ravel())


def per_course_mae(
    actual: np.ndarray,
    predicted: np.ndarray,
    course_labels: Optional[Dict[int, str]] = None,
) -> pd.DataFrame:
    """Compute MAE breakdown per course. Returns DataFrame with Course, MAE, MAE+, MAE-."""
    n_courses = actual.shape[1] if actual.ndim > 1 else 1
    rows = []

    for c in range(n_courses):
        a = actual[:, c] if actual.ndim > 1 else actual
        p = predicted[:, c] if predicted.ndim > 1 else predicted

        label = course_labels.get(c, f"Course_{c}") if course_labels else f"Course_{c}"
        rows.append({
            "Course": label,
            "MAE": mean_absolute_error(a, p),
            "MAE+": compute_mae_positive(a, p),
            "MAE-": compute_mae_negative(a, p),
        })

    return pd.DataFrame(rows)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Tuple[float, float, float, float]:
    """Compute accuracy, precision, recall, and F1 for binary classification. Returns (acc, prec, rec, f1)."""
    return (
        accuracy_score(y_true, y_pred),
        precision_score(y_true, y_pred, average="binary", zero_division=0),
        recall_score(y_true, y_pred, average="binary", zero_division=0),
        f1_score(y_true, y_pred, average="binary", zero_division=0),
    )


def per_subject_classification_metrics(
    results: Dict[str, Tuple[float, float, float]],
) -> pd.DataFrame:
    """Convert per-subject (recall, precision, f1) results to DataFrame."""
    rows = [
        {"Subject": subj, "Recall": r, "Precision": p, "F1": f}
        for subj, (r, p, f) in results.items()
    ]
    return pd.DataFrame(rows)


def build_comparison_results(
    actual: np.ndarray,
    predictions: Dict[str, np.ndarray],
    terms: List[str],
    idx_to_course: Dict[int, str],
    exclude_ids: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Build a comparison DataFrame across multiple models.

    Returns DataFrame with Term, Course, Actual, Pred_{model}, Err_{model} columns.
    """
    n_courses = actual.shape[1]
    records = []

    for i, term_str in enumerate(terms):
        for c_idx in range(n_courses):
            course_id = idx_to_course.get(c_idx, f"ID_{c_idx}")
            if exclude_ids and course_id in exclude_ids:
                continue

            act = actual[i, c_idx]
            row = {"Term": term_str, "Course": course_id, "Actual": act}

            for model_name, pred in predictions.items():
                p = max(0, pred[i, c_idx])
                row[f"Pred_{model_name}"] = p
                row[f"Err_{model_name}"] = abs(act - p)

            records.append(row)

    return pd.DataFrame(records)


def summarize_comparison(df_results: pd.DataFrame, model_names: List[str]) -> Dict[str, float]:
    """Compute global MAE for each model from comparison DataFrame."""
    return {
        name: df_results[f"Err_{name}"].mean()
        for name in model_names
        if f"Err_{name}" in df_results.columns
    }
