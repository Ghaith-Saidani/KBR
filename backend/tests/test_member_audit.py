from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.member import Member, MemberStatus
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


def create_test_member(
    db: Session,
    user: User,
    *,
    slug: str = "john-doe",
    status: MemberStatus = MemberStatus.ACTIVE,
) -> Member:
    member = Member(
        user_id=user.id,
        first_name="John",
        last_name="Doe",
        slug=slug,
        position="Member",
        phone="+21612345678",
        profile_image="https://example.com/profile.jpg",
        bio="KBR test member.",
        joined_at=date(2026, 1, 15),
        status=status,
    )

    db.add(member)
    db.flush()

    return member


def get_member_audits(
    db: Session,
) -> list[UserActivity]:
    statement = (
        select(UserActivity)
        .where(
            UserActivity.resource_type == "member",
        )
        .order_by(
            UserActivity.occurred_at.asc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def test_member_update_creates_business_audit_event(
    client: TestClient,
    db: Session,
    member_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "Jane",
            "position": "Community Manager",
        },
        headers=auth_headers(member_user),
    )

    assert response.status_code == 200

    audits = get_member_audits(db)

    business_audits = [
        audit
        for audit in audits
        if audit.action == "MEMBER_UPDATED"
    ]

    assert len(business_audits) == 1

    audit = business_audits[0]

    assert audit.user_id == member_user.id
    assert audit.resource_type == "member"
    assert audit.resource_id == member.id
    assert audit.details == (
        'Updated member "Jane Doe"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "Jane Doe"
    )

    assert (
        audit.activity_metadata["actor_type"]
        == "member"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "first_name",
        "position",
    ]

    assert audit.activity_metadata["changes"] == {
        "first_name": {
            "from": "John",
            "to": "Jane",
        },
        "position": {
            "from": "Member",
            "to": "Community Manager",
        },
    }


def test_staff_member_update_creates_business_audit_event(
    client: TestClient,
    db: Session,
    member_user: User,
    staff_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        f"/members/{member.id}",
        json={
            "position": "Staff Coordinator",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_member_audits(db)

    business_audits = [
        audit
        for audit in audits
        if audit.action == "MEMBER_UPDATED"
    ]

    assert len(business_audits) == 1

    audit = business_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "member"
    assert audit.resource_id == member.id
    assert audit.details == (
        'Updated member "John Doe"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "John Doe"
    )

    assert (
        audit.activity_metadata["actor_type"]
        == "staff_or_admin"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "position",
    ]

    assert audit.activity_metadata["changes"] == {
        "position": {
            "from": "Member",
            "to": "Staff Coordinator",
        },
    }


def test_member_status_change_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    member_user: User,
    staff_user: User,
):
    member = create_test_member(
        db,
        member_user,
        status=MemberStatus.ACTIVE,
    )

    response = client.patch(
        f"/members/{member.id}",
        json={
            "status": "inactive",
        },
        headers=auth_headers(staff_user),
    )

    assert response.status_code == 200

    audits = get_member_audits(db)

    status_audits = [
        audit
        for audit in audits
        if audit.action == "MEMBER_DEACTIVATED"
    ]

    assert len(status_audits) == 1

    audit = status_audits[0]

    assert audit.user_id == staff_user.id
    assert audit.resource_type == "member"
    assert audit.resource_id == member.id
    assert audit.details == (
        'Deactivated member "John Doe"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "John Doe"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "status",
    ]

    assert audit.activity_metadata["changes"] == {
        "status": {
            "from": "active",
            "to": "inactive",
        },
    }

    assert (
        audit.activity_metadata["previous_status"]
        == "active"
    )

    assert (
        audit.activity_metadata["new_status"]
        == "inactive"
    )


def test_member_reactivation_creates_semantic_audit_event(
    client: TestClient,
    db: Session,
    member_user: User,
    admin_user: User,
):
    member = create_test_member(
        db,
        member_user,
        status=MemberStatus.INACTIVE,
    )

    response = client.patch(
        f"/members/{member.id}",
        json={
            "status": "active",
        },
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200

    audits = get_member_audits(db)

    status_audits = [
        audit
        for audit in audits
        if audit.action == "MEMBER_REACTIVATED"
    ]

    assert len(status_audits) == 1

    audit = status_audits[0]

    assert audit.user_id == admin_user.id
    assert audit.resource_type == "member"
    assert audit.resource_id == member.id
    assert audit.details == (
        'Reactivated member "John Doe"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "John Doe"
    )

    assert audit.activity_metadata["changed_fields"] == [
        "status",
    ]

    assert audit.activity_metadata["changes"] == {
        "status": {
            "from": "inactive",
            "to": "active",
        },
    }

    assert (
        audit.activity_metadata["previous_status"]
        == "inactive"
    )

    assert (
        audit.activity_metadata["new_status"]
        == "active"
    )


def test_admin_member_delete_creates_business_audit_event(
    client: TestClient,
    db: Session,
    member_user: User,
    admin_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    member_id = member.id

    response = client.delete(
        f"/members/{member_id}",
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 204

    audits = get_member_audits(db)

    business_audits = [
        audit
        for audit in audits
        if audit.action == "MEMBER_DELETED"
    ]

    assert len(business_audits) == 1

    audit = business_audits[0]

    assert audit.user_id == admin_user.id
    assert audit.resource_type == "member"
    assert audit.resource_id == member_id
    assert audit.details == (
        'Deleted member "John Doe"'
    )

    assert audit.activity_metadata is not None

    assert (
        audit.activity_metadata["resource_name"]
        == "John Doe"
    )

    assert (
        audit.activity_metadata["actor_type"]
        == "admin"
    )

    assert (
        audit.activity_metadata["affected_user_id"]
        == str(member_user.id)
    )