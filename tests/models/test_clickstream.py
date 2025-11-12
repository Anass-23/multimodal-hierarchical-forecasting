from datetime import datetime

import pytest

from educast.data.models import ClickstreamData


class TestClickstreamCreation:
    """Test ClickstreamData model creation."""

    def test_clickstream_required_fields_only(self):
        """Test creating clickstream with only required fields."""
        now = datetime.now()
        c = ClickstreamData(id=10, eventname="course_module_viewed", timestamp=now)
        assert c.id == 10
        assert c.eventname == "course_module_viewed"
        assert c.timestamp == now
        assert c.action is None
        assert c.target is None
        assert c.ip is None

    def test_clickstream_with_all_fields(self):
        """Test creating clickstream with all fields populated."""
        now = datetime.now()
        c = ClickstreamData(
            id=11,
            eventname="grade_report_viewed",
            timestamp=now,
            action="click",
            target="button",
            ip="127.0.0.1",
        )
        assert c.id == 11
        assert c.eventname == "grade_report_viewed"
        assert c.timestamp == now
        assert c.action == "click"
        assert c.target == "button"
        assert c.ip == "127.0.0.1"

    def test_clickstream_optional_fields_default_none(self):
        """Test that optional fields default to None."""
        now = datetime.now()
        c = ClickstreamData(id=1, eventname="event", timestamp=now)
        assert c.action is None
        assert c.target is None
        assert c.ip is None


class TestClickstreamFieldValidation:
    """Test ClickstreamData field validation."""

    def test_clickstream_id_must_be_integer(self):
        """Test that id field must be an integer."""
        now = datetime.now()
        c = ClickstreamData(id=123, eventname="test", timestamp=now)
        assert isinstance(c.id, int)

    def test_clickstream_timestamp_is_datetime(self):
        """Test that timestamp field is datetime."""
        now = datetime.now()
        c = ClickstreamData(id=1, eventname="test", timestamp=now)
        assert isinstance(c.timestamp, datetime)


class TestClickstreamSerialization:
    """Test ClickstreamData serialization."""

    def test_clickstream_model_dump(self):
        """Test serializing clickstream to dictionary."""
        now = datetime.now()
        c = ClickstreamData(
            id=100,
            eventname="assignment_submitted",
            timestamp=now,
            action="submit",
            target="assignment_1",
        )
        data = c.model_dump()

        assert data["id"] == 100
        assert data["eventname"] == "assignment_submitted"
        assert data["timestamp"] == now
        assert data["action"] == "submit"
        assert data["target"] == "assignment_1"

    def test_clickstream_model_dump_json(self):
        """Test serializing clickstream to JSON."""
        now = datetime.now()
        c = ClickstreamData(id=200, eventname="video_watched", timestamp=now)
        json_str = c.model_dump_json()

        assert isinstance(json_str, str)
        assert "200" in json_str
        assert "video_watched" in json_str


@pytest.mark.parametrize(
    "id,eventname,action,target",
    [
        (1, "course_viewed", "view", "course_page"),
        (2, "assignment_submitted", "submit", "assignment_1"),
        (3, "quiz_started", "start", "quiz_module"),
        (4, "forum_post_created", "create", "forum"),
    ],
)
def test_clickstream_various_events(id, eventname, action, target):
    """Parametrized test for various clickstream event types."""
    now = datetime.now()
    c = ClickstreamData(
        id=id, eventname=eventname, timestamp=now, action=action, target=target
    )

    assert c.id == id
    assert c.eventname == eventname
    assert c.action == action
    assert c.target == target
