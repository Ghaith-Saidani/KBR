from datetime import datetime, timedelta, timezone

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


def activity_payload(
    *,
    title: str = "KBR Audit Activity",
    slug: str = "kbr-audit-activity",
    status: str = "draft",
) -> dict:
    start_at = (
        datetime.now(timezone.utc)
        + timedelta(days=7)
    )
    end_at = start_at + timedelta(hours=2)

    return {
        "title": title,
        "slug": slug,
        "excerpt": "Audit test activity excerpt.",
        "description": "Audit test activity description.",
        "cover_image": (
            "https://example.com/activity.jpg"
        ),
        "status": status,
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "location": "Bizerte",
    }


def get_activity_audits(
    db: Session,
) -> list[UserActivity]:
    statement = (
        select(UserActivity)
        .where(
            UserActivity.resource_type == "activity",
        )
        .order_by(
            UserActivity.occurred_at.asc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def test_activity_creation_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 201

    activity_id = response.json()["id"]

    audits = get_activity_audits(db)

    creation_audits = [
        audit
        for audit in audits
        if audit.action == "ACTIVITY_CREATED"
    ]

    assert len(creation_audits) == 1

    audit = creation_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "activity"
    assert str(audit.resource_id) == activity_id
    assert audit.details == (
        'Created activity "KBR Audit Activity"'
    )
    assert audit.activity_metadata is not None
    assert (
        audit.activity_metadata["resource_name"]
        == "KBR Audit Activity"
    )
    assert audit.activity_metadata["status"] == "draft"


def test_activity_update_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "title": "Updated KBR Audit Activity",
            "location": "Bizerte Marina",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_activity_audits(db)

    update_audits = [
        audit
        for audit in audits
        if audit.action == "ACTIVITY_UPDATED"
    ]

    assert len(update_audits) == 1

    audit = update_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "activity"
    assert str(audit.resource_id) == activity_id
    assert audit.details == (
        'Updated activity "Updated KBR Audit Activity"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Updated KBR Audit Activity"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "location",
        "title",
    ]

    assert audit.activity_metadata["changes"] == {
        "location": {
            "from": "Bizerte",
            "to": "Bizerte Marina",
        },
        "title": {
            "from": "KBR Audit Activity",
            "to": "Updated KBR Audit Activity",
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


def test_activity_publication_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(
            title="Activity To Publish",
            slug="activity-to-publish",
            status="draft",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "status": "published",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"
    assert response.json()["published_at"] is not None

    audits = get_activity_audits(db)

    publication_audits = [
        audit
        for audit in audits
        if audit.action == "ACTIVITY_PUBLISHED"
    ]

    assert len(publication_audits) == 1

    audit = publication_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "activity"
    assert str(audit.resource_id) == activity_id
    assert audit.details == (
        'Published activity "Activity To Publish"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Activity To Publish"
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


def test_activity_deletion_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/activities",
        json=activity_payload(
            title="Activity To Delete",
            slug="activity-to-delete",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.delete(
        f"/activities/{activity_id}",
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 204

    audits = get_activity_audits(db)

    deletion_audits = [
        audit
        for audit in audits
        if audit.action == "ACTIVITY_DELETED"
    ]

    assert len(deletion_audits) == 1

    audit = deletion_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "activity"
    assert str(audit.resource_id) == activity_id
    assert audit.details == (
        'Deleted activity "Activity To Delete"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Activity To Delete"
    )


def test_published_activity_creation_creates_creation_audit(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    response = client.post(
        "/activities",
        json=activity_payload(
            title="Immediately Published Activity",
            slug="immediately-published-activity",
            status="published",
        ),
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 201

    audits = get_activity_audits(db)

    creation_audits = [
        audit
        for audit in audits
        if audit.action == "ACTIVITY_CREATED"
    ]

    assert len(creation_audits) == 1

    audit = creation_audits[0]

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Immediately Published Activity"
    )

    assert (
        audit.activity_metadata["status"]
        == "published"
    )