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


def event_payload(
    *,
    title: str = "KBR Audit Event",
    status: str = "draft",
) -> dict:
    start_at = (
        datetime.now(timezone.utc)
        + timedelta(days=7)
    )

    end_at = start_at + timedelta(hours=2)

    return {
        "title": title,
        "description": "Event used for audit testing.",
        "location": "Bizerte",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "cover_image": "https://example.com/event.jpg",
        "status": status,
    }


def get_event_audits(
    db: Session,
) -> list[UserActivity]:
    statement = (
        select(UserActivity)
        .where(
            UserActivity.resource_type == "event",
        )
        .order_by(
            UserActivity.occurred_at.asc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def test_event_creation_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 201

    event_id = response.json()["id"]

    audits = get_event_audits(db)

    business_audits = [
        audit
        for audit in audits
        if audit.action == "EVENT_CREATED"
    ]

    assert len(business_audits) == 1

    audit = business_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "event"
    assert str(audit.resource_id) == event_id
    assert audit.details == "Event created"
    assert audit.activity_metadata is not None
    assert audit.activity_metadata["status"] == "draft"


def test_event_update_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.patch(
        f"/events/{event_id}",
        json={
            "title": "Updated KBR Event",
            "location": "Bizerte Marina",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_event_audits(db)

    business_audits = [
        audit
        for audit in audits
        if audit.action == "EVENT_UPDATED"
    ]

    assert len(business_audits) == 1

    audit = business_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "event"
    assert str(audit.resource_id) == event_id
    assert audit.details == "Event updated"
    assert audit.activity_metadata is not None
    assert set(
        audit.activity_metadata["changed_fields"]
    ) == {
        "title",
        "location",
    }
    assert (
        audit.activity_metadata["previous_status"]
        == "draft"
    )
    assert (
        audit.activity_metadata["new_status"]
        == "draft"
    )


def test_event_publication_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(
            title="Event To Publish",
            status="draft",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.patch(
        f"/events/{event_id}",
        json={
            "status": "published",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_event_audits(db)

    publication_audits = [
        audit
        for audit in audits
        if audit.action == "EVENT_PUBLISHED"
    ]

    assert len(publication_audits) == 1

    audit = publication_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "event"
    assert str(audit.resource_id) == event_id
    assert audit.details == "Event published"
    assert audit.activity_metadata is not None
    assert (
        audit.activity_metadata["previous_status"]
        == "draft"
    )
    assert (
        audit.activity_metadata["new_status"]
        == "published"
    )


def test_event_cancellation_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(
            title="Event To Cancel",
            status="published",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.patch(
        f"/events/{event_id}",
        json={
            "status": "cancelled",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_event_audits(db)

    cancellation_audits = [
        audit
        for audit in audits
        if audit.action == "EVENT_CANCELLED"
    ]

    assert len(cancellation_audits) == 1

    audit = cancellation_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "event"
    assert str(audit.resource_id) == event_id
    assert audit.details == "Event cancelled"
    assert audit.activity_metadata is not None
    assert (
        audit.activity_metadata["previous_status"]
        == "published"
    )
    assert (
        audit.activity_metadata["new_status"]
        == "cancelled"
    )


def test_event_deletion_creates_business_audit_event(
    client: TestClient,
    db: Session,
    staff_user: User,
):
    create_response = client.post(
        "/events",
        json=event_payload(
            title="Event To Delete",
        ),
        headers=auth_headers(staff_user),
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.delete(
        f"/events/{event_id}",
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 204

    audits = get_event_audits(db)

    deletion_audits = [
        audit
        for audit in audits
        if audit.action == "EVENT_DELETED"
    ]

    assert len(deletion_audits) == 1

    audit = deletion_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "event"
    assert str(audit.resource_id) == event_id
    assert audit.details == "Event deleted"
    assert audit.activity_metadata is not None
    assert (
        audit.activity_metadata["title"]
        == "Event To Delete"
    )