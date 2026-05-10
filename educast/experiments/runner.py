"""Run single or all experiments with structured output to results/."""

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from educast.config import (
    MACRO_WINDOW_SIZE,
    MICRO_WINDOW_SIZE,
    NUM_COURSES,
    RANDOM_SEED,
    RESULTS_DIR,
    SPLIT_YEAR,
    SUBJECTS_ALL,
)
from educast.data.loader import (
    build_acronym_maps,
    build_course_vocabulary,
    load_university_json,
)
from educast.data.splits import split_by_term_string, split_by_year, tabular_train_test_split
from educast.data.transforms import (
    build_tabular_from_json,
    create_macro_dataset,
    create_macro_extended_dataset,
    primera_transformacio,
    segona_transformacio,
)
from educast.evaluation.export import build_experiment_metadata, export_results
from educast.evaluation.metrics import (
    compute_mae,
    compute_mae_negative,
    compute_mae_positive,
    per_course_mae,
    per_subject_classification_metrics,
)
from sklearn.metrics import (
    f1_score as sk_f1,
    precision_score as sk_precision,
    recall_score as sk_recall,
)

from educast.experiments.registry import EXPERIMENTS, get_experiment
from educast.features.multihot import build_macro_windows, build_student_dataset
from educast.features.tabular import identify_feature_types


