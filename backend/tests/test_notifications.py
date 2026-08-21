from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.notification import (
    Notification,
    NotificationType,
)
from backend.app.models.user import User
from backend.app.services.notification import create_notification


def auth_headers(
    user: User,
) -> dict[str, str]:
    """
    Create JWT authentication headers for a test user.
    """

    from backend.app.core.security import create_access_token

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def create_test_notification(
    db: Session,
    user: User,
    *,
    title: str = "Test notification",
    message: str = "This is a test notification.",
    notification_type: NotificationType = NotificationType.INFO,
) -> Notification:
    """
    Create a notification directly for testing.
    """

    notification = Notification(
        user_id=user.id,
        type=notification_type,
        title=title,
        message=message,
    )

    db.add(notification)
    db.flush()

    return notification


def test_list_notifications_requires_authentication(
    client: TestClient,
):
    response = client.get(
        "/notifications",
    )

    assert response.status_code == 401


def test_list_notifications(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_notification(
        db,
        member_user,
        title="Welcome to KBR",
        message="Welcome to Knights of Bizertin Rise.",
    )

    response = client.get(
        "/notifications",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["unread_count"] == 1

    notification = data["items"][0]

    assert notification["user_id"] == str(member_user.id)
    assert notification["title"] == "Welcome to KBR"
    assert notification["message"] == (
        "Welcome to Knights of Bizertin Rise."
    )
    assert notification["is_read"] is False
    assert notification["read_at"] is None


def test_notifications_are_isolated_between_users(
    client: TestClient,
    db: Session,
    member_user: User,
):
    other_user = User(
        email=f"other-{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_email_verified=True,
    )

    db.add(other_user)
    db.flush()

    create_test_notification(
        db,
        member_user,
        title="Private notification",
        message="Only member one should see this.",
    )

    create_test_notification(
        db,
        other_user,
        title="Other notification",
        message="Only member two should see this.",
    )

    response = client.get(
        "/notifications",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Private notification"


def test_list_unread_notifications(
    client: TestClient,
    db: Session,
    member_user: User,
):
    unread_notification = create_test_notification(
        db,
        member_user,
        title="Unread notification",
    )

    read_notification = create_test_notification(
        db,
        member_user,
        title="Read notification",
    )

    read_notification.is_read = True

    db.flush()

    response = client.get(
        "/notifications",
        params={
            "unread_only": True,
        },
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["unread_count"] == 1
    assert data["items"][0]["id"] == str(
        unread_notification.id
    )


def test_get_unread_notification_count(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_notification(
        db,
        member_user,
        title="Notification 1",
    )

    create_test_notification(
        db,
        member_user,
        title="Notification 2",
    )

    read_notification = create_test_notification(
        db,
        member_user,
        title="Notification 3",
    )

    read_notification.is_read = True

    db.flush()

    response = client.get(
        "/notifications/unread-count",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["unread_count"] == 2


def test_mark_notification_as_read(
    client: TestClient,
    db: Session,
    member_user: User,
):
    notification = create_test_notification(
        db,
        member_user,
        title="New notification",
    )

    response = client.patch(
        f"/notifications/{notification.id}/read",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "Notification marked as read."
    )

    assert data["notification"]["id"] == str(
        notification.id
    )

    assert data["notification"]["is_read"] is True
    assert data["notification"]["read_at"] is not None


def test_mark_notification_as_read_is_idempotent(
    client: TestClient,
    db: Session,
    member_user: User,
):
    notification = create_test_notification(
        db,
        member_user,
    )

    first_response = client.patch(
        f"/notifications/{notification.id}/read",
        headers=auth_headers(member_user),
    )

    assert first_response.status_code == 200

    first_read_at = first_response.json()[
        "notification"
    ]["read_at"]

    second_response = client.patch(
        f"/notifications/{notification.id}/read",
        headers=auth_headers(member_user),
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["notification"]["is_read"] is True
    assert second_data["notification"]["read_at"] == (
        first_read_at
    )


def test_cannot_read_another_users_notification(
    client: TestClient,
    db: Session,
    member_user: User,
):
    other_user = User(
        email=f"other-{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_email_verified=True,
    )

    db.add(other_user)
    db.flush()

    notification = create_test_notification(
        db,
        other_user,
        title="Private notification",
    )

    response = client.patch(
        f"/notifications/{notification.id}/read",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 404


def test_mark_all_notifications_as_read(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_notification(
        db,
        member_user,
        title="Notification 1",
    )

    create_test_notification(
        db,
        member_user,
        title="Notification 2",
    )

    create_test_notification(
        db,
        member_user,
        title="Notification 3",
    )

    response = client.post(
        "/notifications/read-all",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "All notifications marked as read."
    )

    assert data["updated_count"] == 3

    unread_response = client.get(
        "/notifications/unread-count",
        headers=auth_headers(member_user),
    )

    assert unread_response.status_code == 200
    assert unread_response.json()["unread_count"] == 0


def test_mark_all_notifications_as_read_when_none_are_unread(
    client: TestClient,
    db: Session,
    member_user: User,
):
    notification = create_test_notification(
        db,
        member_user,
    )

    notification.is_read = True

    db.flush()

    response = client.post(
        "/notifications/read-all",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["updated_count"] == 0


def test_get_missing_notification_returns_404(
    client: TestClient,
    member_user: User,
):
    notification_id = uuid4()

    response = client.patch(
        f"/notifications/{notification_id}/read",
        headers=auth_headers(member_user),
    )

    assert response.status_code == 404


def test_create_notification_service(
    db: Session,
    member_user: User,
):
    notification = create_notification(
        db,
        user_id=member_user.id,
        title="  Service test  ",
        message="  Notification created by service.  ",
        notification_type=NotificationType.INFO,
    )

    assert notification.id is not None
    assert notification.user_id == member_user.id
    assert notification.type == NotificationType.INFO
    assert notification.title == "Service test"
    assert notification.message == (
        "Notification created by service."
    )
    assert notification.is_read is False
    assert notification.read_at is None