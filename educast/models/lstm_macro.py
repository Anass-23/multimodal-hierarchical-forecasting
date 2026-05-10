"""Aggregate LSTM (Macro): course-level enrollment time series prediction."""

from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from torch.utils.data import DataLoader, TensorDataset

from educast.config import (
    MACRO_BATCH_SIZE,
    MACRO_DROPOUT,
    MACRO_EPOCHS,
    MACRO_HIDDEN_SIZE,
    MACRO_LR,
    MACRO_NUM_LAYERS,
    NUM_COURSES,
    RANDOM_SEED,
)


class MacroLSTM(nn.Module):
    """Course-level aggregate LSTM for enrollment count regression.

    Architecture: LSTM -> Dropout -> Dense(relu) -> Dense(relu)
    Input shape: (batch, window_size, n_features)
    Output shape: (batch, num_courses) with ReLU (non-negative counts).
    """

    def __init__(
        self,
        input_dim: int = NUM_COURSES,
        hidden_size: int = MACRO_HIDDEN_SIZE,
        num_layers: int = MACRO_NUM_LAYERS,
        dropout: float = MACRO_DROPOUT,
        output_dim: int = NUM_COURSES,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.dense = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.output = nn.Linear(64, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: (batch, seq_len, input_dim) -> (batch, output_dim) non-negative counts."""
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        x = self.dropout(last_hidden)
        x = self.relu(self.dense(x))
        return self.relu(self.output(x))


class MacroLSTMTrainer:
    """Trainer for the course-level Macro LSTM model."""

    def __init__(
        self,
        input_dim: int = NUM_COURSES,
        hidden_size: int = MACRO_HIDDEN_SIZE,
        num_layers: int = MACRO_NUM_LAYERS,
        dropout: float = MACRO_DROPOUT,
        epochs: int = MACRO_EPOCHS,
        batch_size: int = MACRO_BATCH_SIZE,
        lr: float = MACRO_LR,
        seed: int = RANDOM_SEED,
        device: Optional[str] = None,
        scaler_type: str = "robust",
    ) -> None:
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.seed = seed
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.scaler_type = scaler_type

        torch.manual_seed(seed)
        self.model = MacroLSTM(
            input_dim=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
        ).to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.history: dict = {"train_loss": [], "val_loss": []}

        if scaler_type == "robust":
            self.scaler_x = RobustScaler()
            self.scaler_y = RobustScaler()
        else:
            self.scaler_x = MinMaxScaler()
            self.scaler_y = MinMaxScaler()

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.1,
    ) -> dict:
        """Train the model. Returns training history dict."""
        n_val = max(1, int(len(X_train) * validation_split))
        X_val, y_val = X_train[:n_val], y_train[:n_val]
        X_t, y_t = X_train[n_val:], y_train[n_val:]

        train_ds = TensorDataset(
            torch.FloatTensor(X_t).to(self.device),
            torch.FloatTensor(y_t).to(self.device),
        )
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=False)

        X_val_t = torch.FloatTensor(X_val).to(self.device)
        y_val_t = torch.FloatTensor(y_val).to(self.device)

        for epoch in range(self.epochs):
            self.model.train()
            epoch_loss = 0.0
            for X_batch, y_batch in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()

            avg_train_loss = epoch_loss / len(train_loader)
            self.history["train_loss"].append(avg_train_loss)

            self.model.eval()
            with torch.no_grad():
                val_pred = self.model(X_val_t)
                val_loss = self.criterion(val_pred, y_val_t).item()
            self.history["val_loss"].append(val_loss)

        return self.history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return (samples, num_courses) count predictions."""
        self.model.eval()
        with torch.no_grad():
            X_t = torch.FloatTensor(X).to(self.device)
            return self.model(X_t).cpu().numpy()

    def predict_real(
        self, X: np.ndarray, scaler_y: Optional[object] = None,
    ) -> np.ndarray:
        """Predict and inverse-transform to real counts. Uses self.scaler_y if scaler_y is None."""
        scaled_pred = self.predict(X)
        sy = scaler_y or self.scaler_y
        return np.maximum(0, sy.inverse_transform(scaled_pred))
