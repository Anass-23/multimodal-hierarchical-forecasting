"""Differencing LSTM: first-order differencing on enrollment series before Macro LSTM."""

from typing import Optional

import numpy as np

from educast.models.lstm_macro import MacroLSTMTrainer


class DifferencingLSTMTrainer:
    """Applies first-order differencing before training a Macro LSTM.

    The enrollment series is differenced (delta_t = x_t - x_{t-1}),
    the LSTM is trained on the differences, and predictions are
    inverted by adding the last known value.
    """

    def __init__(self, **kwargs) -> None:
        self.macro_trainer = MacroLSTMTrainer(**kwargs)
        self.last_values: Optional[np.ndarray] = None

    @staticmethod
    def difference(data: np.ndarray) -> np.ndarray:
        """Compute first-order differences along the time axis."""
        return np.diff(data, axis=0)

    @staticmethod
    def inverse_difference(
        predictions: np.ndarray, last_values: np.ndarray,
    ) -> np.ndarray:
        """Invert differencing by cumulative sum from last known values."""
        result = np.zeros_like(predictions)
        current = last_values.copy()
        for i in range(len(predictions)):
            current = current + predictions[i]
            result[i] = current
        return result

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.1,
    ) -> dict:
        """Train on differenced data. Returns training history dict."""
        return self.macro_trainer.fit(X_train, y_train, validation_split)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict differences."""
        return self.macro_trainer.predict(X)

    def predict_real(
        self, X: np.ndarray, last_values: np.ndarray,
    ) -> np.ndarray:
        """Predict differences and invert to real-scale counts."""
        diff_pred = self.predict(X)
        return np.maximum(0, self.inverse_difference(diff_pred, last_values))
