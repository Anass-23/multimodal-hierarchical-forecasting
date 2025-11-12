from datetime import datetime

import pytest

from educast.data.models import (
    AttemptedCourse,
    ClickstreamData,
    Course,
    Department,
    Programme,
    Student,
    University,
)


@pytest.fixture
def cs101_course():
    return Course(course_id="CS101", name="Intro CS", credits=5.0)


@pytest.fixture
def math101_course():
    return Course(course_id="MATH101", name="Calculus I", credits=6.0)


@pytest.fixture
def passing_attempt(cs101_course):
    # Attempt with numeric grade (0-10 scale) — AttemptedCourse.grade is an int/float
    return AttemptedCourse(
        course=cs101_course, year=2024, term=1, timestamp=datetime.now(), grade=8
    )


@pytest.fixture
def failed_attempt(math101_course):
    return AttemptedCourse(
        course=math101_course, year=2024, term=1, timestamp=datetime.now(), grade=3
    )


@pytest.fixture
def in_progress_attempt(math101_course):
    return AttemptedCourse(
        course=math101_course, year=2024, term=2, timestamp=datetime.now(), grade=None
    )


@pytest.fixture
def basic_student():
    return Student(student_id="S100", name="Alice")


@pytest.fixture
def student_with_attempts(passing_attempt, failed_attempt, in_progress_attempt):
    s = Student(student_id="S200", name="Bob")
    s.history.add_attempt(passing_attempt)
    s.history.add_attempt(failed_attempt)
    s.history.add_attempt(in_progress_attempt)
    return s


@pytest.fixture
def sample_clickstream():
    now = datetime.now()
    return [
        ClickstreamData(
            id=1, eventname="view", timestamp=now, action="view", target="course_page"
        ),
        ClickstreamData(
            id=2,
            eventname="submit",
            timestamp=now,
            action="submit",
            target="assignment",
        ),
    ]


@pytest.fixture
def cs_programme(cs101_course, math101_course):
    return Programme(
        programme_id="CS_BSC",
        name="CS BSc",
        courses=[cs101_course, math101_course],
        credits_required=180.0,
    )


@pytest.fixture
def cs_department(cs101_course, math101_course):
    return Department(
        department_id="CS_DEPT", name="CS", courses=[cs101_course, math101_course]
    )


@pytest.fixture
def sample_university(
    cs_department, basic_student, student_with_attempts, cs_programme
):
    return University(
        university_id="UNI1",
        name="Test Uni",
        departments=[cs_department],
        programmes=[cs_programme],
        students=[basic_student, student_with_attempts],
    )
