from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User


def auth_headers(client: TestClient, user: User) -> dict[str, str]:
    """
    Authenticate a test user and return Authorization headers.
    """

    # The test users are created directly in the database, so we need
    # to create a valid access token using the application's security layer.
    from backend.app.core.security import create_access_token

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def event_payload(
    *,
    title: str = "KBR Test Event",
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict:
    """
    Build a valid event payload.
    """

    if start_at is None:
        start_at = datetime.now(timezone.utc) + timedelta(days=7)

    if end_at is None:
        end_at = start_at + timedelta(hours=2)

    return {
        "title": title,
        "description": "Test event for KBR.",
        "location": "Bizerte",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "cover_image": "https://example.com/kbr-event.jpg",
        "status": "published",
    }


def test_list_events_requires_authentication(
    client: TestClient,
):
    response = client.get("/events")

    assert response.status_code == 401


def test_create_event_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/events",
        json=event_payload(),
    )

    assert response.status_code == 401


def test_member_cannot_create_event(
    client: TestClient,
    member_user: User,
):
    response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_staff_can_create_event(
    client: TestClient,
    staff_user: User,
):
    response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "KBR Test Event"
    assert data["description"] == "Test event for KBR."
    assert data["location"] == "Bizerte"
    assert data["status"] == "published"
    assert data["created_by"] == str(staff_user.id)


def test_admin_can_create_event(
    client: TestClient,
    admin_user: User,
):
    response = client.post(
        "/events",
        json=event_payload(
            title="KBR Admin Event",
        ),
        headers=auth_headers(client, admin_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "KBR Admin Event"
    assert data["created_by"] == str(admin_user.id)


def test_get_event(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    event = create_response.json()

    response = client.get(
        f"/events/{event['id']}",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["id"] == event["id"]


def test_list_published_events(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/events",
        json=event_payload(
            title="KBR Published Event",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/events",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert any(
        event["title"] == "KBR Published Event"
        for event in data["items"]
    )


def test_search_events(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/events",
        json=event_payload(
            title="KBR Searchable Event",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/events",
        params={"search": "Searchable"},
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "KBR Searchable Event"


def test_upcoming_events_filter(
    client: TestClient,
    staff_user: User,
):
    upcoming_start = datetime.now(timezone.utc) + timedelta(days=10)
    upcoming_end = upcoming_start + timedelta(hours=2)

    client.post(
        "/events",
        json=event_payload(
            title="KBR Upcoming Event",
            start_at=upcoming_start,
            end_at=upcoming_end,
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/events",
        params={"upcoming": True},
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        event["title"] == "KBR Upcoming Event"
        for event in data["items"]
    )


def test_update_event(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.patch(
        f"/events/{event_id}",
        json={
            "title": "Updated KBR Event",
            "location": "Bizerte Marina",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated KBR Event"
    assert data["location"] == "Bizerte Marina"


def test_member_cannot_update_event(
    client: TestClient,
    staff_user: User,
    member_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.patch(
        f"/events/{event_id}",
        json={
            "title": "Unauthorized Update",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_delete_event(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/events/{event_id}",
        headers=auth_headers(client, staff_user),
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/events/{event_id}",
        headers=auth_headers(client, staff_user),
    )

    assert get_response.status_code == 404


def test_member_cannot_delete_event(
    client: TestClient,
    staff_user: User,
    member_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.delete(
        f"/events/{event_id}",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_get_missing_event_returns_404(
    client: TestClient,
    staff_user: User,
):
    response = client.get(
        "/events/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 404