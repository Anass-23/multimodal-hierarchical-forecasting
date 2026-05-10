"""Course2Vec MLP: flattened multi-hot windows + skip-gram course embeddings -> enrollment prediction."""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from gensim.models import Word2Vec
from torch.utils.data import DataLoader, TensorDataset

from educast.config import (
    MICRO_WINDOW_SIZE,
    NUM_COURSES,
    RANDOM_SEED,
)


class Course2VecMLP(nn.Module):
    """Feedforward MLP combining flattened multi-hot windows with course embeddings.

    Input: (batch, window_size * feat_dim + embedding_dim)
    Output: (batch, num_courses) with sigmoid activations.
    """

    def __init__(
        self,
        input_dim: int,
        output_dim: int = NUM_COURSES,
        dropout1: float = 0.3,
        dropout2: float = 0.2,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(dropout1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout2),
            nn.Linear(64, output_dim),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def train_course_embeddings(
    university_data: dict,
    course_to_idx: Dict[str, int],
    embedding_dim: int = 64,
    seed: int = RANDOM_SEED,
) -> np.ndarray:
    """Train skip-gram course embeddings from enrollment sequences.

    Each student's term-by-term course list becomes a sentence for Word2Vec.
    Returns (num_courses, embedding_dim) embedding matrix.
    """
    sentences: List[List[str]] = []
    for student in university_data.get("students", []):
        history = student.get("history", {})
        attempts = history.get("attempts", [])
        term_courses: Dict[tuple, List[str]] = defaultdict(list)
        for att in attempts:
            year, term = att.get("year"), att.get("term")
            cid = att["course"]["course_id"]
            if year and term and cid in course_to_idx:
                term_courses[(year, term)].append(cid)
        for key in sorted(term_courses.keys()):
            sentences.append(term_courses[key])

    model = Word2Vec(
        sentences=sentences,
        vector_size=embedding_dim,
        window=5,
        min_count=1,
        sg=1,
        seed=seed,
        workers=1,
        epochs=20,
    )

    embedding_matrix = np.zeros((NUM_COURSES, embedding_dim))
    idx_to_course = {v: k for k, v in course_to_idx.items()}
    for idx in range(NUM_COURSES):
        cid = idx_to_course.get(idx)
        if cid and cid in model.wv:
            embedding_matrix[idx] = model.wv[cid]

    return embedding_matrix


class Course2VecMLPTrainer:
    def __init__(
        self,
        input_dim: int,
        epochs: int = 100,
        batch_size: int = 64,
        lr: float = 0.001,
        seed: int = RANDOM_SEED,
        device: Optional[str] = None,
    ) -> None:
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.seed = seed
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        torch.manual_seed(seed)
        self.model = Course2VecMLP(input_dim=input_dim).to(self.device)
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.history: dict = {"train_loss": [], "val_loss": []}

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.1,
    ) -> dict:
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
        self.model.eval()
        with torch.no_grad():
            X_t = torch.FloatTensor(X).to(self.device)
            return self.model(X_t).cpu().numpy()
