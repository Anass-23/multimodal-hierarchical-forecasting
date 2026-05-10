"""Forecast plots, per-course bars, model comparison charts."""

from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot_global_mae_comparison(
    mae_scores: Dict[str, float],
    title: str = "Global MAE",
    colors: Optional[Dict[str, str]] = None,
) -> plt.Figure:
    """Bar chart comparing global MAE across models."""
    default_colors = {"Naive": "gray", "Student": "royalblue", "Macro": "orange"}
    colors = colors or default_colors

    fig, ax = plt.subplots(figsize=(10, 5))
    names = list(mae_scores.keys())
    values = list(mae_scores.values())
    bar_colors = [colors.get(n, "steelblue") for n in names]

    bars = ax.bar(names, values, color=bar_colors, alpha=0.9, edgecolor="k")
    ax.set_title(title, fontsize=14)
    ax.set_ylabel("Avg Error (Students)")

    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{bar.get_height():.2f}",
            ha="center",
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


def plot_term_forecast(
    df_results: pd.DataFrame,
    term: str,
    model_columns: Dict[str, str],
    max_courses: int = 30,
) -> Optional[plt.Figure]:
    """Grouped bar chart for a single term: actual vs predicted per course."""
    df_term = df_results[df_results["Term"] == term].copy()
    if df_term.empty:
        return None

    df_term = df_term.sort_values("Actual", ascending=False).head(max_courses)

    melt_cols = ["Actual"] + list(model_columns.values())
    available_cols = [c for c in melt_cols if c in df_term.columns]

    df_melt = df_term.melt(
        id_vars=["Course"],
        value_vars=available_cols,
        var_name="Model",
        value_name="Count",
    )

    palette = {
        "Actual": "black",
        "Pred_Naive": "lightgray",
        "Pred_Student": "royalblue",
        "Pred_Macro": "orange",
    }

    fig, ax = plt.subplots(figsize=(max(12, len(df_term) * 0.45), 6))
    sns.barplot(data=df_melt, x="Course", y="Count", hue="Model", palette=palette, ax=ax)
    ax.set_title(f"Forecast {term}", fontsize=14)
    ax.set_xlabel("Course")
    ax.set_ylabel("Student Count")
    plt.xticks(rotation=90, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_per_course_mae(
    df_results: pd.DataFrame,
    model_names: List[str],
    title: str = "Mean Absolute Error per Course",
) -> plt.Figure:
    """Line plot of MAE per course across models."""
    course_stats = df_results.groupby("Course").agg(
        {f"Err_{n}": "mean" for n in model_names if f"Err_{n}" in df_results.columns}
    ).reset_index()
    course_stats = course_stats.sort_values(f"Err_{model_names[0]}", ascending=False)

    x = np.arange(len(course_stats))
    fig, ax = plt.subplots(figsize=(18, 8))

    colors = {"Naive": "gray", "Student": "royalblue", "Macro": "orange"}
    for name in model_names:
        col = f"Err_{name}"
        if col in course_stats.columns:
            ax.plot(x, course_stats[col], label=f"Err {name}",
                    color=colors.get(name, None), linewidth=2, alpha=0.8)

    ax.set_title(title, fontsize=16)
    ax.set_ylabel("Avg Error (Students)")
    ax.set_xticks(x)
    ax.set_xticklabels(course_stats["Course"], rotation=90, fontsize=9)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_enrollment_total_comparison(
    df_results: pd.DataFrame,
    model_names: List[str],
    title: str = "Total Enrollment by Course",
) -> plt.Figure:
    """Line plot comparing total predicted vs actual enrollment per course."""
    agg_cols = {"Actual": "sum"}
    for n in model_names:
        col = f"Pred_{n}"
        if col in df_results.columns:
            agg_cols[col] = "sum"

    course_stats = df_results.groupby("Course").agg(agg_cols).reset_index()
    course_stats = course_stats.sort_values("Actual", ascending=False)
    x = np.arange(len(course_stats))

    fig, ax = plt.subplots(figsize=(18, 8))
    ax.plot(x, course_stats["Actual"], "k--o", linewidth=2, label="Actual")

    colors = {"Naive": "red", "Student": "blue", "Macro": "orange"}
    for name in model_names:
        col = f"Pred_{name}"
        if col in course_stats.columns:
            ax.plot(x, course_stats[col], alpha=0.8, linewidth=2,
                    label=name, color=colors.get(name, None))

    ax.set_title(title, fontsize=16)
    ax.set_ylabel("Total Students")
    ax.set_xticks(x)
    ax.set_xticklabels(course_stats["Course"], rotation=90, fontsize=9)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_forecast_heatmap(
    df_results: pd.DataFrame,
    model_names: List[str],
    title: str = "Forecast Comparison Table",
) -> plt.Figure:
    """Interleaved heatmap of actual vs predicted per term per course."""
    pivot_cols = ["Actual"] + [f"Pred_{n}" for n in model_names if f"Pred_{n}" in df_results.columns]
    df_pivot = df_results.groupby(["Course", "Term"])[pivot_cols].sum().unstack("Term")

    total_acts = df_pivot["Actual"].sum(axis=1)
    df_pivot = df_pivot.loc[total_acts.sort_values(ascending=False).index]

    terms = sorted(df_results["Term"].unique())
    final_df = pd.DataFrame(index=df_pivot.index)
    new_labels = []

    for term in terms:
        for col in pivot_cols:
            if (col, term) in df_pivot.columns:
                final_df[f"{term}_{col}"] = df_pivot[(col, term)]
                short = col.replace("Pred_", "").replace("Actual", "Act")[:3]
                new_labels.append(f"{term}\n{short}")

    fig_height = max(12, len(final_df) * 0.35)
    fig_width = max(16, len(terms) * len(pivot_cols) * 0.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    sns.heatmap(
        final_df.fillna(0), annot=True, fmt=".0f", cmap="plasma",
        mask=final_df.fillna(0) == 0, linewidths=0.1, linecolor="white",
        cbar_kws={"label": "Student Count", "shrink": 0.5}, ax=ax,
    )
    ax.set_xticklabels(new_labels, rotation=0, fontsize=9)

    n_cols_per_term = len(pivot_cols)
    for i in range(n_cols_per_term, len(new_labels), n_cols_per_term):
        ax.axvline(i, color="black", linestyle="--", linewidth=1)

    ax.set_title(title, fontsize=16)
    plt.tight_layout()
    return fig


def plot_classification_metrics(
    df_metrics: pd.DataFrame,
    title: str = "Per-Subject Classification Metrics",
    threshold_line: float = 0.8,
    subject_name_map: Optional[Dict[str, str]] = None,
) -> plt.Figure:
    """Line plot of recall, precision, F1 per subject.

    When subject_name_map is provided, tick labels show "Acronym\\nFull Name".
    """
    fig, ax = plt.subplots(figsize=(max(12, len(df_metrics) * 0.5), 6))
    x = np.arange(len(df_metrics))

    ax.plot(x, df_metrics["Recall"], "o-", color="purple", label="Recall")
    ax.plot(x, df_metrics["Precision"], "s-", color="green", label="Precision")
    ax.plot(x, df_metrics["F1"], "^-", color="red", label="F1-Score")
    ax.axhline(y=threshold_line, color="gray", linestyle="--", alpha=0.5, label=f"{threshold_line}")

    ax.set_title(title, fontsize=14)
    ax.set_ylabel("Score")
    ax.set_xticks(x)

    if subject_name_map:
        labels = [
            f"{s}\n{subject_name_map.get(s, s)}" for s in df_metrics["Subject"]
        ]
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    else:
        ax.set_xticklabels(df_metrics["Subject"], rotation=90, fontsize=9)

    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    return fig


def plot_predictions_vs_actual_bars(
    subjects: List[str],
    actual_counts: np.ndarray,
    predicted_counts: np.ndarray,
    title: str = "Predictions vs Actual",
) -> plt.Figure:
    """Side-by-side bar chart of actual vs predicted enrollment counts."""
    fig, ax = plt.subplots(figsize=(max(12, len(subjects) * 0.4), 6))
    x = np.arange(len(subjects))
    width = 0.35

    ax.bar(x - width / 2, actual_counts, width, label="Actual", color="steelblue")
    ax.bar(x + width / 2, predicted_counts, width, label="Predicted", color="orange")

    ax.set_title(title, fontsize=14)
    ax.set_ylabel("Count")
    ax.set_xticks(x)
    ax.set_xticklabels(subjects, rotation=90, fontsize=9)
    ax.legend()
    plt.tight_layout()
    return fig
