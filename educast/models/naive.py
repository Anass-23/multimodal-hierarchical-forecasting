"""Naive last-semester baseline: predict enrollment_t = enrollment_{t-k}."""

from typing import Optional

import numpy as np
import pandas as pd


class NaiveModel:
    """Naive baseline that predicts enrollment using a lagged observation.

    For semester data, the default lag is 2 (one academic year back),
    so it predicts using the same term from the previous year.
    """

    def __init__(self, lag: int = 2) -> None:
        self.lag = lag
        self.df_macro: Optional[pd.DataFrame] = None

    def fit(self, df_macro: pd.DataFrame) -> "NaiveModel":
        """Store the macro enrollment DataFrame for lookups."""
        self.df_macro = df_macro
        return self

    def predict_term(self, target_term: str) -> np.ndarray:
        """Predict enrollment for a given term using lagged data."""
        if self.df_macro is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        try:
            curr_idx = self.df_macro.index.get_loc(target_term)
            prev_idx = curr_idx - self.lag
            if prev_idx < 0:
                return np.zeros(self.df_macro.shape[1])
            return self.df_macro.iloc[prev_idx].values.astype(float)
        except KeyError:
            return np.zeros(self.df_macro.shape[1])

    def predict(self, terms: list) -> np.ndarray:
        """Predict enrollment for multiple terms. Returns (n_terms, n_courses)."""
        return np.array([self.predict_term(t) for t in terms])
