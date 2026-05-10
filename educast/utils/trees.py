"""Decision tree rendering (from TFG)."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

from educast.models.decision_tree import SubjectTreePipeline


def plot_decision_tree(
    pipeline: SubjectTreePipeline,
    transform_name: str = "",
    output_dir: Optional[Path] = None,
    show: bool = False,
) -> plt.Figure:
    """Render a fitted decision tree."""
    clf = pipeline.pipeline.named_steps["clf"]
    feature_names = pipeline.get_feature_names()

    fig, ax = plt.subplots(figsize=(25, 10), dpi=150)
    plot_tree(
        clf,
        feature_names=feature_names,
        class_names=["False", "True"],
        filled=True,
        ax=ax,
    )
    ax.set_title(f"Decision Tree: {pipeline.subject_id}", fontsize=14)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{pipeline.subject_id}_{clf.max_depth}_{transform_name}"
        fig.savefig(output_dir / f"{fname}.png", bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return fig


def plot_pruning_analysis(
    pipeline: SubjectTreePipeline,
    X_train,
    X_test,
    output_dir: Optional[Path] = None,
    show: bool = False,
) -> plt.Figure:
    """Cost Complexity Pruning: 3-panel plot of impurity, node count, and accuracy vs alpha."""
    from sklearn.tree import DecisionTreeClassifier

    clf = pipeline.pipeline.named_steps["clf"]
    preprocessor = pipeline.pipeline.named_steps["preprocessor"]

    X_train_t = preprocessor.transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    path = clf.cost_complexity_pruning_path(X_train_t, pipeline.y_train)
    ccp_alphas = path.ccp_alphas[:-1]
    impurities = path.impurities[:-1]

    train_scores, test_scores, node_counts = [], [], []
    for alpha in ccp_alphas:
        dt = DecisionTreeClassifier(
            max_depth=clf.max_depth, ccp_alpha=alpha, random_state=clf.random_state
        )
        dt.fit(X_train_t, pipeline.y_train)
        train_scores.append(dt.score(X_train_t, pipeline.y_train))
        test_scores.append(dt.score(X_test_t, pipeline.y_test))
        node_counts.append(dt.tree_.node_count)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].plot(ccp_alphas, impurities, marker="o", markersize=3)
    axes[0].set_xlabel("Effective Alpha")
    axes[0].set_ylabel("Total Impurity")
    axes[0].set_title("Impurity vs Alpha")

    axes[1].plot(ccp_alphas, node_counts, marker="o", markersize=3)
    axes[1].set_xlabel("Effective Alpha")
    axes[1].set_ylabel("Node Count")
    axes[1].set_title("Node Count vs Alpha")

    axes[2].plot(ccp_alphas, train_scores, marker="o", markersize=3, label="Train")
    axes[2].plot(ccp_alphas, test_scores, marker="o", markersize=3, label="Test")
    axes[2].set_xlabel("Effective Alpha")
    axes[2].set_ylabel("Accuracy")
    axes[2].set_title("Accuracy vs Alpha")
    axes[2].legend()

    fig.suptitle(f"Pruning Analysis: {pipeline.subject_id}", fontsize=14)
    plt.tight_layout()

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{pipeline.subject_id}_prun.png", bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return fig
