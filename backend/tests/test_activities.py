from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User


def auth_headers(
    client: TestClient,
    user: User,
) -> dict[str, str]:
    """
    Authenticate a test user and return Authorization headers.
    """

    from backend.app.core.security import create_access_token

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def activity_payload(
    *,
    title: str = "KBR Test Activity",
    slug: str = "kbr-test-activity",
    status: str = "published",
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict:
    """
    Build a valid activity payload.
    """

    if start_at is None:
        start_at = datetime.now(timezone.utc) + timedelta(days=7)

    if end_at is None:
        end_at = start_at + timedelta(hours=2)

    return {
        "title": title,
        "slug": slug,
        "excerpt": "Test activity excerpt.",
        "description": "Test activity description for KBR.",
        "cover_image": "https://example.com/kbr-activity.jpg",
        "status": status,
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "location": "Bizerte",
    }


def test_list_activities_is_public(
    client: TestClient,
):
    response = client.get("/activities")

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data


def test_create_activity_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/activities",
        json=activity_payload(),
    )

    assert response.status_code == 401


def test_member_cannot_create_activity(
    client: TestClient,
    member_user: User,
):
    response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_staff_can_create_activity(
    client: TestClient,
    staff_user: User,
):
    response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "KBR Test Activity"
    assert data["slug"] == "kbr-test-activity"
    assert data["description"] == "Test activity description for KBR."
    assert data["location"] == "Bizerte"
    assert data["status"] == "published"
    assert data["created_by"] == str(staff_user.id)


