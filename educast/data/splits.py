"""Chronological and student-level train/val/test splitting."""

from typing import List, Tuple

import numpy as np
from sklearn.model_selection import train_test_split

from educast.config import RANDOM_SEED, SPLIT_YEAR, TEST_SIZE


def split_by_year(
    X: np.ndarray,
    y: np.ndarray,
    meta: List[tuple],
    split_year: int = SPLIT_YEAR,
) -> Tuple[np.ndarray, np.ndarray, list, np.ndarray, np.ndarray, list]:
    """Split data chronologically: year < split_year to train, rest to test.

    Returns (X_train, y_train, meta_train, X_test, y_test, meta_test).
    """
    train_idx = [i for i, m in enumerate(meta) if m[0] < split_year]
    test_idx = [i for i, m in enumerate(meta) if m[0] >= split_year]

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    meta_train = [meta[i] for i in train_idx]
    meta_test = [meta[i] for i in test_idx]

    return X_train, y_train, meta_train, X_test, y_test, meta_test


def split_by_term_string(
    X: np.ndarray,
    y: np.ndarray,
    meta: List[str],
    split_year: int = SPLIT_YEAR,
) -> Tuple[np.ndarray, np.ndarray, list, np.ndarray, np.ndarray, list]:
    """Split macro data by parsing year from term string 'YYYY-TT'.

    Returns (X_train, y_train, meta_train, X_test, y_test, meta_test).
    """
    train_idx = [i for i, t in enumerate(meta) if int(t.split("-")[0]) < split_year]
    test_idx = [i for i, t in enumerate(meta) if int(t.split("-")[0]) >= split_year]

    return (
        X[train_idx], y[train_idx], [meta[i] for i in train_idx],
        X[test_idx], y[test_idx], [meta[i] for i in test_idx],
    )


def split_by_student(
    students: list,
    test_size: float = TEST_SIZE,
    seed: int = RANDOM_SEED,
) -> Tuple[list, list]:
    """Split students into train/test sets at the student level."""
    return train_test_split(students, test_size=test_size, random_state=seed)


def split_macro_last_n(
    X: np.ndarray,
    y: np.ndarray,
    meta: list,
    n_test: int = 4,
) -> Tuple[np.ndarray, np.ndarray, list, np.ndarray, np.ndarray, list]:
    """Hold out the last n_test terms as test set."""
    return (
        X[:-n_test], y[:-n_test], meta[:-n_test],
        X[-n_test:], y[-n_test:], meta[-n_test:],
    )


def tabular_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = TEST_SIZE,
    seed: int = RANDOM_SEED,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Standard sklearn train/test split for tabular data."""
    return train_test_split(X, y, test_size=test_size, random_state=seed)
