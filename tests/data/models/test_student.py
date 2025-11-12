from datetime import datetime

import pytest

from educast.data.models import AcademicHistory, AttemptedCourse, Course, Student


class TestStudentCreation:
    """Test Student model creation."""

    def test_student_creation_minimal(self):
        """Test creating a student with only student_id."""
        student = Student(student_id="S12345")
        assert student.student_id == "S12345"
        assert student.name is None
        assert len(student.history) == 0

    def test_student_creation_with_name(self):
        """Test creating a student with a name."""
        student = Student(student_id="S12345", name="John Doe")
        assert student.student_id == "S12345"
        assert student.name == "John Doe"

    def test_student_default_history(self):
        """Test that student has an empty history by default."""
        student = Student(student_id="S001")
        assert isinstance(student.history, AcademicHistory)
        assert len(student.history) == 0

    def test_student_attempts_property(self):
        """Test student.attempts property returns count of attempts."""
        student = Student(student_id="S001")
        assert student.attempts == 0

        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=7)
        student.history.add_attempt(attempt)

        assert student.attempts == 1


class TestAcademicHistoryCreation:
    """Test AcademicHistory model creation."""

    def test_empty_history(self):
        """Test creating an empty academic history."""
        history = AcademicHistory()
        assert len(history) == 0
        assert history.attempts == []
        assert history.total_credits == 0.0
        assert history.gpa == 0.0

    def test_history_length(self):
        """Test that __len__ returns correct count."""
        history = AcademicHistory()
        assert len(history) == 0

        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024, timestamp=datetime.now())
        history.add_attempt(attempt)

        assert len(history) == 1


class TestAcademicHistoryAddAttempt:
    """Test adding course attempts to history."""

    def test_add_single_attempt(self):
        """Test adding a single course attempt."""
        history = AcademicHistory()
        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(
            course=course, year=2024, timestamp=datetime.now(), grade=8
        )

        history.add_attempt(attempt)
        assert len(history) == 1
        assert history.attempts[0].course.course_id == "CS101"

    def test_add_multiple_attempts(self):
        """Test adding multiple course attempts."""
        history = AcademicHistory()

        for i in range(5):
            course = Course(course_id=f"CS10{i}", credits=5.0)
            attempt = AttemptedCourse(
                course=course, year=2024, timestamp=datetime.now()
            )
            history.add_attempt(attempt)

        assert len(history) == 5

    def test_add_attempt_via_student(self):
        """Test adding attempt through student.history."""
        student = Student(student_id="S123")
        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=7)

        student.history.add_attempt(attempt)

        assert student.attempts == 1
        assert len(student.history) == 1


class TestAcademicHistoryTotalCredits:
    """Test total_credits computed property."""

    def test_total_credits_empty_history(self):
        """Test that empty history has 0 credits."""
        history = AcademicHistory()
        assert history.total_credits == 0.0

    def test_total_credits_passed_courses(self):
        """Test total credits from passed courses."""
        history = AcademicHistory()

        # Passed course (5 credits, grade >= 5)
        course1 = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(
            course=course1, year=2024, timestamp=datetime.now(), grade=8
        )

        # Another passed course (6 credits)
        course2 = Course(course_id="MATH101", credits=6.0)
        attempt2 = AttemptedCourse(
            course=course2, year=2024, timestamp=datetime.now(), grade=9
        )

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)

        assert history.total_credits == 11.0

    def test_total_credits_excludes_failed(self):
        """Test that failed courses don't count toward total credits."""
        history = AcademicHistory()

        # Passed course
        course1 = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(
            course=course1, year=2024, timestamp=datetime.now(), grade=8
        )

        # Failed course (grade < 5)
        course2 = Course(course_id="CS102", credits=6.0)
        attempt2 = AttemptedCourse(
            course=course2, year=2024, timestamp=datetime.now(), grade=3
        )

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)

        # Only passed course credits count
        assert history.total_credits == 5.0

    def test_total_credits_excludes_ungraded(self):
        """Test that ungraded courses don't count toward total credits."""
        history = AcademicHistory()

        # Passed course
        course1 = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(
            course=course1, year=2024, timestamp=datetime.now(), grade=8
        )

        # Ungraded course (in progress)
        course2 = Course(course_id="CS102", credits=6.0)
        attempt2 = AttemptedCourse(course=course2, year=2024, timestamp=datetime.now())

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)

        # Only passed course credits count
        assert history.total_credits == 5.0

    def test_total_credits_boundary_grade_five(self):
        """Test that grade of exactly 5 is considered passing."""
        history = AcademicHistory()

        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=5)
        history.add_attempt(attempt)

        # Grade of 5 should pass
        assert history.total_credits == 5.0


