"""Tests for model instantiation and basic forward passes."""

import numpy as np
import pytest

from educast.config import FEAT_DIM_STUDENT, NUM_COURSES
from educast.models.naive import NaiveModel


class TestNaiveModel:
    def _make_macro_df(self):
        import pandas as pd
        terms = ["2017-01", "2017-02", "2018-01", "2018-02", "2019-01", "2019-02"]
        data = np.random.randint(0, 50, (len(terms), 5))
        return pd.DataFrame(data, index=terms, columns=[f"C{i}" for i in range(5)])

    def test_fit_and_predict(self):
        df = self._make_macro_df()
        model = NaiveModel(lag=2)
        model.fit(df)
        pred = model.predict_term("2019-01")
        assert pred.shape == (5,)

    def test_predict_multiple(self):
        df = self._make_macro_df()
        model = NaiveModel(lag=2)
        model.fit(df)
        pred = model.predict(["2019-01", "2019-02"])
        assert pred.shape == (2, 5)

    def test_early_term_returns_zeros(self):
        df = self._make_macro_df()
        model = NaiveModel(lag=2)
        model.fit(df)
        pred = model.predict_term("2017-01")
        assert np.all(pred == 0)


class TestMicroLSTM:
    def test_forward_pass(self):
        from educast.models.lstm_micro import MicroLSTM
        import torch

        model = MicroLSTM(input_dim=FEAT_DIM_STUDENT, hidden_size=32, output_dim=NUM_COURSES)
        x = torch.randn(4, 3, FEAT_DIM_STUDENT)
        out = model(x)
        assert out.shape == (4, NUM_COURSES)
        assert torch.all(out >= 0) and torch.all(out <= 1)


class TestMacroLSTM:
    def test_forward_pass(self):
        from educast.models.lstm_macro import MacroLSTM
        import torch

        model = MacroLSTM(input_dim=NUM_COURSES, hidden_size=32, output_dim=NUM_COURSES)
        x = torch.randn(2, 4, NUM_COURSES)
        out = model(x)
        assert out.shape == (2, NUM_COURSES)
        assert torch.all(out >= 0)  # ReLU output


class TestMetrics:
    def test_mae_computation(self):
        from educast.evaluation.metrics import compute_mae, compute_mae_positive, compute_mae_negative
        actual = np.array([10, 20, 30])
        pred = np.array([12, 18, 30])
        assert compute_mae(actual, pred) == pytest.approx(4 / 3)
        assert compute_mae_positive(actual, pred) == pytest.approx(2.0)  # 12-10=2
        assert compute_mae_negative(actual, pred) == pytest.approx(2.0)  # 20-18=2
