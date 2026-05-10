"""Tests for data loading and vocabulary building."""

import numpy as np
import pytest

from educast.config import NUM_COURSES
from educast.data.loader import build_course_vocabulary


def _make_university_data(n_courses: int = 5) -> dict:
    """Create minimal university data for testing."""
    courses = [
        {"course_id": f"C{i:03d}", "name": f"Course {i}", "credits": 6.0}
        for i in range(n_courses)
    ]
    return {
        "university_id": "TEST",
        "name": "Test University",
        "departments": [{"department_id": "D1", "name": "Dept 1", "courses": courses}],
        "programmes": [],
        "students": [
            {
                "student_id": "S001",
                "history": {
                    "attempts": [
                        {
                            "course": courses[0],
                            "year": 2020,
                            "term": 1,
                            "grade": 7.5,
                        },
                        {
                            "course": courses[1],
                            "year": 2020,
                            "term": 1,
                            "grade": 5.0,
                        },
                        {
                            "course": courses[2],
                            "year": 2020,
                            "term": 2,
                            "grade": 8.0,
                        },
                    ],
                },
            },
        ],
    }


class TestBuildCourseVocabulary:
    def test_returns_sorted_ids(self):
        data = _make_university_data(5)
        ids, c2i, i2c = build_course_vocabulary(data)
        assert ids == sorted(ids)
        assert len(ids) == 5

    def test_mappings_are_consistent(self):
        data = _make_university_data(3)
        ids, c2i, i2c = build_course_vocabulary(data)
        for i, cid in enumerate(ids):
            assert c2i[cid] == i
            assert i2c[i] == cid

    def test_empty_departments(self):
        data = {"departments": [], "students": []}
        ids, c2i, i2c = build_course_vocabulary(data)
        assert len(ids) == 0
