"""Tests for feature transforms and windowing."""

import numpy as np
import pytest

from educast.data.cleaning import fill_missing_values, filter_inactive_courses
from educast.features.multihot import (
    build_macro_windows,
    get_empty_student_vector,
    process_student_history,
)
from educast.config import FEAT_DIM_STUDENT, NUM_COURSES


class TestEmptyStudentVector:
    def test_shape(self):
        vec = get_empty_student_vector()
        assert vec.shape == (FEAT_DIM_STUDENT,)

    def test_enrollment_zeros(self):
        vec = get_empty_student_vector()
        assert np.all(vec[:NUM_COURSES] == 0.0)

    def test_grades_minus_one(self):
        vec = get_empty_student_vector()
        assert np.all(vec[NUM_COURSES: NUM_COURSES * 2] == -1.0)

    def test_attempts_zeros(self):
        vec = get_empty_student_vector()
        assert np.all(vec[NUM_COURSES * 2: NUM_COURSES * 3] == 0.0)


class TestProcessStudentHistory:
    def _make_student(self, n_terms: int = 4) -> dict:
        courses = [{"course_id": f"C{i:03d}", "name": f"Course {i}"} for i in range(3)]
        attempts = []
        for t in range(n_terms):
            for c in courses[:2]:
                attempts.append({
                    "course": c,
                    "year": 2020 + t // 2,
                    "term": (t % 2) + 1,
                    "grade": 5.0 + t,
                })
        return {"student_id": "S001", "history": {"attempts": attempts}}

    def _make_course_map(self, n: int = 3) -> dict:
        return {f"C{i:03d}": i for i in range(n)}

    def test_returns_sequences(self):
        student = self._make_student(4)
        c2i = self._make_course_map()
        X, y, meta = process_student_history(student, c2i, window_size=2)
        assert len(X) > 0
        assert len(X) == len(y) == len(meta)

    def test_target_shape(self):
        student = self._make_student(4)
        c2i = self._make_course_map()
        X, y, meta = process_student_history(student, c2i, window_size=2)
        assert y[0].shape == (NUM_COURSES,)

    def test_too_few_terms(self):
        student = self._make_student(1)
        c2i = self._make_course_map()
        X, y, meta = process_student_history(student, c2i, window_size=3)
        assert len(X) == 0


class TestBuildMacroWindows:
    def test_window_shapes(self):
        data = np.random.randn(10, 51)
        targets = np.random.randn(10, 51)
        terms = [f"2020-{i:02d}" for i in range(10)]
        X, y, meta = build_macro_windows(data, targets, terms, window_size=3)
        assert X.shape[0] == 9  # 10 - 1
        assert X.shape[1] == 3
        assert X.shape[2] == 51
        assert y.shape == (9, 51)

    def test_meta_length(self):
        data = np.random.randn(5, 10)
        targets = np.random.randn(5, 10)
        terms = [f"2020-{i:02d}" for i in range(5)]
        X, y, meta = build_macro_windows(data, targets, terms, window_size=2)
        assert len(meta) == len(X)


class TestFilterInactiveCourses:
    def test_filters_zeros(self):
        enrollment = np.array([[1, 0, 1], [0, 0, 1]])
        target = np.array([0, 0, 1])
        mask = filter_inactive_courses(enrollment, target)
        assert mask.tolist() == [True, False, True]

    def test_all_active(self):
        enrollment = np.ones((3, 4))
        target = np.ones(4)
        mask = filter_inactive_courses(enrollment, target)
        assert all(mask)
