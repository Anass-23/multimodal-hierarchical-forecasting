"""153-dim multi-hot vector builder (enrollment + grade + attempts) for LSTM models."""

from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np

from educast.config import FEAT_DIM_STUDENT, MICRO_WINDOW_SIZE, NUM_COURSES


def get_empty_student_vector() -> np.ndarray:
    """Create an empty student feature vector.

    Layout (154 dims):
      [0:51]     - Enrollment flags (0/1)
      [51:102]   - Normalized grades (0-1, -1 = not taken)
      [102:153]  - Normalized attempt counts (0-1, capped at 5)
      [153]      - Cumulative GPA (0-1)
    """
    vec = np.zeros(FEAT_DIM_STUDENT)
    vec[NUM_COURSES: NUM_COURSES * 2] = -1.0  # Default grade = not taken
    return vec


def process_student_history(
    student_data: dict,
    course_to_idx: Dict[str, int],
    window_size: int = MICRO_WINDOW_SIZE,
) -> Tuple[List[np.ndarray], List[np.ndarray], List[tuple]]:
    """Convert a student's academic history into LSTM input sequences.

    Groups attempts by (year, term), builds 154-dim feature vectors per term,
    then creates sliding window sequences.
    Returns (X_sequences, y_targets, metadata) where X is (window_size, 154),
    y is (51,) enrollment flags, meta is (year, term, student_id).
    """
    history = student_data.get("history", {})
    attempts = history.get("attempts", [])
    student_id = student_data.get("student_id", "unknown")

    history_map: Dict[tuple, list] = defaultdict(list)
    for attempt in attempts:
        year = attempt.get("year")
        term = attempt.get("term")
        if year and term:
            history_map[(year, term)].append(attempt)

    sorted_terms = sorted(history_map.keys())
    if len(sorted_terms) < 2:
        return [], [], []

    real_vectors = []
    course_counters: Dict[int, int] = defaultdict(int)
    cum_grades_sum = 0.0
    cum_courses_taken = 0

    for year, term in sorted_terms:
        vec = get_empty_student_vector()
        term_grades = []

        for att in history_map[(year, term)]:
            cid = att["course"]["course_id"]
            if cid not in course_to_idx:
                continue
            idx = course_to_idx[cid]

            # Enrollment flag
            vec[idx] = 1.0

            # Grade (normalized to 0-1); leave default -1.0 if not yet graded
            grade = att.get("grade")
            if grade is not None:
                vec[NUM_COURSES + idx] = grade / 10.0
                term_grades.append(grade)

            # Attempt count (normalized, capped at 5)
            course_counters[idx] += 1
            vec[NUM_COURSES * 2 + idx] = min(course_counters[idx] / 5.0, 1.0)

        # Cumulative GPA
        if term_grades:
            cum_grades_sum += sum(term_grades)
            cum_courses_taken += len(term_grades)
        vec[-1] = (cum_grades_sum / cum_courses_taken / 10.0) if cum_courses_taken > 0 else 0.0

        real_vectors.append(vec)

    X, y, meta = [], [], []
    for i in range(1, len(real_vectors)):
        y_target = real_vectors[i][:NUM_COURSES]
        hist = real_vectors[:i]

        if len(hist) < window_size:
            pad_needed = window_size - len(hist)
            pad = [get_empty_student_vector()] * pad_needed
            X_win = np.array(pad + hist)
        else:
            X_win = np.array(hist[-window_size:])

        X.append(X_win)
        y.append(y_target)
        meta.append(sorted_terms[i] + (student_id,))

    return X, y, meta


def build_student_dataset(
    university_data: dict,
    course_to_idx: Dict[str, int],
    window_size: int = MICRO_WINDOW_SIZE,
) -> Tuple[np.ndarray, np.ndarray, List[tuple]]:
    """Process all students into LSTM-ready dataset. Returns (X_all, y_all, meta_all)."""
    X_all, y_all, meta_all = [], [], []
    for student in university_data.get("students", []):
        x, y, m = process_student_history(student, course_to_idx, window_size)
        X_all.extend(x)
        y_all.extend(y)
        meta_all.extend(m)

    return np.array(X_all), np.array(y_all), meta_all


def build_macro_windows(
    scaled_data: np.ndarray,
    scaled_targets: np.ndarray,
    terms: List[str],
    window_size: int,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Create sliding windows from scaled macro time series. Returns (X, y, meta)."""
    X, y, meta = [], [], []
    empty_vec = np.zeros(scaled_data.shape[1])

    for target_idx in range(1, len(scaled_data)):
        y_target = scaled_targets[target_idx]
        raw_history = scaled_data[:target_idx]

        if len(raw_history) < window_size:
            pad_needed = window_size - len(raw_history)
            padding = [empty_vec] * pad_needed
            X_win = np.array(padding + list(raw_history))
        else:
            X_win = raw_history[-window_size:]

        X.append(X_win)
        y.append(y_target)
        meta.append(terms[target_idx])

    return np.array(X), np.array(y), meta
