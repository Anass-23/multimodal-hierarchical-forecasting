"""Data cleaning: missing value handling and course activity filtering."""

import numpy as np
import pandas as pd


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fill NaN values in enrollment DataFrames using standard conventions.

    - .m (enrolled) columns: False
    - .n (grade) columns: 0.0
    - becat (scholarship) columns: False
    - VIA, ORDRE, NACC: 0
    """
    df = df.copy()
    m_cols = [c for c in df.columns if c.endswith(".m")]
    n_cols = [c for c in df.columns if c.endswith(".n")]
    becat_cols = [c for c in df.columns if c.endswith("becat") or c == "BECAT"]

    if m_cols:
        df[m_cols] = df[m_cols].fillna(False)
    if n_cols:
        df[n_cols] = df[n_cols].fillna(0.0)
    if becat_cols:
        df[becat_cols] = df[becat_cols].fillna(False)

    for col in ["VIA", "ORDRE", "NACC"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df


def filter_inactive_courses(
    enrollment_matrix: np.ndarray,
    target: np.ndarray,
    threshold: int = 0,
) -> np.ndarray:
    """Return boolean mask of courses with activity above threshold."""
    activity = np.sum(enrollment_matrix, axis=0) + target
    return activity > threshold
