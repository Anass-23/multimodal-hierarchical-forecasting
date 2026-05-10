"""Service layer: data loading, manifest validation, transforms."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from educast.data.loader import (
    build_acronym_maps,
    build_course_label_map,
    build_course_vocabulary,
    load_university_json,
)
from educast.data.transforms import create_macro_dataset
from educast.features.multihot import build_student_dataset
from educast.server.services.app_state import state



REQUIRED_MANIFEST_KEYS = {"version", "university", "files", "schema", "settings"}


def validate_manifest(manifest: dict) -> List[str]:
    """Return list of validation errors (empty = OK)."""
    errors: List[str] = []
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            errors.append(f"Missing required key: {key}")

    files = manifest.get("files", {})
    if "enrollments" not in files:
        errors.append("files.enrollments is required")
    if "courses" not in files:
        errors.append("files.courses is required")

    schema = manifest.get("schema", {})
    if "enrollments" not in schema:
        errors.append("schema.enrollments is required")
    if "courses" not in schema:
        errors.append("schema.courses is required")

    return errors


def load_manifest(data_dir: Path) -> Tuple[dict, List[str]]:
    """Load and validate educast.yaml from a data directory."""
    manifest_path = data_dir / "educast.yaml"
    if not manifest_path.exists():
        manifest_path = data_dir / "educast.yml"
    if not manifest_path.exists():
        return {}, ["educast.yaml not found in data directory"]

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    errors = validate_manifest(manifest)
    return manifest, errors



def load_data_from_manifest(data_dir: Path) -> Dict[str, Any]:
    """Load university data from a standardized educast.yaml folder.

    Returns summary dict with stats.
    """
    manifest, errors = load_manifest(data_dir)
    if errors:
        return {"ok": False, "errors": errors}

    state.manifest = manifest
    state.data_dir = data_dir

    files_cfg = manifest["files"]
    schema_cfg = manifest["schema"]

    enrollments_path = data_dir / files_cfg["enrollments"]
    courses_path = data_dir / files_cfg["courses"]

    if not enrollments_path.exists():
        return {"ok": False, "errors": [f"Enrollments file not found: {enrollments_path}"]}
    if not courses_path.exists():
        return {"ok": False, "errors": [f"Courses file not found: {courses_path}"]}

    # For now, store raw DataFrames; transforms happen per-model
    state.data_loaded = True
    return {"ok": True, "errors": [], "manifest": manifest}


def load_data_legacy() -> Dict[str, Any]:
    """Load data using the built-in educast paths (EPSEM data).

    This is the default mode for EPSEM-UPC data already on disk.
    """
    try:
        university_data = load_university_json()
        state.university_data = university_data

        course_ids, course_to_idx, idx_to_course = build_course_vocabulary(university_data)
        state.course_ids = course_ids
        state.course_to_idx = course_to_idx
        state.idx_to_course = idx_to_course
        state.course_label_map = build_course_label_map(university_data, idx_to_course)

        # Derive acronym maps from enriched JSON (no CSV needed)
        id_to_acr, acr_to_id, _ = build_acronym_maps(university_data)
        # Convert string course_id keys to int keys for backward compat
        state.id_to_acronym = {int(k) if k.isdigit() else k: v for k, v in id_to_acr.items()}
        state.acronym_to_id = {v: int(k) if k.isdigit() else k for k, v in id_to_acr.items()}
        name_map: Dict[str, str] = {}
        for dept in university_data.get("departments", []):
            for course in dept.get("courses", []):
                acr = course.get("acronym")
                name = course.get("name")
                if acr and name:
                    name_map[acr] = name
        state.subject_names = name_map

        df_macro = create_macro_dataset(university_data, course_ids)
        state.df_macro = df_macro

        X_all, y_all, meta_all = build_student_dataset(university_data, course_to_idx)
        state.X_all = X_all
        state.y_all = y_all
        state.meta_all = meta_all

        state.data_loaded = True
        return {
            "ok": True,
            "errors": [],
            "n_students": len(state.get_student_ids()),
            "n_courses": len(course_ids),
            "n_terms": len(df_macro),
            "n_enrollment_records": int(X_all.shape[0]) if X_all is not None else 0,
            "terms": list(df_macro.index),
        }
    except Exception as e:
        return {"ok": False, "errors": [str(e)]}



def _group_attempts_by_semester(attempts: List) -> Dict[str, List[dict]]:
    """Group a flat list of attempt records into {term_key: [records]}."""
    semesters: Dict[str, List[dict]] = {}
    for a in attempts:
        year = a.get("year", 0)
        term = a.get("term", 1)
        key = f"{year}-{term:02d}"
        semesters.setdefault(key, []).append(a)
    return dict(sorted(semesters.items()))


def get_student_list() -> List[Dict[str, Any]]:
    """Return lightweight list of all students with basic info."""
    if state.university_data is None:
        return []

    students = state.university_data.get("students", [])
    if isinstance(students, dict):
        students = [{"student_id": k, **v} for k, v in students.items()]

    result = []
    for sdata in sorted(students, key=lambda s: s.get("student_id", "")):
        sid = sdata.get("student_id", "")
        attempts = sdata.get("history", {}).get("attempts", [])
        semesters = _group_attempts_by_semester(attempts)
        courses_taken = {a.get("course", {}).get("course_id", "") for a in attempts}

        result.append({
            "id": sid,
            "n_semesters": len(semesters),
            "n_courses_taken": len(courses_taken),
            "first_term": min(semesters.keys()) if semesters else None,
            "last_term": max(semesters.keys()) if semesters else None,
        })
    return result


def get_student_history(student_id: str) -> Optional[Dict[str, Any]]:
    """Return full enrollment history for a single student.

    Adapted for the real JSON schema where students is a list and
    history.attempts is a flat list of enrollment records.
    """
    student = state.get_student(student_id)
    if student is None:
        return None

    attempts = student.get("history", {}).get("attempts", [])
    semesters_grouped = _group_attempts_by_semester(attempts)
    terms_sorted = sorted(semesters_grouped.keys())
    all_course_ids = state.course_ids

    # Build heatmap matrices (courses x terms)
    n_courses = len(all_course_ids)
    n_terms = len(terms_sorted)
    enrollment_matrix = np.zeros((n_courses, n_terms))
    grade_matrix = np.full((n_courses, n_terms), np.nan)
    attempt_matrix = np.zeros((n_courses, n_terms))

    # Track cumulative attempts per course
    cumulative_attempts: Dict[str, int] = {}

    semester_details = []
    for t_idx, term in enumerate(terms_sorted):
        courses_in_term = []
        for record in semesters_grouped[term]:
            course_info = record.get("course", {})
            cid = course_info.get("course_id", "")
            if cid in state.course_to_idx:
                c_idx = state.course_to_idx[cid]
                enrollment_matrix[c_idx, t_idx] = 1
                grade = record.get("grade")
                if grade is not None:
                    try:
                        grade_matrix[c_idx, t_idx] = float(grade)
                    except (ValueError, TypeError):
                        pass
                cumulative_attempts[cid] = cumulative_attempts.get(cid, 0) + 1
                attempt_matrix[c_idx, t_idx] = cumulative_attempts[cid]

                acronym = state.course_label_map.get(c_idx, cid)
                courses_in_term.append({
                    "course_id": cid,
                    "acronym": acronym,
                    "grade": grade,
                    "attempt": cumulative_attempts[cid],
                })
        semester_details.append({"term": term, "courses": courses_in_term})

    # Course labels
    course_labels = [state.course_label_map.get(i, cid) for i, cid in enumerate(all_course_ids)]

    return {
        "student_id": student_id,
        "semesters": semester_details,
        "heatmap_data": {
            "courses": course_labels,
            "course_ids": all_course_ids,
            "terms": terms_sorted,
            "enrollment": enrollment_matrix.tolist(),
            "grades": np.where(np.isnan(grade_matrix), None, grade_matrix).tolist(),
            "attempts": attempt_matrix.tolist(),
        },
    }


def get_courses_summary() -> List[Dict[str, Any]]:
    """Return summary of all courses with enrollment trends."""
    if state.df_macro is None:
        return []

    result = []
    for i, cid in enumerate(state.course_ids):
        acronym = state.course_label_map.get(i, cid)
        enrollment_series = state.df_macro[cid].tolist() if cid in state.df_macro.columns else []
        full_name = state.subject_names.get(acronym, acronym)
        result.append({
            "course_id": cid,
            "acronym": acronym,
            "name": full_name,
            "enrollment_by_term": enrollment_series,
            "terms": list(state.df_macro.index),
            "total_enrollments": int(sum(enrollment_series)),
            "avg_enrollment": round(float(np.mean(enrollment_series)), 2) if enrollment_series else 0,
        })
    return result
