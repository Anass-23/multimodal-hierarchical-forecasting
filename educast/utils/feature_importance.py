"""Feature importance heatmap (from TFG random forests)."""

from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from educast.models.random_forest import RandomForestManager


def plot_feature_importance_heatmap(
    manager: RandomForestManager,
    subject_groups: Optional[Dict[str, List[str]]] = None,
    title: str = "Feature Importance Heatmap",
    show: bool = False,
) -> plt.Figure:
    """Heatmap of feature importances: rows = target subjects, columns = source features."""
    subjects = manager.fitted_subjects
    if not subjects:
        raise ValueError("No fitted subjects in manager")

    rows = {}
    feature_names = None
    for subj in subjects:
        model = manager[subj]
        if model.is_fitted:
            importances = model.get_feature_importances()
            if feature_names is None:
                feature_names = model.get_feature_names()
            rows[subj] = importances

    if not rows:
        raise ValueError("No fitted models found")

    df = pd.DataFrame(rows, index=feature_names).T

    fig, ax = plt.subplots(figsize=(max(12, len(feature_names) * 0.15), max(6, len(subjects) * 0.4)))
    sns.heatmap(
        df, cmap="YlOrRd", linewidths=0.5, linecolor="white",
        ax=ax, cbar_kws={"label": "Importance"},
    )
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Feature")
    ax.set_ylabel("Target Subject")
    plt.xticks(rotation=90, fontsize=7)
    plt.yticks(fontsize=9)
    plt.tight_layout()

    if show:
        plt.show()
    else:
        plt.close(fig)

    return fig


def plot_top_features_per_subject(
    manager: RandomForestManager,
    top_n: int = 10,
    show: bool = False,
) -> plt.Figure:
    """Horizontal bar charts of top N features per subject."""
    subjects = manager.fitted_subjects
    n_subjects = len(subjects)
    n_cols = min(3, n_subjects)
    n_rows = (n_subjects + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 3 * n_rows))
    if n_subjects == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for idx, subj in enumerate(subjects):
        model = manager[subj]
        if not model.is_fitted:
            continue

        importances = model.get_feature_importances()
        names = model.get_feature_names()

        sorted_idx = np.argsort(importances)[-top_n:]
        axes[idx].barh(
            [names[i] for i in sorted_idx],
            importances[sorted_idx],
            color="steelblue",
        )
        axes[idx].set_title(subj, fontsize=10)
        axes[idx].tick_params(axis="y", labelsize=7)

    for idx in range(n_subjects, len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle(f"Top {top_n} Features per Subject", fontsize=14)
    plt.tight_layout()

    if show:
        plt.show()
    else:
        plt.close(fig)

    return fig