def test_admin_can_create_activity(
    client: TestClient,
    admin_user: User,
):
    response = client.post(
        "/activities",
        json=activity_payload(
            title="KBR Admin Activity",
            slug="kbr-admin-activity",
        ),
        headers=auth_headers(client, admin_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "KBR Admin Activity"
    assert data["created_by"] == str(admin_user.id)


def test_get_activity(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity = create_response.json()

    response = client.get(
        f"/activities/{activity['id']}",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["id"] == activity["id"]


def test_get_activity_by_slug(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/activities",
        json=activity_payload(
            slug="community-cleanup",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/activities/slug/community-cleanup",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "community-cleanup"


def test_list_published_activities(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/activities",
        json=activity_payload(
            title="KBR Published Activity",
            slug="kbr-published-activity",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/activities",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert any(
        activity["title"] == "KBR Published Activity"
        for activity in data["items"]
    )


def test_draft_activity_is_not_publicly_visible(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(
            title="KBR Draft Activity",
            slug="kbr-draft-activity",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    response = client.get(
        "/activities",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert not any(
        activity["slug"] == "kbr-draft-activity"
        for activity in data["items"]
    )


def test_draft_activity_not_available_by_slug(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/activities",
        json=activity_payload(
            title="KBR Hidden Draft",
            slug="kbr-hidden-draft",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/activities/slug/kbr-hidden-draft",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 404


def test_search_activities(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/activities",
        json=activity_payload(
            title="KBR Community Cleanup",
            slug="kbr-community-cleanup",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/activities",
        params={"search": "Community"},
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "KBR Community Cleanup"


def test_upcoming_activity(
    client: TestClient,
    staff_user: User,
):
    upcoming_start = datetime.now(timezone.utc) + timedelta(days=10)
    upcoming_end = upcoming_start + timedelta(hours=2)

    client.post(
        "/activities",
        json=activity_payload(
            title="KBR Upcoming Activity",
            slug="kbr-upcoming-activity",
            start_at=upcoming_start,
            end_at=upcoming_end,
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/activities",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        activity["title"] == "KBR Upcoming Activity"
        for activity in data["items"]
    )


def test_update_activity(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "title": "Updated KBR Activity",
            "location": "Bizerte Marina",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated KBR Activity"
    assert data["location"] == "Bizerte Marina"


def test_member_cannot_update_activity(
    client: TestClient,
    staff_user: User,
    member_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "title": "Unauthorized Update",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_delete_activity(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/activities/{activity_id}",
        headers=auth_headers(client, staff_user),
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/activities/{activity_id}",
        headers=auth_headers(client, staff_user),
    )

    assert get_response.status_code == 404


def test_member_cannot_delete_activity(
    client: TestClient,
    staff_user: User,
    member_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.delete(
        f"/activities/{activity_id}",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_get_missing_activity_returns_404(
    client: TestClient,
    staff_user: User,
):
    response = client.get(
        "/activities/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 404


def test_duplicate_activity_slug_is_rejected(
    client: TestClient,
    staff_user: User,
):
    first_response = client.post(
        "/activities",
        json=activity_payload(
            slug="duplicate-activity",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/activities",
        json=activity_payload(
            title="Another Activity",
            slug="duplicate-activity",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert second_response.status_code == 409


def test_draft_activity_has_no_published_at(
    client: TestClient,
    staff_user: User,
):
    response = client.post(
        "/activities",
        json=activity_payload(
            title="Draft Activity",
            slug="draft-activity",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201
    assert response.json()["published_at"] is None


def test_publishing_draft_sets_published_at(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(
            title="Activity To Publish",
            slug="activity-to-publish",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201
    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "status": "published",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"
    assert response.json()["published_at"] is not None


def test_unpublishing_activity_clears_published_at(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(
            title="Activity To Unpublish",
            slug="activity-to-unpublish",
            status="published",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    assert create_response.json()["published_at"] is not None

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "status": "draft",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    assert response.json()["published_at"] is None


def test_explicit_published_at_is_preserved(
    client: TestClient,
    staff_user: User,
):
    published_at = datetime.now(timezone.utc) - timedelta(days=2)

    response = client.post(
        "/activities",
        json={
            **activity_payload(
                title="Historical Activity",
                slug="historical-activity",
            ),
            "published_at": published_at.isoformat(),
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201

    returned_published_at = datetime.fromisoformat(
        response.json()["published_at"]
    )

    assert abs(
        (returned_published_at - published_at).total_seconds()
    ) < 2


def test_update_slug_is_normalized(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(
            slug="original-activity",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "slug": " UPDATED-ACTIVITY ",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "updated-activity"


def test_update_slug_conflict_returns_409(
    client: TestClient,
    staff_user: User,
):
    first_response = client.post(
        "/activities",
        json=activity_payload(
            title="First Activity",
            slug="first-activity",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/activities",
        json=activity_payload(
            title="Second Activity",
            slug="second-activity",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert second_response.status_code == 201

    second_id = second_response.json()["id"]

    response = client.patch(
        f"/activities/{second_id}",
        json={
            "slug": "first-activity",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 409


def test_end_at_before_start_at_is_rejected(
    client: TestClient,
    staff_user: User,
):
    start_at = datetime.now(timezone.utc) + timedelta(days=5)
    end_at = start_at - timedelta(hours=1)

    response = client.post(
        "/activities",
        json=activity_payload(
            title="Invalid Activity",
            slug="invalid-activity",
            start_at=start_at,
            end_at=end_at,
        ),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 422


def test_published_activities_are_ordered_newest_first(
    client: TestClient,
    staff_user: User,
):
    older = datetime.now(timezone.utc) - timedelta(days=5)
    newer = datetime.now(timezone.utc) - timedelta(days=1)

    client.post(
        "/activities",
        json=activity_payload(
            title="Older Activity",
            slug="older-activity",
            start_at=older,
            end_at=older + timedelta(hours=2),
        ),
        headers=auth_headers(client, staff_user),
    )

    client.post(
        "/activities",
        json=activity_payload(
            title="Newer Activity",
            slug="newer-activity",
            start_at=newer,
            end_at=newer + timedelta(hours=2),
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/activities",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    items = response.json()["items"]

    titles = [activity["title"] for activity in items]

    assert titles.index("Newer Activity") < titles.index("Older Activity")