class TestAcademicHistoryGPA:
    """Test GPA computed property."""

    def test_gpa_empty_history(self):
        """Test that empty history has GPA of 0.0."""
        history = AcademicHistory()
        assert history.gpa == 0.0

    def test_gpa_single_course(self):
        """Test GPA calculation with single course."""
        history = AcademicHistory()

        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(
            course=course, year=2024, timestamp=datetime.now(), grade=8
        )

        history.add_attempt(attempt)
        assert history.gpa == 8.0

    def test_gpa_multiple_courses(self):
        """Test GPA calculation with multiple courses."""
        history = AcademicHistory()

        # Course 1: grade=8
        course1 = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(
            course=course1, year=2024, timestamp=datetime.now(), grade=8
        )

        # Course 2: grade=7
        course2 = Course(course_id="MATH101", credits=6.0)
        attempt2 = AttemptedCourse(
            course=course2, year=2024, timestamp=datetime.now(), grade=7
        )

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)

        # GPA = (8 + 7) / 2 = 7.5
        assert history.gpa == 7.5

    def test_gpa_includes_failed_courses(self):
        """Test that GPA includes failed courses in calculation."""
        history = AcademicHistory()

        # Passed course (grade 8)
        course1 = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(
            course=course1, year=2024, timestamp=datetime.now(), grade=8
        )

        # Failed course (grade 3)
        course2 = Course(course_id="CS102", credits=6.0)
        attempt2 = AttemptedCourse(
            course=course2, year=2024, timestamp=datetime.now(), grade=3
        )

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)

        # GPA = (8 + 3) / 2 = 5.5
        assert history.gpa == 5.5

    def test_gpa_excludes_ungraded(self):
        """Test that GPA excludes ungraded courses."""
        history = AcademicHistory()

        # Graded course
        course1 = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(
            course=course1, year=2024, timestamp=datetime.now(), grade=8
        )

        # Ungraded course (in progress)
        course2 = Course(course_id="CS102", credits=6.0)
        attempt2 = AttemptedCourse(course=course2, year=2024, timestamp=datetime.now())

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)

        # GPA should only consider graded attempts
        assert history.gpa == 8.0

    def test_gpa_rounding(self):
        """Test that GPA is rounded to 2 decimal places."""
        history = AcademicHistory()

        course = Course(course_id="CS101", credits=5.0)
        attempt1 = AttemptedCourse(course=course, year=2024, grade=8)
        attempt2 = AttemptedCourse(course=course, year=2024, grade=7)
        attempt3 = AttemptedCourse(course=course, year=2024, grade=6)

        history.add_attempt(attempt1)
        history.add_attempt(attempt2)
        history.add_attempt(attempt3)

        # (8 + 7 + 6) / 3 = 7.0
        assert history.gpa == 7.0


class TestStudentEnrollments:
    """Test Student enrollment tracking."""

    def test_enrollments_empty_history(self):
        """Test enrollments with no course attempts."""
        student = Student(student_id="S001")
        assert student.enrollments == 0

    def test_enrollments_counts_unique_year_term(self):
        """Test enrollments counts unique (year, term) combinations."""
        student = Student(student_id="S001")
        course = Course(course_id="CS101", credits=5.0)

        # Same year/term (should count as 1)
        student.history.add_attempt(AttemptedCourse(course=course, year=2024, term=1))
        student.history.add_attempt(AttemptedCourse(course=course, year=2024, term=1))

        # Different term (should count as 2 total)
        student.history.add_attempt(AttemptedCourse(course=course, year=2024, term=2))

        assert student.enrollments == 2

    def test_enrollments_requires_term_field(self):
        """Test enrollments only counts attempts with term field."""
        student = Student(student_id="S001")
        course = Course(course_id="CS101", credits=5.0)

        # Attempt without term (should not count)
        student.history.add_attempt(AttemptedCourse(course=course, year=2024))

        # Attempt with term (should count)
        student.history.add_attempt(AttemptedCourse(course=course, year=2024, term=1))

        assert student.enrollments == 1


