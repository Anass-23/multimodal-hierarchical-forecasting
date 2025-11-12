from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field

from .course import Course
from .student import Student


class TermType(str, Enum):
    YEARLY = "yearly"
    SEMESTER = "semester"
    TRIMESTER = "trimester"
    QUADRIMESTER = "quadrimester"

    def get_terms_per_year(self) -> int:
        mapping = {
            TermType.YEARLY: 1,
            TermType.SEMESTER: 2,
            TermType.TRIMESTER: 3,
            TermType.QUADRIMESTER: 4,
        }
        return mapping[self]


class Programme(BaseModel):
    """
    Academic programme (degree program).

    Represents a degree programme such as "Bachelor of Computer Science"
    with its associated courses and credit requirements.
    """

    programme_id: str = Field(..., description="Unique programme identifier")
    name: str = Field(..., description="Programme name")
    courses: List[Course] = Field(
        default_factory=list, description="Courses given in this programme"
    )
    credits_required: Optional[float] = Field(
        None, description="Total credits required for completion", ge=0.0
    )
    term_type: Optional[TermType] = Field(None, description="Term type for the program")


class Department(BaseModel):
    """
    Academic department within a university which offers courses.
    """

    department_id: str = Field(..., description="Unique department identifier")
    name: str = Field(..., description="Department name")
    courses: List[Course] = Field(
        default_factory=list, description="Courses offered by this department"
    )


class University(BaseModel):
    """
    Represents the entire university with all its departments and students.
    This is the root of the organizational hierarchy.

    Computed Properties:
        total_students: Count of enrolled students
        total_departments: Count of departments
        total_courses: Count of courses offered
        total_enrollments: Total student enrollments across all students
    """

    university_id: str = Field(..., description="Unique university identifier")
    name: str = Field(..., description="University name")
    departments: List[Department] = Field(
        default_factory=list, description="Departments in the university"
    )
    programmes: List[Programme] = Field(
        default_factory=list, description="Programmes in the university"
    )
    students: List[Student] = Field(
        default_factory=list, description="Enrolled students"
    )

    @computed_field  # type: ignore[misc]
    @property
    def total_students(self) -> int:
        """
        Get total number of enrolled students.

        Returns:
            Count of students in the students list
        """
        return len(self.students)

    @computed_field  # type: ignore[misc]
    @property
    def total_departments(self) -> int:
        """
        Get total number of departments.

        Returns:
            Count of departments in the departments list
        """
        return len(self.departments)

    @computed_field  # type: ignore[misc]
    @property
    def total_courses(self) -> int:
        """
        Get total number of courses offered.

        Returns:
            Count of unique courses across all departments
        """
        course_ids = {
            course.course_id for dept in self.departments for course in dept.courses
        }
        return len(course_ids)

    @computed_field  # type: ignore[misc]
    @property
    def total_enrollments(self) -> int:
        """
        Get total number of course enrollments across all students.

        Returns:
            Total count of course attempts by all students
        """
        return sum(student.enrollments for student in self.students)
