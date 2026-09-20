from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.user_activity import UserActivity


def auth_headers(
    user: User,
) -> dict[str, str]:
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
    title: str = "KBR Audit News",
    slug: str = "kbr-audit-news",
    status: str = "draft",
) -> dict:
    return {
        "title": title,
        "slug": slug,
        "excerpt": "Audit test news excerpt.",
        "content": "Audit test news content.",
        "cover_image": (
            "https://example.com/news.jpg"
        ),
        "status": status,
    }


def get_news_audits(
    db: Session,
) -> list[UserActivity]:
    statement = (
        select(UserActivity)
        .where(
            UserActivity.resource_type == "news",
        )
        .order_by(
            UserActivity.occurred_at.asc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def test_news_creation_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 201

    news_id = response.json()["id"]

    audits = get_news_audits(db)

    business_audits = [
        audit
        for audit in audits
        if audit.action == "NEWS_CREATED"
    ]

    assert len(business_audits) == 1

    audit = business_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "news"
    assert str(audit.resource_id) == news_id
    assert audit.details == (
        'Created news article "KBR Audit News"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "KBR Audit News"
    )

    assert audit.activity_metadata["status"] == "draft"


def test_news_update_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.patch(
        f"/news/{news_id}",
        json={
            "title": "Updated KBR Audit News",
            "excerpt": "Updated excerpt.",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_news_audits(db)

    update_audits = [
        audit
        for audit in audits
        if audit.action == "NEWS_UPDATED"
    ]

    assert len(update_audits) == 1

    audit = update_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "news"
    assert str(audit.resource_id) == news_id
    assert audit.details == (
        'Updated news article "Updated KBR Audit News"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Updated KBR Audit News"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "excerpt",
        "title",
    ]

    assert audit.activity_metadata["changes"] == {
        "excerpt": {
            "from": "Audit test news excerpt.",
            "to": "Updated excerpt.",
        },
        "title": {
            "from": "KBR Audit News",
            "to": "Updated KBR Audit News",
        },
    }

    assert (
        audit.activity_metadata["previous_status"]
        == "draft"
    )

    assert (
        audit.activity_metadata["new_status"]
        == "draft"
    )


def test_news_publication_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="News To Publish",
            slug="news-to-publish",
            status="draft",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.patch(
        f"/news/{news_id}",
        json={
            "status": "published",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"
    assert response.json()["published_at"] is not None

    audits = get_news_audits(db)

    publication_audits = [
        audit
        for audit in audits
        if audit.action == "NEWS_PUBLISHED"
    ]

    assert len(publication_audits) == 1

    audit = publication_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "news"
    assert str(audit.resource_id) == news_id
    assert audit.details == (
        'Published news article "News To Publish"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "News To Publish"
    )

    assert (
        audit.activity_metadata["previous_status"]
        == "draft"
    )

    assert (
        audit.activity_metadata["new_status"]
        == "published"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "status",
    ]

    assert audit.activity_metadata["changes"] == {
        "status": {
            "from": "draft",
            "to": "published",
        },
    }


def test_news_unpublication_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="News To Unpublish",
            slug="news-to-unpublish",
            status="published",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.patch(
        f"/news/{news_id}",
        json={
            "status": "draft",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    assert response.json()["published_at"] is None

    audits = get_news_audits(db)

    unpublication_audits = [
        audit
        for audit in audits
        if audit.action == "NEWS_UNPUBLISHED"
    ]

    assert len(unpublication_audits) == 1

    audit = unpublication_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "news"
    assert str(audit.resource_id) == news_id
    assert audit.details == (
        'Unpublished news article "News To Unpublish"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "News To Unpublish"
    )

    assert (
        audit.activity_metadata["previous_status"]
        == "published"
    )

    assert (
        audit.activity_metadata["new_status"]
        == "draft"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "status",
    ]

    assert audit.activity_metadata["changes"] == {
        "status": {
            "from": "published",
            "to": "draft",
        },
    }


def test_news_deletion_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/news",
        json=news_payload(
            title="News To Delete",
            slug="news-to-delete",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    news_id = create_response.json()["id"]

    response = client.delete(
        f"/news/{news_id}",
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 204

    audits = get_news_audits(db)

    deletion_audits = [
        audit
        for audit in audits
        if audit.action == "NEWS_DELETED"
    ]

    assert len(deletion_audits) == 1

    audit = deletion_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "news"
    assert str(audit.resource_id) == news_id
    assert audit.details == (
        'Deleted news article "News To Delete"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "News To Delete"
    )


def test_news_created_with_published_status_creates_creation_audit(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    response = client.post(
        "/news",
        json=news_payload(
            title="Immediately Published News",
            slug="immediately-published-news",
            status="published",
        ),
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 201

    audits = get_news_audits(db)

    creation_audits = [
        audit
        for audit in audits
        if audit.action == "NEWS_CREATED"
    ]

    assert len(creation_audits) == 1

    audit = creation_audits[0]

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Immediately Published News"
    )

    assert (
        audit.activity_metadata["status"]
        == "published"
    )