from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from .clickstream import ClickstreamData


class Course(BaseModel):
    """
    Represents a course that can be taken by students.
    """

    course_id: str = Field(..., description="Unique course identifier")
    name: Optional[str] = Field(None, description="Course name")
    credits: float = Field(
        0.0, description="Credit awarded for completing the course", ge=0.0
    )


class AttemptedCourse(BaseModel):
    """
    Student's attempt at a specific course.

    Tracks a student's enrollment and performance in a course,
    including grade information and activity logs.

    Computed Properties:
        passed: Whether the student passed the course (None if ungraded)
    """

    course: Course = Field(..., description="Course being attempted")
    year: Optional[int] = Field(None, description="Academic year")
    term: Optional[int] = Field(None, description="Academic term")
    timestamp: Optional[datetime] = Field(
        None, description="Attempt timestamp enrollment date"
    )
    grade: Optional[int] = Field(None, description="Grade received (if completed)")
    clickstream: List[ClickstreamData] = Field(
        default_factory=list, description="Activity logs for this course"
    )

    @computed_field  # type: ignore[misc]
    @property
    def passed(self) -> Optional[bool]:
        """
        Check if student passed the course.

        Returns:
            True if passed, False if failed, None if not yet graded
        """
        return self.grade >= 5 if self.grade is not None else None