class TestStudentWithHistory:
    """Test Student with complete academic history."""

    def test_student_complete_workflow(self):
        """Test a complete student academic workflow."""
        student = Student(student_id="S12345", name="Alice Johnson")

        # Year 1: Take 3 courses
        courses_data = [
            ("CS101", 5.0, 8),  # Pass
            ("MATH101", 6.0, 9),  # Pass
            ("PHY101", 4.0, 4),  # Fail (grade < 5)
        ]

        for course_id, credits, grade in courses_data:
            course = Course(course_id=course_id, credits=credits)
            attempt = AttemptedCourse(
                course=course, year=2024, timestamp=datetime.now(), grade=grade
            )
            student.history.add_attempt(attempt)

        # Verify metrics
        assert len(student.history) == 3
        assert student.attempts == 3
        assert student.history.total_credits == 11.0  # 5 + 6, not 4 (failed)
        # GPA = (8 + 9 + 4) / 3 = 7.0
        assert student.history.gpa == 7.0

    def test_student_retake_course(self):
        """Test student retaking a failed course."""
        student = Student(student_id="S001")
        course = Course(course_id="CS101", credits=5.0)

        # First attempt: failed
        attempt1 = AttemptedCourse(course=course, year=2024, term=1, grade=3)
        student.history.add_attempt(attempt1)

        # Second attempt: passed
        attempt2 = AttemptedCourse(course=course, year=2024, term=2, grade=7)
        student.history.add_attempt(attempt2)

        # Both attempts count, credits counted once for passed attempt
        assert student.attempts == 2
        assert student.history.total_credits == 5.0
        # GPA includes both attempts: (3 + 7) / 2 = 5.0
        assert student.history.gpa == 5.0

    def test_student_serialization(self):
        """Test serializing student with history."""
        student = Student(student_id="S001", name="Test Student")
        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(
            course=course, year=2024, timestamp=datetime.now(), grade=8
        )
        student.history.add_attempt(attempt)

        data = student.model_dump()

        assert data["student_id"] == "S001"
        assert data["name"] == "Test Student"
        assert len(data["history"]["attempts"]) == 1
        assert data["history"]["total_credits"] == 5.0
        assert data["history"]["gpa"] == 8.0
        assert data["attempts"] == 1


class TestStudentPerformanceScenarios:
    """Test various student performance scenarios."""

    def test_excellent_student(self):
        """Test student with all high grades."""
        student = Student(student_id="S001", name="Excellent Student")

        for i in range(5):
            course = Course(course_id=f"CS{101+i}", credits=5.0)
            attempt = AttemptedCourse(course=course, year=2024, grade=9)
            student.history.add_attempt(attempt)

        assert student.attempts == 5
        assert student.history.total_credits == 25.0
        assert student.history.gpa == 9.0

    def test_struggling_student(self):
        """Test student with mixed grades including failures."""
        student = Student(student_id="S002", name="Struggling Student")

        grades = [7, 3, 5, 4, 6]  # 2 passed (7,5,6), 2 failed (3,4)
        for i, grade in enumerate(grades):
            course = Course(course_id=f"CS{101+i}", credits=5.0)
            attempt = AttemptedCourse(course=course, year=2024, grade=grade)
            student.history.add_attempt(attempt)

        assert student.attempts == 5
        # Only grades >= 5 count: 7, 5, 6 = 3 courses * 5 credits
        assert student.history.total_credits == 15.0
        # GPA includes all: (7+3+5+4+6)/5 = 5.0
        assert student.history.gpa == 5.0

    def test_student_in_progress_courses(self):
        """Test student with mix of completed and in-progress courses."""
        student = Student(student_id="S003")

        # 2 completed courses
        c1 = Course(course_id="CS101", credits=5.0)
        student.history.add_attempt(AttemptedCourse(course=c1, year=2024, grade=8))

        c2 = Course(course_id="CS102", credits=6.0)
        student.history.add_attempt(AttemptedCourse(course=c2, year=2024, grade=7))

        # 1 in-progress course (no grade)
        c3 = Course(course_id="CS103", credits=4.0)
        student.history.add_attempt(AttemptedCourse(course=c3, year=2024))

        assert student.attempts == 3
        assert student.history.total_credits == 11.0  # Only graded & passed
        assert student.history.gpa == 7.5  # (8 + 7) / 2


@pytest.mark.parametrize(
    "num_courses,grade,expected_credits,expected_gpa",
    [
        (0, None, 0.0, 0.0),  # No courses
        (1, 8, 5.0, 8.0),  # One passing course
        (1, 3, 0.0, 3.0),  # One failing course
        (3, 8, 15.0, 8.0),  # Three passing courses
        (5, 7, 25.0, 7.0),  # Five passing courses
    ],
)
def test_student_performance_parametrized(
    num_courses, grade, expected_credits, expected_gpa
):
    """Parametrized test for different student performance scenarios."""
    student = Student(student_id="S001")

    for i in range(num_courses):
        course = Course(course_id=f"CS{101+i}", credits=5.0)
        attempt = AttemptedCourse(
            course=course, year=2024, timestamp=datetime.now(), grade=grade
        )
        student.history.add_attempt(attempt)

    assert student.history.total_credits == expected_credits
    assert student.history.gpa == expected_gpa
