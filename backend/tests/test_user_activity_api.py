import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.user_activity import UserActivity
from backend.tests.conftest import create_test_user


def create_activity(
    db,
    *,
    user_id=None,
    action="TEST_ACTION",
    resource_type="test",
    method="GET",
    occurred_at=None,
):
    activity = UserActivity(
        id=uuid.uuid4(),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        method=method,
        endpoint="/test",
        details="Test activity",
        occurred_at=occurred_at,
    )

    db.add(activity)
    db.flush()

    return activity


def admin_headers(admin_user: User) -> dict[str, str]:
    """Build authorization headers for an admin test user."""

    token = create_access_token(
        subject=str(admin_user.id),
        role=admin_user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_admin_can_list_activity_logs(
    client,
    db,
    admin_user,
):
    create_activity(
        db,
        user_id=admin_user.id,
        action="MEMBER_CREATED",
    )

    db.commit()

    response = client.get(
        "/admin/activity-logs",
        headers=admin_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data

    assert data["total"] >= 1

    assert any(
        item["action"] == "MEMBER_CREATED"
        for item in data["items"]
    )


def test_non_admin_cannot_list_activity_logs(
    client,
    db,
    member_user,
):
    token = create_access_token(
        subject=str(member_user.id),
        role=member_user.role.value,
    )

    response = client.get(
        "/admin/activity-logs",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_activity_logs_can_be_filtered_by_user(
    client,
    db,
    admin_user,
):
    other_user = create_test_user(
        db,
        email=f"activity-other-{uuid.uuid4()}@example.com",
    )

    create_activity(
        db,
        user_id=admin_user.id,
        action="ADMIN_ACTION",
    )

    create_activity(
        db,
        user_id=other_user.id,
        action="OTHER_ACTION",
    )

    db.commit()

    response = client.get(
        "/admin/activity-logs",
        params={
            "user_id": str(admin_user.id),
        },
        headers=admin_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["action"] == "ADMIN_ACTION"


def test_activity_logs_can_be_filtered_by_action(
    client,
    db,
    admin_user,
):
    create_activity(
        db,
        user_id=admin_user.id,
        action="LOGIN",
    )

    create_activity(
        db,
        user_id=admin_user.id,
        action="LOGOUT",
    )

    db.commit()

    response = client.get(
        "/admin/activity-logs",
        params={
            "action": "LOGIN",
        },
        headers=admin_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["action"] == "LOGIN"


def test_activity_logs_can_be_filtered_by_method(
    client,
    db,
    admin_user,
):
    create_activity(
        db,
        user_id=admin_user.id,
        action="READ_ACTION",
        method="GET",
    )

    create_activity(
        db,
        user_id=admin_user.id,
        action="WRITE_ACTION",
        method="POST",
    )

    db.commit()

    response = client.get(
        "/admin/activity-logs",
        params={
            "method": "POST",
        },
        headers=admin_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["action"] == "WRITE_ACTION"


def test_activity_logs_support_date_filters(
    client,
    db,
    admin_user,
):
    now = datetime.now(timezone.utc)

    create_activity(
        db,
        user_id=admin_user.id,
        action="OLD_ACTION",
        occurred_at=now - timedelta(days=2),
    )

    create_activity(
        db,
        user_id=admin_user.id,
        action="RECENT_ACTION",
        occurred_at=now,
    )

    db.commit()

    response = client.get(
        "/admin/activity-logs",
        params={
            "date_from": (
                now - timedelta(days=1)
            ).isoformat(),
        },
        headers=admin_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["action"] == "RECENT_ACTION"


def test_activity_logs_support_pagination(
    client,
    db,
    admin_user,
):
    for index in range(5):
        create_activity(
            db,
            user_id=admin_user.id,
            action=f"ACTION_{index}",
        )

    db.commit()

    response = client.get(
        "/admin/activity-logs",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers=admin_headers(admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3