def _build_unified_per_course(
    course_names: List[str],
    *,
    mae_values: Optional[List[float]] = None,
    mae_pos_values: Optional[List[float]] = None,
    mae_neg_values: Optional[List[float]] = None,
    precision_values: Optional[List[float]] = None,
    recall_values: Optional[List[float]] = None,
    f1_values: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Build a unified per-course DataFrame with all metric columns.

    Missing metrics are filled with NaN so every model's DataFrame has the
    same schema: Course, MAE, MAE+, MAE-, Precision, Recall, F1.
    """
    n = len(course_names)
    data = {
        "Course": course_names,
        "MAE": mae_values if mae_values is not None else [float("nan")] * n,
        "MAE+": mae_pos_values if mae_pos_values is not None else [float("nan")] * n,
        "MAE-": mae_neg_values if mae_neg_values is not None else [float("nan")] * n,
        "Precision": precision_values if precision_values is not None else [float("nan")] * n,
        "Recall": recall_values if recall_values is not None else [float("nan")] * n,
        "F1": f1_values if f1_values is not None else [float("nan")] * n,
    }
    return pd.DataFrame(data)


def _build_unified_metrics(per_course: pd.DataFrame) -> Dict[str, float]:
    """Compute global averages from a unified per-course DataFrame."""
    m: Dict[str, float] = {}
    for col in ["MAE", "MAE+", "MAE-", "Precision", "Recall", "F1"]:
        vals = per_course[col].dropna()
        if len(vals) > 0:
            m[col] = float(vals.mean())
    return m


def run_naive(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run the naive baseline experiment."""
    from educast.models.naive import NaiveModel

    df_macro = create_macro_dataset(university_data, course_ids)
    model = NaiveModel(lag=params.get("lag", 2))
    model.fit(df_macro)

    all_terms = df_macro.index.tolist()
    test_terms = [t for t in all_terms if int(t.split("-")[0]) >= SPLIT_YEAR]

    predictions = model.predict(test_terms)
    actuals = df_macro.loc[test_terms].values.astype(float)

    idx_to_course = {i: cid for i, cid in enumerate(course_ids)}
    mae_df = per_course_mae(actuals, predictions, idx_to_course)
    per_course = _build_unified_per_course(
        mae_df["Course"].tolist(),
        mae_values=mae_df["MAE"].tolist(),
        mae_pos_values=mae_df["MAE+"].tolist(),
        mae_neg_values=mae_df["MAE-"].tolist(),
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "naive", "aggregate", params, seed,
        train_samples=len(all_terms) - len(test_terms),
        test_samples=len(test_terms),
        split_info=f"year >= {SPLIT_YEAR}",
    )
    metadata["_trainer"] = model
    return metrics, per_course, metadata


def run_micro_lstm(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run the student-level Micro LSTM experiment."""
    from educast.models.lstm_micro import MicroLSTMTrainer

    window_size = params.get("window_size", MICRO_WINDOW_SIZE)
    X_all, y_all, meta_all = build_student_dataset(
        university_data, course_to_idx, window_size
    )

    X_train, y_train, meta_train, X_test, y_test, meta_test = split_by_year(
        X_all, y_all, meta_all, SPLIT_YEAR
    )

    trainer = MicroLSTMTrainer(
        input_dim=X_train.shape[2],
        hidden_size=params.get("hidden_size", 128),
        num_layers=params.get("num_layers", 1),
        dropout=params.get("dropout", 0.2),
        epochs=params.get("epochs", 100),
        batch_size=params.get("batch_size", 64),
        seed=seed,
    )
    trainer.fit(X_train, y_train)

    pred_probs = trainer.predict(X_test)
    student_agg: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(NUM_COURSES))
    actual_agg: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(NUM_COURSES))

    for i, (year, term, sid) in enumerate(meta_test):
        term_key = f"{year}-{term:02d}"
        student_agg[term_key] += pred_probs[i]
        actual_agg[term_key] += y_test[i]

    terms = sorted(student_agg.keys())
    predictions = np.array([student_agg[t] for t in terms])
    actuals = np.array([actual_agg[t] for t in terms])

    idx_to_course = {i: cid for i, cid in enumerate(course_ids)}
    mae_df = per_course_mae(actuals, predictions, idx_to_course)

    binary_preds = (pred_probs > 0.5).astype(int)
    prec_list, rec_list, f1_list = [], [], []
    for c_idx in range(NUM_COURSES):
        y_true_c = y_test[:, c_idx]
        y_pred_c = binary_preds[:, c_idx]
        prec_list.append(float(sk_precision(y_true_c, y_pred_c, zero_division=0)))
        rec_list.append(float(sk_recall(y_true_c, y_pred_c, zero_division=0)))
        f1_list.append(float(sk_f1(y_true_c, y_pred_c, zero_division=0)))

    per_course = _build_unified_per_course(
        mae_df["Course"].tolist(),
        mae_values=mae_df["MAE"].tolist(),
        mae_pos_values=mae_df["MAE+"].tolist(),
        mae_neg_values=mae_df["MAE-"].tolist(),
        precision_values=prec_list,
        recall_values=rec_list,
        f1_values=f1_list,
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "lstm_micro", "multihot_153", params, seed,
        train_samples=len(X_train),
        test_samples=len(X_test),
        split_info=f"year >= {SPLIT_YEAR}",
    )
    metadata["_trainer"] = trainer
    return metrics, per_course, metadata


def run_macro_lstm(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run the aggregate Macro LSTM experiment."""
    from educast.models.lstm_macro import MacroLSTMTrainer

    window_size = params.get("window_size", MACRO_WINDOW_SIZE)
    df_macro = create_macro_extended_dataset(university_data, course_ids)
    count_cols = [c for c in df_macro.columns if c.startswith("Count_")]

    scaler_x = RobustScaler()
    scaler_y = RobustScaler()
    data_x = scaler_x.fit_transform(df_macro.values)
    data_y = scaler_y.fit_transform(df_macro[count_cols].values)
    terms = df_macro.index.tolist()

    X_all, y_all, meta_all = build_macro_windows(
        data_x, data_y, terms, window_size
    )
    X_train, y_train, meta_train, X_test, y_test, meta_test = split_by_term_string(
        X_all, y_all, meta_all, SPLIT_YEAR
    )

    trainer = MacroLSTMTrainer(
        input_dim=X_train.shape[2],
        hidden_size=params.get("hidden_size", 128),
        num_layers=params.get("num_layers", 1),
        dropout=params.get("dropout", 0.3),
        epochs=params.get("epochs", 100),
        batch_size=params.get("batch_size", 4),
        seed=seed,
    )
    trainer.fit(X_train, y_train)

    pred_scaled = trainer.predict(X_test)
    predictions = np.maximum(0, scaler_y.inverse_transform(pred_scaled))
    actuals = scaler_y.inverse_transform(y_test)

    idx_to_course = {i: cid for i, cid in enumerate(course_ids)}
    mae_df = per_course_mae(actuals, predictions, idx_to_course)
    per_course = _build_unified_per_course(
        mae_df["Course"].tolist(),
        mae_values=mae_df["MAE"].tolist(),
        mae_pos_values=mae_df["MAE+"].tolist(),
        mae_neg_values=mae_df["MAE-"].tolist(),
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "lstm_macro", "aggregate_seq", params, seed,
        train_samples=len(X_train),
        test_samples=len(X_test),
        split_info=f"year >= {SPLIT_YEAR}",
    )
    metadata["_trainer"] = trainer
    return metrics, per_course, metadata


def _load_tabular(
    university_data: dict,
    transform: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Build tabular dataset from JSON and apply the requested transform."""
    id_to_acr, _, acronym_list = build_acronym_maps(university_data)
    raw_df = build_tabular_from_json(university_data, id_to_acr)

    if transform == "tabular_t1":
        dataset = primera_transformacio(raw_df, acronym_list)
    elif transform == "tabular_t2":
        dataset = segona_transformacio(raw_df, acronym_list)
    else:
        raise ValueError(f"Unknown tabular transform: {transform}")

    num_acr = len(acronym_list)
    X = dataset.iloc[:, :-num_acr]
    y = dataset.iloc[:, -num_acr:]

    # Fill missing values (same logic as old load_tabular_dataset)
    m_cols = X.columns[X.columns.str.endswith(".m")]
    n_cols = X.columns[X.columns.str.endswith(".n")]
    becat_cols = X.columns[X.columns.str.endswith("becat")]
    X[m_cols] = X[m_cols].fillna(False)
    X[n_cols] = X[n_cols].fillna(0.0)
    X[becat_cols] = X[becat_cols].fillna(False)
    for col in ["VIA", "ORDRE", "NACC"]:
        if col in X.columns:
            X[col] = X[col].fillna(0)

    subjects = [s for s in SUBJECTS_ALL if s in y.columns]
    return X, y, subjects


def run_decision_tree(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
    transform: str = "tabular_t1",
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run per-subject decision tree experiment."""
    from educast.models.decision_tree import DecisionTreeManager, SubjectTreePipeline

    X, y, subjects = _load_tabular(university_data, transform)
    dataset_version = "v1" if transform == "tabular_t1" else "v2"
    cat_feats, num_feats = identify_feature_types(X, dataset_version)

    from sklearn.model_selection import train_test_split as sk_split
    X_train, X_test, y_train_full, y_test_full = sk_split(
        X, y, test_size=0.2, random_state=seed
    )

    manager = DecisionTreeManager()
    for subj in subjects:
        pipeline = SubjectTreePipeline(
            subject_id=subj,
            y_train=y_train_full[subj].values.astype(int),
            y_test=y_test_full[subj].values.astype(int),
            numerical_features=num_feats,
            categorical_features=cat_feats,
            max_depth=params.get("max_depth", 4),
            random_state=seed,
        )
        manager.add_model(subj, pipeline)

    manager.fit(subjects, X_train)
    results = manager.evaluate(X_test)

    course_names, mae_list, prec_list, rec_list, f1_list = [], [], [], [], []
    for subj in subjects:
        if subj not in results:
            continue
        r, p, f = results[subj]
        pipeline = manager.models[subj]
        y_pred = pipeline.predict(X_test)
        y_true = pipeline.y_test
        # Count-based MAE: aggregate difference over all test students
        mae = abs(int(y_pred.sum()) - int(y_true.sum()))
        course_names.append(subj)
        mae_list.append(float(mae))
        prec_list.append(float(p))
        rec_list.append(float(r))
        f1_list.append(float(f))

    per_course = _build_unified_per_course(
        course_names,
        mae_values=mae_list,
        precision_values=prec_list,
        recall_values=rec_list,
        f1_values=f1_list,
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "decision_tree", transform, params, seed,
        train_samples=len(X_train),
        test_samples=len(X_test),
        split_info=f"random split, seed={seed}",
    )
    metadata["_trainer"] = manager
    return metrics, per_course, metadata


def run_random_forest(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
    transform: str = "tabular_t1",
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run per-subject random forest experiment."""
    from educast.models.random_forest import RandomForestManager, SubjectForestPipeline

    X, y, subjects = _load_tabular(university_data, transform)
    dataset_version = "v1" if transform == "tabular_t1" else "v2"
    cat_feats, num_feats = identify_feature_types(X, dataset_version)

    from sklearn.model_selection import train_test_split as sk_split
    X_train, X_test, y_train_full, y_test_full = sk_split(
        X, y, test_size=0.2, random_state=seed
    )

    manager = RandomForestManager()
    for subj in subjects:
        pipeline = SubjectForestPipeline(
            subject_id=subj,
            y_train=y_train_full[subj].values.astype(int),
            y_test=y_test_full[subj].values.astype(int),
            numerical_features=num_feats,
            categorical_features=cat_feats,
            max_depth=params.get("max_depth", 4),
            max_features=params.get("max_features", "sqrt"),
            auto_estimators=params.get("auto_estimators", True),
            random_state=seed,
        )
        manager.add_model(subj, pipeline)

    manager.fit(subjects, X_train)
    results = manager.evaluate(X_test)

    course_names, mae_list, prec_list, rec_list, f1_list = [], [], [], [], []
    for subj in subjects:
        if subj not in results:
            continue
        r, p, f = results[subj]
        pipeline = manager.models[subj]
        y_pred = pipeline.predict(X_test)
        y_true = pipeline.y_test
        mae = abs(int(y_pred.sum()) - int(y_true.sum()))
        course_names.append(subj)
        mae_list.append(float(mae))
        prec_list.append(float(p))
        rec_list.append(float(r))
        f1_list.append(float(f))

    per_course = _build_unified_per_course(
        course_names,
        mae_values=mae_list,
        precision_values=prec_list,
        recall_values=rec_list,
        f1_values=f1_list,
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "random_forest", transform, params, seed,
        train_samples=len(X_train),
        test_samples=len(X_test),
        split_info=f"random split, seed={seed}",
    )
    metadata["_trainer"] = manager
    return metrics, per_course, metadata


def run_xgboost(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
    transform: str = "tabular_t2",
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run per-subject XGBoost experiment."""
    from educast.models.xgboost_clf import XGBoostManager, SubjectXGBPipeline

    X, y, subjects = _load_tabular(university_data, transform)
    dataset_version = "v1" if transform == "tabular_t1" else "v2"
    cat_feats, num_feats = identify_feature_types(X, dataset_version)

    from sklearn.model_selection import train_test_split as sk_split
    X_train, X_test, y_train_full, y_test_full = sk_split(
        X, y, test_size=0.2, random_state=seed
    )

    manager = XGBoostManager()
    for subj in subjects:
        pipeline = SubjectXGBPipeline(
            subject_id=subj,
            y_train=y_train_full[subj].values.astype(int),
            y_test=y_test_full[subj].values.astype(int),
            numerical_features=num_feats,
            categorical_features=cat_feats,
            max_depth=params.get("max_depth", 4),
            n_estimators=params.get("n_estimators", 200),
            learning_rate=params.get("learning_rate", 0.1),
            random_state=seed,
        )
        manager.add_model(subj, pipeline)

    manager.fit(subjects, X_train)
    results = manager.evaluate(X_test)

    course_names, mae_list, prec_list, rec_list, f1_list = [], [], [], [], []
    for subj in subjects:
        if subj not in results:
            continue
        r, p, f = results[subj]
        pipeline = manager.models[subj]
        y_pred = pipeline.predict(X_test)
        y_true = pipeline.y_test
        mae = abs(int(y_pred.sum()) - int(y_true.sum()))
        course_names.append(subj)
        mae_list.append(float(mae))
        prec_list.append(float(p))
        rec_list.append(float(r))
        f1_list.append(float(f))

    per_course = _build_unified_per_course(
        course_names,
        mae_values=mae_list,
        precision_values=prec_list,
        recall_values=rec_list,
        f1_values=f1_list,
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "xgboost", transform, params, seed,
        train_samples=len(X_train),
        test_samples=len(X_test),
        split_info=f"random split, seed={seed}",
    )
    metadata["_trainer"] = manager
    return metrics, per_course, metadata


def run_course2vec_mlp(
    university_data: dict,
    course_ids: List[str],
    course_to_idx: Dict[str, int],
    params: dict,
    seed: int = RANDOM_SEED,
) -> Tuple[Dict[str, float], pd.DataFrame, dict]:
    """Run Course2Vec MLP: flattened multi-hot windows + skip-gram embeddings."""
    from educast.models.course2vec_mlp import Course2VecMLPTrainer, train_course_embeddings

    window_size = params.get("window_size", MICRO_WINDOW_SIZE)
    embedding_dim = params.get("embedding_dim", 64)

    X_all, y_all, meta_all = build_student_dataset(
        university_data, course_to_idx, window_size
    )

    emb_matrix = train_course_embeddings(
        university_data, course_to_idx, embedding_dim=embedding_dim, seed=seed,
    )
    mean_embedding = emb_matrix.mean(axis=0)

    n_samples = len(X_all)
    X_flat = X_all.reshape(n_samples, -1)
    emb_tile = np.tile(mean_embedding, (n_samples, 1))
    X_combined = np.hstack([X_flat, emb_tile])

    X_train, y_train, meta_train, X_test, y_test, meta_test = split_by_year(
        X_combined, y_all, meta_all, SPLIT_YEAR
    )

    trainer = Course2VecMLPTrainer(
        input_dim=X_combined.shape[1],
        epochs=params.get("epochs", 100),
        batch_size=params.get("batch_size", 64),
        seed=seed,
    )
    trainer.fit(X_train, y_train)

    pred_probs = trainer.predict(X_test)
    student_agg: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(NUM_COURSES))
    actual_agg: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(NUM_COURSES))

    for i, (year, term, sid) in enumerate(meta_test):
        term_key = f"{year}-{term:02d}"
        student_agg[term_key] += pred_probs[i]
        actual_agg[term_key] += y_test[i]

    terms = sorted(student_agg.keys())
    predictions = np.array([student_agg[t] for t in terms])
    actuals = np.array([actual_agg[t] for t in terms])

    idx_to_course = {i: cid for i, cid in enumerate(course_ids)}
    mae_df = per_course_mae(actuals, predictions, idx_to_course)

    binary_preds = (pred_probs > 0.5).astype(int)
    prec_list, rec_list, f1_list = [], [], []
    for c_idx in range(NUM_COURSES):
        y_true_c = y_test[:, c_idx]
        y_pred_c = binary_preds[:, c_idx]
        prec_list.append(float(sk_precision(y_true_c, y_pred_c, zero_division=0)))
        rec_list.append(float(sk_recall(y_true_c, y_pred_c, zero_division=0)))
        f1_list.append(float(sk_f1(y_true_c, y_pred_c, zero_division=0)))

    per_course = _build_unified_per_course(
        mae_df["Course"].tolist(),
        mae_values=mae_df["MAE"].tolist(),
        mae_pos_values=mae_df["MAE+"].tolist(),
        mae_neg_values=mae_df["MAE-"].tolist(),
        precision_values=prec_list,
        recall_values=rec_list,
        f1_values=f1_list,
    )
    metrics = _build_unified_metrics(per_course)
    metadata = build_experiment_metadata(
        "course2vec_mlp", "multihot_flat", params, seed,
        train_samples=len(X_train),
        test_samples=len(X_test),
        split_info=f"year >= {SPLIT_YEAR}",
    )
    metadata["_trainer"] = trainer
    return metrics, per_course, metadata


RUNNERS = {
    "naive": run_naive,
    "lstm_micro": run_micro_lstm,
    "lstm_macro": run_macro_lstm,
    "decision_tree": run_decision_tree,
    "random_forest": run_random_forest,
    "xgboost": run_xgboost,
    "course2vec_mlp": run_course2vec_mlp,
}


def run_experiment(
    name: str,
    seed: int = RANDOM_SEED,
    save_results: bool = True,
) -> Tuple[Dict[str, float], pd.DataFrame]:
    config = get_experiment(name)
    model_type = config["model"]

    if model_type not in RUNNERS:
        raise NotImplementedError(
            f"Runner for model '{model_type}' not implemented. "
            f"Available: {list(RUNNERS.keys())}"
        )

    university_data = load_university_json()
    course_ids, course_to_idx, idx_to_course = build_course_vocabulary(university_data)

    runner = RUNNERS[model_type]
    kwargs = {}
    if model_type in ("decision_tree", "random_forest", "xgboost"):
        kwargs["transform"] = config["transform"]
    metrics, per_course, metadata = runner(
        university_data, course_ids, course_to_idx, config["params"], seed, **kwargs
    )

    trainer = metadata.pop("_trainer", None)

    print(f"\n{'=' * 50}")
    print(f"Experiment: {name}")
    print(f"Model: {model_type}")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
    print(f"{'=' * 50}\n")

    if save_results:
        json_path, csv_path = export_results(
            name, metrics, per_course, metadata
        )
        print(f"Results saved to:")
        print(f"  JSON: {json_path}")
        print(f"  CSV:  {csv_path}")

    return metrics, per_course, trainer


def run_all_experiments(
    seed: int = RANDOM_SEED,
    save_results: bool = True,
    experiments: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """Run all (or selected) experiments. Returns dict mapping experiment name to metrics."""
    all_metrics = {}
    exp_names = experiments or list(EXPERIMENTS.keys())

    for name in exp_names:
        try:
            metrics, _, _ = run_experiment(name, seed, save_results)
            all_metrics[name] = metrics
        except Exception as e:
            print(f"ERROR running {name}: {e}")
            all_metrics[name] = {"error": str(e)}

    return all_metrics


def main() -> None:
    """CLI entry point for running experiments."""
    parser = argparse.ArgumentParser(description="EduCast Experiment Runner")
    parser.add_argument(
        "--experiment", "-e",
        type=str,
        default="all",
        help="Experiment name or 'all' to run everything",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed (default: {RANDOM_SEED})",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to disk",
    )

    args = parser.parse_args()

    if args.experiment == "all":
        run_all_experiments(seed=args.seed, save_results=not args.no_save)
    else:
        run_experiment(args.experiment, seed=args.seed, save_results=not args.no_save)


if __name__ == "__main__":
    main()
