"""Student-profile LSTM (Micro): per-student 153-dim sequences -> 51-dim enrollment prediction."""

from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from educast.config import (
    FEAT_DIM_STUDENT,
    MICRO_BATCH_SIZE,
    MICRO_DROPOUT,
    MICRO_EPOCHS,
    MICRO_HIDDEN_SIZE,
    MICRO_LR,
    MICRO_NUM_LAYERS,
    NUM_COURSES,
    RANDOM_SEED,
)


class MicroLSTM(nn.Module):
    """Student-level LSTM for multi-label enrollment prediction.

    Architecture: Dense -> LSTM -> Dropout -> Dense(sigmoid)
    Input shape: (batch, window_size, feat_dim)
    Output shape: (batch, num_courses) with sigmoid activations.
    """

    def __init__(
        self,
        input_dim: int = FEAT_DIM_STUDENT,
        hidden_size: int = MICRO_HIDDEN_SIZE,
        num_layers: int = MICRO_NUM_LAYERS,
        dropout: float = MICRO_DROPOUT,
        output_dim: int = NUM_COURSES,
    ) -> None:
        super().__init__()
        self.projection = nn.Linear(input_dim, 64)
        self.relu = nn.ReLU()
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.dense = nn.Linear(hidden_size, 64)
        self.output = nn.Linear(64, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: (batch, seq_len, input_dim) -> (batch, output_dim) probabilities."""
        x = self.relu(self.projection(x))
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        x = self.dropout(last_hidden)
        x = self.relu(self.dense(x))
        return self.sigmoid(self.output(x))


class MicroLSTMTrainer:
    """Trainer for the student-level Micro LSTM model."""

    def __init__(
        self,
        input_dim: int = FEAT_DIM_STUDENT,
        hidden_size: int = MICRO_HIDDEN_SIZE,
        num_layers: int = MICRO_NUM_LAYERS,
        dropout: float = MICRO_DROPOUT,
        epochs: int = MICRO_EPOCHS,
        batch_size: int = MICRO_BATCH_SIZE,
        lr: float = MICRO_LR,
        seed: int = RANDOM_SEED,
        device: Optional[str] = None,
    ) -> None:
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.seed = seed
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        torch.manual_seed(seed)
        self.model = MicroLSTM(
            input_dim=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
        ).to(self.device)
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.history: dict = {"train_loss": [], "val_loss": []}

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.1,
    ) -> dict:
        """Train the model. Returns training history dict."""
        n_val = int(len(X_train) * validation_split)
        X_val, y_val = X_train[:n_val], y_train[:n_val]
        X_t, y_t = X_train[n_val:], y_train[n_val:]

        train_ds = TensorDataset(
            torch.FloatTensor(X_t).to(self.device),
            torch.FloatTensor(y_t).to(self.device),
        )
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)

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
        """Return (samples, num_courses) probability array."""
        self.model.eval()
        with torch.no_grad():
            X_t = torch.FloatTensor(X).to(self.device)
            return self.model(X_t).cpu().numpy()

    def predict_binary(self, X: np.ndarray, threshold: float = 0.45) -> np.ndarray:
        """Return (samples, num_courses) binary array at given threshold."""
        probs = self.predict(X)
        return (probs >= threshold).astype(int)
