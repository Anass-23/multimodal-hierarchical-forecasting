"""Experiment registry: name -> config -> model -> data transform."""

from educast.config import (
    FOREST_MAX_DEPTH,
    FOREST_MAX_FEATURES,
    MACRO_BATCH_SIZE,
    MACRO_DROPOUT,
    MACRO_EPOCHS,
    MACRO_HIDDEN_SIZE,
    MACRO_NUM_LAYERS,
    MACRO_WINDOW_SIZE,
    MICRO_BATCH_SIZE,
    MICRO_DROPOUT,
    MICRO_EPOCHS,
    MICRO_HIDDEN_SIZE,
    MICRO_NUM_LAYERS,
    MICRO_WINDOW_SIZE,
    TREE_MAX_DEPTH,
)

EXPERIMENTS = {
    "naive": {
        "model": "naive",
        "transform": "aggregate",
        "params": {"lag": 2},
    },
    "macro_lstm": {
        "model": "lstm_macro",
        "transform": "aggregate_seq",
        "params": {
            "hidden_size": MACRO_HIDDEN_SIZE,
            "num_layers": MACRO_NUM_LAYERS,
            "dropout": MACRO_DROPOUT,
            "epochs": MACRO_EPOCHS,
            "batch_size": MACRO_BATCH_SIZE,
            "window_size": MACRO_WINDOW_SIZE,
        },
    },
    "micro_lstm": {
        "model": "lstm_micro",
        "transform": "multihot_153",
        "params": {
            "hidden_size": MICRO_HIDDEN_SIZE,
            "num_layers": MICRO_NUM_LAYERS,
            "dropout": MICRO_DROPOUT,
            "epochs": MICRO_EPOCHS,
            "batch_size": MICRO_BATCH_SIZE,
            "window_size": MICRO_WINDOW_SIZE,
        },
    },
    "course2vec_mlp": {
        "model": "course2vec_mlp",
        "transform": "multihot_flat",
        "params": {
            "embedding_dim": 64,
            "epochs": 100,
            "batch_size": 64,
            "window_size": MICRO_WINDOW_SIZE,
        },
    },
    "decision_tree_d4_t1": {
        "model": "decision_tree",
        "transform": "tabular_t1",
        "params": {"max_depth": TREE_MAX_DEPTH},
    },
    "decision_tree_d4_t2": {
        "model": "decision_tree",
        "transform": "tabular_t2",
        "params": {"max_depth": TREE_MAX_DEPTH},
    },
    "random_forest_t1": {
        "model": "random_forest",
        "transform": "tabular_t1",
        "params": {
            "auto_estimators": True,
            "max_depth": FOREST_MAX_DEPTH,
            "max_features": FOREST_MAX_FEATURES,
        },
    },
    "random_forest_t2": {
        "model": "random_forest",
        "transform": "tabular_t2",
        "params": {
            "auto_estimators": True,
            "max_depth": FOREST_MAX_DEPTH,
            "max_features": FOREST_MAX_FEATURES,
        },
    },
    "xgboost_t2": {
        "model": "xgboost",
        "transform": "tabular_t2",
        "params": {
            "max_depth": TREE_MAX_DEPTH,
            "n_estimators": 200,
            "learning_rate": 0.1,
        },
    },
}


def get_experiment(name: str) -> dict:
    if name not in EXPERIMENTS:
        available = ", ".join(EXPERIMENTS.keys())
        raise KeyError(f"Unknown experiment '{name}'. Available: {available}")
    return EXPERIMENTS[name]


def list_experiments() -> list:
    return list(EXPERIMENTS.keys())
