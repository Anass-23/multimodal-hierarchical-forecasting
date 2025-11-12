from datetime import datetime

import pytest

from educast.data.models import (
    AttemptedCourse,
    Course,
    Department,
    Programme,
    Student,
    TermType,
    University,
)


class TestTermType:
    """Test TermType enumeration."""

    def test_termtype_yearly_value(self):
        """Test YEARLY term type returns 1 term per year."""
        assert TermType.YEARLY.get_terms_per_year() == 1

    def test_termtype_semester_value(self):
        """Test SEMESTER term type returns 2 terms per year."""
        assert TermType.SEMESTER.get_terms_per_year() == 2

    def test_termtype_trimester_value(self):
        """Test TRIMESTER term type returns 3 terms per year."""
        assert TermType.TRIMESTER.get_terms_per_year() == 3

    def test_termtype_quadrimester_value(self):
        """Test QUADRIMESTER term type returns 4 terms per year."""
        assert TermType.QUADRIMESTER.get_terms_per_year() == 4

    def test_termtype_all_values(self):
        """Test all TermType enum values exist."""
        assert TermType.YEARLY
        assert TermType.SEMESTER
        assert TermType.TRIMESTER
        assert TermType.QUADRIMESTER


class TestProgrammeCreation:
    """Test Programme model creation."""

    def test_programme_creation_minimal(self):
        """Test creating programme with minimal required fields."""
        prog = Programme(programme_id="CS_BSC", name="CS BSc")
        assert prog.programme_id == "CS_BSC"
        assert prog.name == "CS BSc"
        assert prog.courses == []
        assert prog.credits_required is None
        assert prog.term_type is None

    def test_programme_creation_with_all_fields(self):
        """Test creating programme with all fields."""
        c1 = Course(course_id="CS101", credits=5.0)
        c2 = Course(course_id="CS102", credits=6.0)

        prog = Programme(
            programme_id="CS_BSC",
            name="Computer Science BSc",
            courses=[c1, c2],
            credits_required=180.0,
            term_type=TermType.SEMESTER,
        )

        assert prog.programme_id == "CS_BSC"
        assert prog.name == "Computer Science BSc"
        assert len(prog.courses) == 2
        assert prog.credits_required == 180.0
        assert prog.term_type == TermType.SEMESTER

    def test_programme_default_courses_empty(self):
        """Test that courses list defaults to empty."""
        prog = Programme(programme_id="P1", name="Programme 1")
        assert isinstance(prog.courses, list)
        assert len(prog.courses) == 0


class TestProgrammeValidation:
    """Test Programme field validation."""

    def test_programme_credits_required_non_negative(self):
        """Test that credits_required cannot be negative."""
        with pytest.raises(Exception):  # Pydantic validation error
            Programme(programme_id="P1", name="Test", credits_required=-10.0)

    def test_programme_credits_required_can_be_zero(self):
        """Test that credits_required can be zero."""
        prog = Programme(programme_id="P1", name="Test", credits_required=0.0)
        assert prog.credits_required == 0.0


class TestDepartmentCreation:
    """Test Department model creation."""

    def test_department_creation_minimal(self):
        """Test creating department with minimal fields."""
        dept = Department(department_id="CS_DEPT", name="Computer Science")
        assert dept.department_id == "CS_DEPT"
        assert dept.name == "Computer Science"
        assert dept.courses == []

    def test_department_creation_with_courses(self):
        """Test creating department with courses."""
        c1 = Course(course_id="CS101", name="Intro CS", credits=5.0)
        c2 = Course(course_id="MATH101", name="Calculus", credits=6.0)

        dept = Department(
            department_id="CS_DEPT", name="Computer Science", courses=[c1, c2]
        )

        assert dept.department_id == "CS_DEPT"
        assert dept.name == "Computer Science"
        assert len(dept.courses) == 2
        assert dept.courses[0].course_id == "CS101"
        assert dept.courses[1].course_id == "MATH101"

    def test_department_default_courses_empty(self):
        """Test that courses list defaults to empty."""
        dept = Department(department_id="D1", name="Dept 1")
        assert isinstance(dept.courses, list)
        assert len(dept.courses) == 0


class TestUniversityCreation:
    """Test University model creation."""

    def test_university_creation_minimal(self):
        """Test creating university with minimal fields."""
        uni = University(university_id="UNI1", name="Test University")
        assert uni.university_id == "UNI1"
        assert uni.name == "Test University"
        assert uni.departments == []
        assert uni.programmes == []
        assert uni.students == []

    def test_university_creation_with_all_fields(self):
        """Test creating university with all fields."""
        c1 = Course(course_id="C1", credits=5.0)
        dept = Department(department_id="D1", name="Dept1", courses=[c1])
        prog = Programme(programme_id="P1", name="Prog1")
        student = Student(student_id="S1", name="Alice")

        uni = University(
            university_id="UNI1",
            name="Test Uni",
            departments=[dept],
            programmes=[prog],
            students=[student],
        )

        assert uni.university_id == "UNI1"
        assert len(uni.departments) == 1
        assert len(uni.programmes) == 1
        assert len(uni.students) == 1


