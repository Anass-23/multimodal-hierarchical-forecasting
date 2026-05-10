"""Data transformations: TFG tabular transforms and TFM sequential 153-dim transform."""

from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from educast.config import NUM_COURSES


def build_tabular_from_json(
    university_data: dict,
    id_to_acr: Dict[str, str],
    max_quads: int = 10,
) -> pd.DataFrame:
    """Build wide-format tabular DataFrame from enriched *.educast.json.

    Each row is a snapshot of a student at enrollment period *i*, with
    cumulative columns ``{j}:{acr}.m`` (enrolled) and ``{j}:{acr}.n`` (grade)
    for j in 0..i. Compatible with ``primera_transformacio`` and ``segona_transformacio``.
    """
    acr_list = sorted(set(id_to_acr.values()))
    all_rows: List[Dict] = []

    for student in tqdm(university_data.get("students", []), desc="Building tabular dataset"):
        history = student.get("history", {})
        attempts = history.get("attempts", [])
        if not attempts:
            continue

        # Group attempts by (year, term)
        quad_groups: Dict[tuple, list] = defaultdict(list)
        for att in attempts:
            year = att.get("year")
            term = att.get("term")
            if year and term:
                quad_groups[(year, term)].append(att)

        sorted_quads = sorted(quad_groups.keys())
        num_quads = len(sorted_quads)
        if num_quads < 2:
            continue  # Need at least 2 periods for features + label

        # Student-level metadata
        first_year = sorted_quads[0][0]
        birth_year = student.get("birth_year")
        anyn = birth_year if birth_year else (first_year - 18)
        edat_raw = first_year - anyn
        edat = 0 if 18 <= edat_raw <= 20 else (1 if 21 <= edat_raw <= 24 else 2)

        cols: Dict[str, Any] = {
            "EXPID": student["student_id"],
            "EDAT": edat,
            "VIA": student.get("access_path"),
            "ORDRE": student.get("enrollment_order"),
            "NACC": student.get("access_grade"),
        }

        for i in range(min(max_quads, num_quads)):
            q = sorted_quads[i]
            quad_attempts = quad_groups[q]

            # Scholarship: any attempt in this quad had scholarship
            cols[f"{i}:becat"] = any(
                att.get("scholarship", False) for att in quad_attempts
            )

            # Initialize all subjects as not enrolled
            for acr in acr_list:
                cols[f"{i}:{acr}.m"] = False
                cols[f"{i}:{acr}.n"] = 0.0

            # Fill in actual enrollments
            for att in quad_attempts:
                cid = att.get("course", {}).get("course_id")
                acr = id_to_acr.get(cid)
                if acr is None:
                    continue
                grade = att.get("grade")
                if grade is not None:
                    cols[f"{i}:{acr}.m"] = True
                    cols[f"{i}:{acr}.n"] = grade

            all_rows.append(dict(cols))  # snapshot at quad i

    return pd.DataFrame(all_rows)


def primera_transformacio(
    raw_df: pd.DataFrame,
    acronym_list: List[str],
) -> pd.DataFrame:
    """Transform 1: enrollment history as binary features.

    Creates binary target columns indicating which subjects the student
    will enroll in next. Students with only one enrollment period are dropped.
    """
    num_acr = len(acronym_list)
    dataset = raw_df.copy(deep=True)

    for acr in acronym_list:
        if acr:
            dataset[acr] = False

    indx = 0
    indexes_to_delete = []

    for expid in tqdm(raw_df["EXPID"].unique(), desc="Building dataset (Transform 1)"):
        num_mat = len(raw_df[raw_df["EXPID"] == expid])

        if num_mat == 1:
            indexes_to_delete.append(indx)
            indx += 1
        else:
            for mat in range(num_mat):
                if mat == 0:
                    r = raw_df[raw_df["EXPID"] == expid].loc[
                        indx:indx,
                        raw_df.columns.str.startswith(f"{mat}:"),
                    ]
                    # Just read current enrollment, set labels later
                elif mat > 0:
                    r = raw_df[raw_df["EXPID"] == expid].loc[
                        indx:indx,
                        raw_df.columns.str.startswith(f"{mat}:"),
                    ]
                    next_assigs = [
                        acr.split(":")[1].strip(".m")
                        for acr, v in r.loc[
                            indx, r.columns.str.endswith(".m")
                        ].to_dict().items()
                        if v
                    ]

                    mapping = dataset.iloc[indx - 1, -num_acr:].to_dict()
                    for k in mapping:
                        mapping[k] = False
                    for assig in next_assigs:
                        mapping[assig] = True
                    dataset.loc[indx - 1, dataset.columns[-num_acr:]] = list(
                        mapping.values()
                    )

                    if mat == num_mat - 1:
                        indexes_to_delete.append(indx)
                indx += 1

    dataset = dataset.drop(indexes_to_delete)

    # Row-level .loc assignments upcast bool columns to object dtype in pandas.
    # Multi-column setitem is unreliable for dtype changes in pandas 2.x (CoW).
    # Assign column-by-column to guarantee each target column is numpy bool.
    for col in dataset.columns[-num_acr:]:
        dataset[col] = dataset[col].fillna(False).astype(bool)

    return dataset


