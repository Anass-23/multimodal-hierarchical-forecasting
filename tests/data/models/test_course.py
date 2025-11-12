from datetime import datetime

import pytest

from educast.data.models import AttemptedCourse, ClickstreamData, Course


class TestCourseCreation:
    """Test Course model creation."""

    def test_course_creation_minimal(self):
        """Test creating a course with only course_id."""
        c = Course(course_id="CS101")
        assert c.course_id == "CS101"
        assert c.name is None
        assert c.credits == 0.0

    def test_course_creation_with_all_fields(self):
        """Test creating a course with all fields."""
        c = Course(course_id="TST100", name="Test Course", credits=4.0)
        assert c.course_id == "TST100"
        assert c.name == "Test Course"
        assert c.credits == 4.0

    def test_course_default_credits_zero(self):
        """Test that credits default to 0.0."""
        c = Course(course_id="C1")
        assert c.credits == 0.0


class TestCourseValidation:
    """Test Course field validation."""

    def test_course_credits_non_negative(self):
        """Test that credits cannot be negative."""
        with pytest.raises(Exception):  # Pydantic validation error
            Course(course_id="C1", credits=-1.0)

    def test_course_credits_can_be_zero(self):
        """Test that credits can be zero."""
        c = Course(course_id="C1", credits=0.0)
        assert c.credits == 0.0


class TestAttemptedCourseCreation:
    """Test AttemptedCourse model creation."""

    def test_attempted_course_minimal(self):
        """Test creating attempted course with only required course field."""
        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(course=course)
        assert attempt.course.course_id == "CS101"
        assert attempt.year is None
        assert attempt.term is None
        assert attempt.timestamp is None
        assert attempt.grade is None

    def test_attempted_course_with_all_fields(self):
        """Test creating attempted course with all fields."""
        course = Course(course_id="CS101", credits=5.0)
        now = datetime.now()
        attempt = AttemptedCourse(
            course=course, year=2024, term=1, timestamp=now, grade=8
        )
        assert attempt.course.course_id == "CS101"
        assert attempt.year == 2024
        assert attempt.term == 1
        assert attempt.timestamp == now
        assert attempt.grade == 8

    def test_attempted_course_clickstream_defaults_empty(self):
        """Test that clickstream list defaults to empty."""
        course = Course(course_id="C4", credits=2.0)
        attempt = AttemptedCourse(course=course)
        assert isinstance(attempt.clickstream, list)
        assert len(attempt.clickstream) == 0


class TestAttemptedCoursePassed:
    """Test AttemptedCourse 'passed' computed property."""

    def test_passed_true_when_grade_equal_to_5(self):
        """Test that passed is True when grade equals 5."""
        course = Course(course_id="C1", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=5)
        assert attempt.passed is True

    def test_passed_true_when_grade_greater_than_5(self):
        """Test that passed is True when grade is greater than 5."""
        course = Course(course_id="C1", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=7)
        assert attempt.passed is True

    def test_passed_false_when_grade_below_5(self):
        """Test that passed is False when grade is below 5."""
        course = Course(course_id="C2", credits=3.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=2)
        assert attempt.passed is False

    def test_passed_false_when_grade_is_zero(self):
        """Test that passed is False when grade is 0."""
        course = Course(course_id="C3", credits=3.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=0)
        assert attempt.passed is False

    def test_passed_none_when_ungraded(self):
        """Test that passed is None when no grade is assigned."""
        course = Course(course_id="C3", credits=3.0)
        attempt = AttemptedCourse(course=course, year=2024, grade=None)
        assert attempt.passed is None


class TestAttemptedCourseClickstream:
    """Test AttemptedCourse clickstream integration."""

    def test_add_clickstream_data(self):
        """Test adding clickstream data to attempted course."""
        course = Course(course_id="CS101", credits=5.0)
        attempt = AttemptedCourse(course=course, year=2024)

        now = datetime.now()
        click1 = ClickstreamData(
            id=1, eventname="course_viewed", timestamp=now, action="view"
        )
        click2 = ClickstreamData(
            id=2, eventname="assignment_submitted", timestamp=now, action="submit"
        )

        attempt.clickstream.append(click1)
        attempt.clickstream.append(click2)

        assert len(attempt.clickstream) == 2
        assert attempt.clickstream[0].eventname == "course_viewed"
        assert attempt.clickstream[1].eventname == "assignment_submitted"

    def test_attempted_course_with_clickstream_in_constructor(self):
        """Test creating attempted course with clickstream data."""
        course = Course(course_id="CS101", credits=5.0)
        now = datetime.now()
        clickstream = [
            ClickstreamData(id=1, eventname="event1", timestamp=now),
            ClickstreamData(id=2, eventname="event2", timestamp=now),
        ]

        attempt = AttemptedCourse(course=course, clickstream=clickstream)
        assert len(attempt.clickstream) == 2


class TestAttemptedCourseSerialization:
    """Test AttemptedCourse serialization."""

    def test_attempted_course_model_dump(self):
        """Test serializing attempted course to dictionary."""
        course = Course(course_id="CS101", name="Intro CS", credits=5.0)
        now = datetime.now()
        attempt = AttemptedCourse(
            course=course, year=2024, term=1, timestamp=now, grade=8
        )

        data = attempt.model_dump()

        assert data["course"]["course_id"] == "CS101"
        assert data["year"] == 2024
        assert data["term"] == 1
        assert data["grade"] == 8
        assert data["passed"] is True


@pytest.mark.parametrize(
    "grade,expected_passed",
    [
        (10, True),
        (9, True),
        (8, True),
        (7, True),
        (6, True),
        (5, True),
        (4, False),
        (3, False),
        (2, False),
        (1, False),
        (0, False),
        (None, None),
    ],
)
def test_attempted_course_passed_boundary_values(grade, expected_passed):
    """Parametrized test for passed property with various grades."""
    course = Course(course_id="TEST", credits=5.0)
    attempt = AttemptedCourse(course=course, grade=grade)
    assert attempt.passed == expected_passed
