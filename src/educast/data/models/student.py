from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from .course import AttemptedCourse


class AcademicHistory(BaseModel):
    """
    Student's complete academic history.

    Tracks all course attempts, calculates cumulative statistics like
    total credits earned and GPA (0-10 scale).

    Computed Properties:
        total_credits: Sum of credits from passed courses
        gpa: Grade Point Average from all graded attempts (0-10 scale)

    Example:
        >>> history = AcademicHistory()
        >>> course = Course(course_id="CS101", credits=5.0)
        >>> grade = Grade(max_grade=100, min_grade=0, raw_grade=85, pass_grade=5)
        >>> attempt = AttemptedCourse(
        ...     course=course,
        ...     year="2024",
        ...     timestamp=datetime.now(),
        ...     grade=grade
        ... )
        >>> history.add_attempt(attempt)
        >>> history.total_credits
        5.0
        >>> history.gpa
        8.5
    """

    attempts: List[AttemptedCourse] = Field(
        default_factory=list, description="List of course attempts"
    )

    def add_attempt(self, attempted_course: AttemptedCourse) -> None:
        """
        Add a course attempt to the academic history.
        """
        self.attempts.append(attempted_course)

    def __len__(self) -> int:
        """
        Get number of course attempts.
        """
        return len(self.attempts)

    @computed_field  # type: ignore[misc]
    @property
    def total_credits(self) -> float:
        """
        Calculate total credits earned from passed courses.

        Only counts credits from courses where the student passed.
        In-progress or failed courses do not contribute to the total.
        """
        return sum(
            attempt.course.credits for attempt in self.attempts if attempt.passed
        )

    @computed_field  # type: ignore[misc]
    @property
    def gpa(self) -> float:
        """
        Calculate Grade Point Average from all graded attempts.

        Computes the mean of final_grade values from all graded course attempts.
        Ungraded courses (in-progress) are excluded from the calculation.
        """
        grades = [attempt.grade for attempt in self.attempts if attempt.grade]
        if not grades:
            return 0.0
        return round(sum(grades) / len(grades), 2)


class Student(BaseModel):
    """
    Student entity with academic history.

    Represents a student enrolled in the university system with
    their complete academic record.
    """

    student_id: str = Field(..., description="Unique student identifier")
    name: Optional[str] = Field(None, description="Student's full name")
    history: AcademicHistory = Field(
        default_factory=AcademicHistory, description="Academic history and records"
    )

    @computed_field  # type: ignore[misc]
    @property
    def attempts(self) -> int:
        """
        Get number of course attempts by the student.
        """
        return len(self.history)

    @computed_field  # type: ignore[misc]
    @property
    def enrollments(self) -> int:
        """
        Number of enrollments (unique year-term combinations).
        """
        unique_terms = set()
        for attempt in self.history.attempts:
            if attempt.term:
                unique_terms.add((attempt.year, attempt.term))
        return len(unique_terms)