class TestUniversityComputedProperties:
    """Test University computed properties."""

    def test_total_students_empty(self):
        """Test total_students with no students."""
        uni = University(university_id="U1", name="U")
        assert uni.total_students == 0

    def test_total_students_multiple(self):
        """Test total_students with multiple students."""
        s1 = Student(student_id="S1")
        s2 = Student(student_id="S2")
        uni = University(university_id="U1", name="U", students=[s1, s2])
        assert uni.total_students == 2

    def test_total_departments_empty(self):
        """Test total_departments with no departments."""
        uni = University(university_id="U1", name="U")
        assert uni.total_departments == 0

    def test_total_departments_multiple(self):
        """Test total_departments with multiple departments."""
        d1 = Department(department_id="D1", name="Dept1")
        d2 = Department(department_id="D2", name="Dept2")
        uni = University(university_id="U1", name="U", departments=[d1, d2])
        assert uni.total_departments == 2

    def test_total_courses_empty(self):
        """Test total_courses with no courses."""
        uni = University(university_id="U1", name="U")
        assert uni.total_courses == 0

    def test_total_courses_single_department(self):
        """Test total_courses from single department."""
        c1 = Course(course_id="C1", credits=5.0)
        c2 = Course(course_id="C2", credits=3.0)
        dept = Department(department_id="D1", name="Dept1", courses=[c1, c2])

        uni = University(university_id="U1", name="U", departments=[dept])
        assert uni.total_courses == 2

    def test_total_courses_multiple_departments(self):
        """Test total_courses from multiple departments."""
        c1 = Course(course_id="C1", credits=5.0)
        c2 = Course(course_id="C2", credits=3.0)
        c3 = Course(course_id="C3", credits=4.0)

        dept1 = Department(department_id="D1", name="Dept1", courses=[c1, c2])
        dept2 = Department(department_id="D2", name="Dept2", courses=[c3])

        uni = University(university_id="U1", name="U", departments=[dept1, dept2])
        assert uni.total_courses == 3

    def test_total_courses_deduplicates_same_course(self):
        """Test total_courses deduplicates courses across departments."""
        c1 = Course(course_id="C1", credits=5.0)
        c2 = Course(course_id="C2", credits=3.0)

        # Same course in both departments
        dept1 = Department(department_id="D1", name="Dept1", courses=[c1, c2])
        dept2 = Department(department_id="D2", name="Dept2", courses=[c1])

        uni = University(university_id="U1", name="U", departments=[dept1, dept2])
        # Should only count unique course IDs
        assert uni.total_courses == 2


class TestUniversityEnrollments:
    """Test University enrollment tracking."""

    def test_total_enrollments_no_students(self):
        """Test total_enrollments with no students."""
        uni = University(university_id="U1", name="U")
        assert uni.total_enrollments == 0

    def test_total_enrollments_students_no_attempts(self):
        """Test total_enrollments with students but no course attempts."""
        s1 = Student(student_id="S1")
        s2 = Student(student_id="S2")
        uni = University(university_id="U1", name="U", students=[s1, s2])
        assert uni.total_enrollments == 0

    def test_total_enrollments_counts_unique_terms(self):
        """Test total_enrollments counts unique (year, term) combinations."""
        c = Course(course_id="C3", credits=5.0)
        s = Student(student_id="S3")

        # Multiple attempts in same term
        s.history.add_attempt(
            AttemptedCourse(course=c, year=2024, term=1, timestamp=datetime.now())
        )
        s.history.add_attempt(
            AttemptedCourse(course=c, year=2024, term=1, timestamp=datetime.now())
        )
        # Different term
        s.history.add_attempt(
            AttemptedCourse(course=c, year=2024, term=2, timestamp=datetime.now())
        )

        uni = University(university_id="U2", name="U2", students=[s])
        # Should count unique (year, term) combinations: (2024,1) and (2024,2) = 2
        assert uni.total_enrollments == 2

    def test_total_enrollments_multiple_students(self):
        """Test total_enrollments across multiple students."""
        c = Course(course_id="C1", credits=5.0)

        s1 = Student(student_id="S1")
        s1.history.add_attempt(
            AttemptedCourse(course=c, year=2024, term=1, timestamp=datetime.now())
        )

        s2 = Student(student_id="S2")
        s2.history.add_attempt(
            AttemptedCourse(course=c, year=2024, term=1, timestamp=datetime.now())
        )
        s2.history.add_attempt(
            AttemptedCourse(course=c, year=2024, term=2, timestamp=datetime.now())
        )

        uni = University(university_id="U1", name="U", students=[s1, s2])
        # s1: 1 enrollment, s2: 2 enrollments = 3 total
        assert uni.total_enrollments == 3


class TestUniversitySerialization:
    """Test University serialization."""

    def test_university_model_dump(self):
        """Test serializing university to dictionary."""
        c1 = Course(course_id="C1", credits=5.0)
        dept = Department(department_id="D1", name="Dept1", courses=[c1])
        student = Student(student_id="S1", name="Alice")

        uni = University(
            university_id="UNI1",
            name="Test University",
            departments=[dept],
            students=[student],
        )

        data = uni.model_dump()

        assert data["university_id"] == "UNI1"
        assert data["name"] == "Test University"
        assert len(data["departments"]) == 1
        assert len(data["students"]) == 1
        assert data["total_students"] == 1
        assert data["total_departments"] == 1
        assert data["total_courses"] == 1


@pytest.mark.parametrize(
    "term_type,expected_terms",
    [
        (TermType.YEARLY, 1),
        (TermType.SEMESTER, 2),
        (TermType.TRIMESTER, 3),
        (TermType.QUADRIMESTER, 4),
    ],
)
def test_programme_term_types(term_type, expected_terms):
    """Parametrized test for different programme term types."""
    prog = Programme(programme_id="P1", name="Test Programme", term_type=term_type)
    assert prog.term_type.get_terms_per_year() == expected_terms
