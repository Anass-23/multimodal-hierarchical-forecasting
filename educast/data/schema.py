"""Canonical Pydantic schema for the *.educast.json format.

All university data (departments, courses, students, enrollment history,
and student metadata) is captured in these models. This is the single
source of truth for the educast data format.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field


class ClickstreamData(BaseModel):
    """User interaction/activity log entry."""

    id: int = Field(..., description="Unique event identifier")
    eventname: str = Field(..., description="Type of event that occurred")
    timestamp: datetime = Field(..., description="Event datetime")
    action: Optional[str] = Field(None, description="Action type performed")
    target: Optional[str] = Field(None, description="Target resource of the action")
    ip: Optional[str] = Field(None, description="IP address of the user")


class Course(BaseModel):
    """A course that can be taken by students."""

    course_id: str = Field(..., description="Unique course identifier")
    name: Optional[str] = Field(None, description="Course name")
    acronym: Optional[str] = Field(None, description="Short acronym (e.g. 'MBE')")
    credits: float = Field(
        0.0, description="Credits awarded for completing the course", ge=0.0
    )


class AttemptedCourse(BaseModel):
    """A student's attempt at a specific course in a given term."""

    course: Course = Field(..., description="Course being attempted")
    year: Optional[int] = Field(None, description="Academic year")
    term: Optional[int] = Field(None, description="Academic term (1 or 2)")
    semester: Optional[int] = Field(None, description="Cumulative semester number")
    timestamp: Optional[datetime] = Field(None, description="Enrollment date")
    grade: Optional[float] = Field(None, description="Grade received (0-10 scale)")
    clickstream: List[ClickstreamData] = Field(
        default_factory=list, description="Activity logs for this course"
    )
    # Enriched fields (from raw CSV metadata)
    scholarship: Optional[bool] = Field(None, description="Had scholarship this term")
    grade_description: Optional[str] = Field(
        None, description="Grade descriptor (e.g. 'N', 'A', 'E', 'MH')"
    )
    grade_type: Optional[str] = Field(None, description="Grading type")

    @computed_field  # type: ignore[misc]
    @property
    def passed(self) -> Optional[bool]:
        """Whether the student passed (grade >= 5.0). None if ungraded."""
        return self.grade >= 5.0 if self.grade is not None else None


class AcademicHistory(BaseModel):
    """Student's complete academic transcript."""

    attempts: List[AttemptedCourse] = Field(
        default_factory=list, description="List of course attempts"
    )

    def add_attempt(self, attempted_course: AttemptedCourse) -> None:
        self.attempts.append(attempted_course)

    def __len__(self) -> int:
        return len(self.attempts)

    @computed_field  # type: ignore[misc]
    @property
    def total_credits(self) -> float:
        """Total credits earned from passed courses."""
        return sum(
            attempt.course.credits for attempt in self.attempts if attempt.passed
        )

    @computed_field  # type: ignore[misc]
    @property
    def gpa(self) -> float:
        """Grade Point Average from all graded attempts (0-10 scale)."""
        grades = [attempt.grade for attempt in self.attempts if attempt.grade]
        if not grades:
            return 0.0
        return round(sum(grades) / len(grades), 2)


class Student(BaseModel):
    """Student entity with academic history and demographic metadata."""

    student_id: str = Field(..., description="Unique student identifier")
    name: Optional[str] = Field(None, description="Student's full name")
    history: AcademicHistory = Field(
        default_factory=AcademicHistory, description="Academic history"
    )
    # Enriched fields (from raw CSV metadata)
    birth_year: Optional[int] = Field(None, description="Year of birth")
    access_path: Optional[int] = Field(
        None, description="University access path code (via d'acces)"
    )
    enrollment_order: Optional[int] = Field(
        None, description="Enrollment order (ordre d'assignacio)"
    )
    access_grade: Optional[float] = Field(
        None, description="University access grade (nota d'acces)"
    )

    @computed_field  # type: ignore[misc]
    @property
    def attempts(self) -> int:
        """Number of course attempts."""
        return len(self.history)

    @computed_field  # type: ignore[misc]
    @property
    def enrollments(self) -> int:
        """Number of unique year-term enrollment periods."""
        unique_terms = set()
        for attempt in self.history.attempts:
            if attempt.term:
                unique_terms.add((attempt.year, attempt.term))
        return len(unique_terms)


class TermType(str, Enum):
    YEARLY = "yearly"
    SEMESTER = "semester"
    TRIMESTER = "trimester"
    QUADRIMESTER = "quadrimester"

    def get_terms_per_year(self) -> int:
        return {
            TermType.YEARLY: 1,
            TermType.SEMESTER: 2,
            TermType.TRIMESTER: 3,
            TermType.QUADRIMESTER: 4,
        }[self]


class Programme(BaseModel):
    """Academic programme (degree program)."""

    programme_id: str = Field(..., description="Unique programme identifier")
    name: str = Field(..., description="Programme name")
    courses: List[Course] = Field(default_factory=list)
    credits_required: Optional[float] = Field(None, ge=0.0)
    term_type: Optional[TermType] = Field(None)


class Department(BaseModel):
    """Academic department that offers courses."""

    department_id: str = Field(..., description="Unique department identifier")
    name: str = Field(..., description="Department name")
    courses: List[Course] = Field(default_factory=list)


class University(BaseModel):
    """Root aggregate: the entire university dataset.

    This is the top-level model validated when loading a *.educast.json file.
    """

    university_id: str = Field(..., description="Unique university identifier")
    name: str = Field(..., description="University name")
    departments: List[Department] = Field(default_factory=list)
    programmes: List[Programme] = Field(default_factory=list)
    students: List[Student] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def total_students(self) -> int:
        return len(self.students)

    @computed_field  # type: ignore[misc]
    @property
    def total_departments(self) -> int:
        return len(self.departments)

    @computed_field  # type: ignore[misc]
    @property
    def total_courses(self) -> int:
        course_ids = {
            course.course_id for dept in self.departments for course in dept.courses
        }
        return len(course_ids)

    @computed_field  # type: ignore[misc]
    @property
    def total_enrollments(self) -> int:
        return sum(student.enrollments for student in self.students)


__all__ = [
    "ClickstreamData",
    "Course",
    "AttemptedCourse",
    "AcademicHistory",
    "Student",
    "TermType",
    "Programme",
    "Department",
    "University",
]
