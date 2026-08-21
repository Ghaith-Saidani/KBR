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


def news_payload(
    *,
    title: str = "KBR Test News",
    slug: str = "kbr-test-news",
    status: str = "published",
    published_at: datetime | None = None,
) -> dict:
    """
    Build a valid news article payload.
    """

    payload = {
        "title": title,
        "slug": slug,
        "excerpt": "Test news article for KBR.",
        "content": "This is test news content for KBR.",
        "cover_image": "https://example.com/kbr-news.jpg",
        "status": status,
    }

    if published_at is not None:
        payload["published_at"] = published_at.isoformat()

    return payload


def test_list_news_requires_authentication(
    client: TestClient,
):
    response = client.get("/news")

    assert response.status_code == 401


def test_create_news_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/news",
        json=news_payload(),
    )

    assert response.status_code == 401


def test_member_cannot_create_news(
    client: TestClient,
    member_user: User,
):
    response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_staff_can_create_news(
    client: TestClient,
    staff_user: User,
):
    response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "KBR Test News"
    assert data["slug"] == "kbr-test-news"
    assert data["status"] == "published"
    assert data["published_at"] is not None
    assert data["created_by"] == str(staff_user.id)


def test_admin_can_create_news(
    client: TestClient,
    admin_user: User,
):
    response = client.post(
        "/news",
        json=news_payload(
            title="KBR Admin News",
            slug="kbr-admin-news",
        ),
        headers=auth_headers(client, admin_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "KBR Admin News"
    assert data["created_by"] == str(admin_user.id)


def test_get_news(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news = create_response.json()

    response = client.get(
        f"/news/{news['id']}",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200
    assert response.json()["id"] == news["id"]


def test_get_news_by_slug(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/news/slug/kbr-test-news",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["slug"] == "kbr-test-news"
    assert data["title"] == "KBR Test News"


def test_list_published_news(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/news",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    assert any(
        article["slug"] == "kbr-test-news"
        for article in data["items"]
    )


def test_draft_news_is_not_publicly_visible(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="KBR Draft News",
            slug="kbr-draft-news",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    response = client.get(
        "/news",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert not any(
        article["slug"] == "kbr-draft-news"
        for article in data["items"]
    )


def test_draft_news_not_available_by_slug(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/news",
        json=news_payload(
            title="KBR Draft News",
            slug="kbr-draft-news",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/news/slug/kbr-draft-news",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 404


def test_search_news(
    client: TestClient,
    staff_user: User,
):
    client.post(
        "/news",
        json=news_payload(
            title="KBR Searchable Article",
            slug="kbr-searchable-article",
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/news",
        params={"search": "Searchable"},
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "KBR Searchable Article"


def test_update_news(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.patch(
        f"/news/{news_id}",
        json={
            "title": "Updated KBR News",
            "excerpt": "Updated excerpt.",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated KBR News"
    assert data["excerpt"] == "Updated excerpt."
    assert data["content"] == "This is test news content for KBR."


def test_member_cannot_update_news(
    client: TestClient,
    staff_user: User,
    member_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.patch(
        f"/news/{news_id}",
        json={
            "title": "Unauthorized Update",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_delete_news(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/news/{news_id}",
        headers=auth_headers(client, staff_user),
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/news/{news_id}",
        headers=auth_headers(client, staff_user),
    )

    assert get_response.status_code == 404


def test_member_cannot_delete_news(
    client: TestClient,
    staff_user: User,
    member_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.delete(
        f"/news/{news_id}",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_get_missing_news_returns_404(
    client: TestClient,
    staff_user: User,
):
    response = client.get(
        "/news/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 404


def test_duplicate_news_slug_is_rejected(
    client: TestClient,
    staff_user: User,
):
    first_response = client.post(
        "/news",
        json=news_payload(
            title="First Article",
            slug="duplicate-slug",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/news",
        json=news_payload(
            title="Second Article",
            slug="duplicate-slug",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "A news article with this slug already exists."
    )


# ---------------------------------------------------------------------------
# Publication lifecycle tests
# ---------------------------------------------------------------------------


def test_draft_news_has_no_published_at(
    client: TestClient,
    staff_user: User,
):
    response = client.post(
        "/news",
        json=news_payload(
            title="KBR Draft Lifecycle",
            slug="kbr-draft-lifecycle",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "draft"
    assert data["published_at"] is None


def test_publishing_draft_sets_published_at(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="KBR Publish Lifecycle",
            slug="kbr-publish-lifecycle",
            status="draft",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    assert create_response.json()["published_at"] is None

    before_publish = datetime.now(timezone.utc)

    update_response = client.patch(
        f"/news/{news_id}",
        json={
            "status": "published",
        },
        headers=auth_headers(client, staff_user),
    )

    after_publish = datetime.now(timezone.utc)

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["status"] == "published"
    assert data["published_at"] is not None

    published_at = datetime.fromisoformat(
        data["published_at"],
    )

    assert before_publish <= published_at <= after_publish


def test_unpublishing_news_clears_published_at(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="KBR Unpublish Lifecycle",
            slug="kbr-unpublish-lifecycle",
            status="published",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    assert create_response.json()["published_at"] is not None

    response = client.patch(
        f"/news/{news_id}",
        json={
            "status": "draft",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "draft"
    assert data["published_at"] is None


def test_explicit_published_at_is_preserved(
    client: TestClient,
    staff_user: User,
):
    publication_date = (
        datetime.now(timezone.utc)
        - timedelta(days=30)
    )

    response = client.post(
        "/news",
        json=news_payload(
            title="KBR Historical Article",
            slug="kbr-historical-article",
            status="published",
            published_at=publication_date,
        ),
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 201

    data = response.json()

    actual_published_at = datetime.fromisoformat(
        data["published_at"],
    )

    assert abs(
        (
            actual_published_at
            - publication_date
        ).total_seconds()
    ) < 1


def test_update_slug_is_normalized(
    client: TestClient,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="KBR Slug Update",
            slug="kbr-slug-update",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.patch(
        f"/news/{news_id}",
        json={
            "slug": "  KBR-UPDATED-SLUG  ",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    assert response.json()["slug"] == "kbr-updated-slug"


def test_update_slug_conflict_returns_409(
    client: TestClient,
    staff_user: User,
):
    first_response = client.post(
        "/news",
        json=news_payload(
            title="First Article",
            slug="first-article",
        ),
        headers=auth_headers(client, staff_user),
    )

    second_response = client.post(
        "/news",
        json=news_payload(
            title="Second Article",
            slug="second-article",
        ),
        headers=auth_headers(client, staff_user),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    second_id = second_response.json()["id"]

    response = client.patch(
        f"/news/{second_id}",
        json={
            "slug": "first-article",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "A news article with this slug already exists."
    )


def test_published_news_are_ordered_newest_first(
    client: TestClient,
    staff_user: User,
):
    older_date = (
        datetime.now(timezone.utc)
        - timedelta(days=10)
    )

    newer_date = (
        datetime.now(timezone.utc)
        - timedelta(days=1)
    )

    client.post(
        "/news",
        json=news_payload(
            title="Older KBR News",
            slug="older-kbr-news",
            published_at=older_date,
        ),
        headers=auth_headers(client, staff_user),
    )

    client.post(
        "/news",
        json=news_payload(
            title="Newer KBR News",
            slug="newer-kbr-news",
            published_at=newer_date,
        ),
        headers=auth_headers(client, staff_user),
    )

    response = client.get(
        "/news",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    items = response.json()["items"]

    newer_index = next(
        index
        for index, item in enumerate(items)
        if item["slug"] == "newer-kbr-news"
    )

    older_index = next(
        index
        for index, item in enumerate(items)
        if item["slug"] == "older-kbr-news"
    )

    assert newer_index < older_index