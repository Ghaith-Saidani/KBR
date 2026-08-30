import uuid

from backend.app.models.user_activity import UserActivity
from backend.app.services.user_activity import log_user_activity


def test_log_user_activity_creates_activity(
    db,
    member_user,
):
    resource_id = uuid.uuid4()

    activity = log_user_activity(
        db,
        action="create_event",
        user_id=member_user.id,
        resource_type="event",
        resource_id=resource_id,
        method="POST",
        endpoint="/events",
        ip_address="127.0.0.1",
        user_agent="pytest",
        details="Test event creation",
        activity_metadata={
            "source": "test",
            "test": True,
        },
    )

    db.flush()

    assert activity.id is not None
    assert activity.user_id == member_user.id
    assert activity.action == "create_event"
    assert activity.resource_type == "event"
    assert activity.resource_id == resource_id
    assert activity.method == "POST"
    assert activity.endpoint == "/events"
    assert activity.ip_address == "127.0.0.1"
    assert activity.user_agent == "pytest"
    assert activity.details == "Test event creation"
    assert activity.activity_metadata == {
        "source": "test",
        "test": True,
    }


def test_log_user_activity_supports_anonymous_activity(
    db,
):
    activity = log_user_activity(
        db,
        action="contact_message_created",
        details="Anonymous contact message",
    )

    db.flush()

    assert activity.id is not None
    assert activity.user_id is None
    assert activity.action == "contact_message_created"