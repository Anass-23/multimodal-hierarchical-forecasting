"""Per-course univariate ARIMA model, order selected by AIC."""

import warnings
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from educast.config import RANDOM_SEED


class PerCourseARIMA:
    """Fits an independent ARIMA model for each course's enrollment series.

    Automatically selects (p, d, q) order by minimizing AIC over a grid.
    """

    def __init__(
        self,
        max_p: int = 3,
        max_d: int = 2,
        max_q: int = 3,
        auto_order: bool = True,
        default_order: Tuple[int, int, int] = (1, 1, 1),
    ) -> None:
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.auto_order = auto_order
        self.default_order = default_order
        self.models: Dict[str, ARIMA] = {}
        self.fitted_models: Dict[str, object] = {}
        self.orders: Dict[str, Tuple[int, int, int]] = {}

    def _select_order(self, series: np.ndarray) -> Tuple[int, int, int]:
        """Select best ARIMA order by AIC grid search."""
        best_aic = np.inf
        best_order = self.default_order

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for p in range(self.max_p + 1):
                for d in range(self.max_d + 1):
                    for q in range(self.max_q + 1):
                        if p == 0 and q == 0:
                            continue
                        try:
                            model = ARIMA(series, order=(p, d, q))
                            result = model.fit()
                            if result.aic < best_aic:
                                best_aic = result.aic
                                best_order = (p, d, q)
                        except Exception:
                            continue

        return best_order

    def fit(self, df_macro: pd.DataFrame) -> "PerCourseARIMA":
        """Fit one ARIMA model per course."""
        for col in df_macro.columns:
            series = df_macro[col].values.astype(float)

            if self.auto_order:
                order = self._select_order(series)
            else:
                order = self.default_order

            self.orders[col] = order
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = ARIMA(series, order=order)
                    self.fitted_models[col] = model.fit()
            except Exception:
                self.fitted_models[col] = None

        return self

    def predict(self, steps: int = 1) -> np.ndarray:
        """Forecast the next `steps` terms for all courses. Returns (steps, n_courses)."""
        n_courses = len(self.fitted_models)
        predictions = np.zeros((steps, n_courses))

        for i, (col, model) in enumerate(self.fitted_models.items()):
            if model is not None:
                try:
                    forecast = model.forecast(steps=steps)
                    predictions[:, i] = np.maximum(0, forecast)
                except Exception:
                    pass

        return predictions
