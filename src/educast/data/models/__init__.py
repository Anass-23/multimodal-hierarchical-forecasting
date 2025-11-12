from __future__ import annotations

from .clickstream import ClickstreamData
from .course import AttemptedCourse, Course
from .organization import Department, Programme, TermType, University
from .student import AcademicHistory, Student

__version__ = "0.1.0"

__all__ = [
    "ClickstreamData",
    "Course",
    "AttemptedCourse",
    "Student",
    "AcademicHistory",
    "Programme",
    "Department",
    "University",
    "TermType",
]