def segona_transformacio(
    raw_df: pd.DataFrame,
    acronym_list: List[str],
) -> pd.DataFrame:
    """Transform 2: enrollment history with attempts, grades, and marks.

    Extends Transform 1 by adding per-subject history columns:
    ``{acr}.da`` (attempt count), ``{acr}.n`` (grade), ``{acr}.m`` (enrolled).
    Uses forward-fill to propagate student history across enrollment periods.
    """
    num_acr = len(acronym_list)
    columns = ["EXPID", "EDAT", "VIA", "ORDRE", "NACC", "BECAT"]

    for acr in acronym_list:
        if acr:
            columns.extend([f"{acr}.da", f"{acr}.n", f"{acr}.m"])
    for acr in acronym_list:
        if acr:
            columns.append(acr)

    dataset = pd.DataFrame(columns=columns, data=[])
    for col in columns[:5]:
        dataset[col] = raw_df[col]

    indx = 0
    indexes_to_delete = []

    for expid in tqdm(raw_df["EXPID"].unique(), desc="Building dataset (Transform 2)"):
        num_mat = len(raw_df[raw_df["EXPID"] == expid])
        assig_hist: Dict[str, list] = {}

        if num_mat == 1:
            indexes_to_delete.append(indx)
            indx += 1
        else:
            for mat in range(num_mat):
                r = raw_df[raw_df["EXPID"] == expid].loc[
                    indx:indx,
                    raw_df.columns.str.startswith(f"{mat}:"),
                ]
                notes_assigs = [
                    (acr.split(":")[1].strip(".n"), v)
                    for acr, v in r.loc[
                        indx, r.columns.str.endswith(".n")
                    ].to_dict().items()
                    if v
                ]
                dataset.at[indx, "BECAT"] = r.at[indx, f"{mat}:becat"]

                for acr, v in notes_assigs:
                    if acr in assig_hist:
                        assig_hist[acr].append(v)
                    else:
                        assig_hist[acr] = [v]
                    dataset.at[indx, f"{acr}.da"] = len(assig_hist[acr])
                    dataset.at[indx, f"{acr}.n"] = v
                    dataset.at[indx, f"{acr}.m"] = True

                if mat > 0:
                    next_assigs = [
                        acr.split(":")[1].strip(".m")
                        for acr, v in r.loc[
                            indx, r.columns.str.endswith(".m")
                        ].to_dict().items()
                        if v
                    ]
                    mapping = dataset.iloc[indx - 1, -num_acr:].to_dict()
                    for k in mapping:
                        mapping[k] = False
                    for assig in next_assigs:
                        mapping[assig] = True
                    dataset.loc[indx - 1, dataset.columns[-num_acr:]] = list(
                        mapping.values()
                    )

                    if mat == num_mat - 1:
                        indexes_to_delete.append(indx)
                indx += 1

    dataset = dataset.drop(indexes_to_delete)

    # Ensure target columns (last num_acr) are bool, not object/NaN
    target_cols = [c for c in dataset.columns[-num_acr:]]
    dataset[target_cols] = dataset[target_cols].fillna(False).astype(bool)

    # Forward-fill student history
    m_cols = [c for c in dataset.columns if c.endswith(".m")]
    dataset[m_cols] = dataset[m_cols].fillna(False)
    dataset = dataset.ffill()

    da_cols = [c for c in dataset.columns if c.endswith(".da")]
    dataset[da_cols] = dataset[da_cols].fillna(0)
    n_cols = [c for c in dataset.columns if c.endswith(".n")]
    dataset[n_cols] = dataset[n_cols].fillna(0.0)

    return dataset


def create_macro_dataset(
    university_data: dict,
    course_ids: List[str],
) -> pd.DataFrame:
    """Aggregate student enrollments into a global timeline.

    Returns a DataFrame indexed by term string, columns are course IDs,
    values are enrollment counts.
    """
    records = []
    for student in university_data.get("students", []):
        history = student.get("history", {})
        for attempt in history.get("attempts", []):
            year = attempt.get("year")
            term = attempt.get("term")
            if year and term:
                records.append({
                    "Term": f"{year}-{term:02d}",
                    "CourseID": attempt["course"]["course_id"],
                })

    df = pd.DataFrame(records)
    df_pivot = df.pivot_table(
        index="Term", columns="CourseID", aggfunc="size", fill_value=0
    )
    df_pivot = df_pivot.reindex(columns=course_ids, fill_value=0)
    return df_pivot


def create_macro_extended_dataset(
    university_data: dict,
    course_ids: List[str],
) -> pd.DataFrame:
    """Create macro dataset with extended metrics per course: Count_{cid}, Grade_{cid}, Passed_{cid}, Failed_{cid}."""
    records = []
    for student in university_data.get("students", []):
        history = student.get("history", {})
        for attempt in history.get("attempts", []):
            year = attempt.get("year")
            term = attempt.get("term")
            if year and term:
                grade = attempt.get("grade")
                records.append({
                    "Term": f"{year}-{term:02d}",
                    "CourseID": attempt["course"]["course_id"],
                    "Count": 1,
                    "Grade": grade if grade is not None else 0.0,
                    "Passed": 1 if (grade is not None and grade >= 5.0) else 0,
                    "Failed": 1 if (grade is not None and grade < 5.0) else 0,
                })

    df = pd.DataFrame(records)
    df_agg = df.groupby(["Term", "CourseID"]).agg({
        "Count": "sum", "Grade": "mean", "Passed": "sum", "Failed": "sum",
    }).unstack(fill_value=0)

    metrics = ["Count", "Grade", "Passed", "Failed"]
    full_cols = pd.MultiIndex.from_product(
        [metrics, course_ids], names=["Metric", "CourseID"]
    )
    df_agg = df_agg.reindex(columns=full_cols, fill_value=0)
    df_agg.columns = [f"{m}_{c}" for m, c in df_agg.columns]
    return df_agg
