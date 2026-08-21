from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.member import Member, MemberStatus
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


def create_test_member(
    db: Session,
    user: User,
    *,
    first_name: str = "John",
    last_name: str = "Doe",
    slug: str = "john-doe",
    position: str | None = "Member",
    phone: str | None = "+21612345678",
    profile_image: str | None = (
        "https://example.com/profile.jpg"
    ),
    bio: str | None = "KBR test member.",
    joined_at: date | None = date(2026, 1, 15),
    status: MemberStatus = MemberStatus.ACTIVE,
) -> Member:
    """
    Create a member profile directly in the database.
    """

    member = Member(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        slug=slug,
        position=position,
        phone=phone,
        profile_image=profile_image,
        bio=bio,
        joined_at=joined_at,
        status=status,
    )

    db.add(member)
    db.flush()

    return member


def test_list_members(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.get("/members")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "John"
    assert data["items"][0]["last_name"] == "Doe"
    assert data["items"][0]["slug"] == "john-doe"


def test_list_members_does_not_expose_private_fields(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.get("/members")

    assert response.status_code == 200

    member = response.json()["items"][0]

    assert "user_id" not in member
    assert "phone" not in member
    assert "email" not in member


def test_get_member_by_id(
    client: TestClient,
    db: Session,
    member_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.get(
        f"/members/{member.id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(member.id)
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["slug"] == "john-doe"


def test_get_member_by_slug(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        slug="john-doe-test",
    )

    response = client.get(
        "/members/slug/john-doe-test",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["slug"] == "john-doe-test"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"


def test_get_missing_member_returns_404(
    client: TestClient,
):
    response = client.get(
        "/members/00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404


def test_get_missing_member_by_slug_returns_404(
    client: TestClient,
):
    response = client.get(
        "/members/slug/does-not-exist",
    )

    assert response.status_code == 404


def test_member_can_get_own_profile(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.get(
        "/members/me",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == str(member_user.id)
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["phone"] == "+21612345678"


def test_member_profile_requires_authentication(
    client: TestClient,
):
    response = client.get("/members/me")

    assert response.status_code == 401


def test_member_without_profile_gets_404(
    client: TestClient,
    member_user: User,
):
    response = client.get(
        "/members/me",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 404


def test_member_can_update_own_profile(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "Jane",
            "position": "Community Manager",
            "bio": "Updated KBR profile.",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["position"] == "Community Manager"
    assert data["bio"] == "Updated KBR profile."
    assert data["slug"] == "jane-doe"


def test_member_update_normalizes_name(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "  Jane  ",
            "last_name": "  Smith  ",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert data["slug"] == "jane-smith"


def test_member_update_normalizes_optional_strings(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "position": "  President  ",
            "phone": "  +21698765432  ",
            "bio": "  Updated biography.  ",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["position"] == "President"
    assert data["phone"] == "+21698765432"
    assert data["bio"] == "Updated biography."


def test_member_can_clear_optional_fields(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "position": None,
            "phone": None,
            "profile_image": None,
            "bio": None,
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["position"] is None
    assert data["phone"] is None
    assert data["profile_image"] is None
    assert data["bio"] is None


def test_member_cannot_change_own_status(
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
            "status": "archived",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "active"
    assert data["id"] == str(member.id)


def test_staff_can_update_member(
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
            "status": "inactive",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["position"] == "Staff Coordinator"
    assert data["status"] == "inactive"


def test_admin_can_update_member(
    client: TestClient,
    db: Session,
    member_user: User,
    admin_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        f"/members/{member.id}",
        json={
            "position": "Administrator",
            "status": "active",
        },
        headers=auth_headers(client, admin_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["position"] == "Administrator"
    assert data["status"] == "active"


def test_member_cannot_update_another_member(
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
            "position": "Unauthorized",
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200


def test_regular_member_cannot_update_member(
    client: TestClient,
    db: Session,
    member_user: User,
):
    another_user = User(
        email="another-member@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    db.add(another_user)
    db.flush()

    member = create_test_member(
        db,
        another_user,
        slug="another-member",
    )

    response = client.patch(
        f"/members/{member.id}",
        json={
            "position": "Unauthorized",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_staff_cannot_delete_member(
    client: TestClient,
    db: Session,
    member_user: User,
    staff_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.delete(
        f"/members/{member.id}",
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 403


def test_admin_can_delete_member(
    client: TestClient,
    db: Session,
    member_user: User,
    admin_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.delete(
        f"/members/{member.id}",
        headers=auth_headers(client, admin_user),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/members/{member.id}",
    )

    assert get_response.status_code == 404

    user = db.get(User, member_user.id)

    assert user is not None


def test_member_delete_requires_admin(
    client: TestClient,
    db: Session,
    member_user: User,
):
    member = create_test_member(
        db,
        member_user,
    )

    response = client.delete(
        f"/members/{member.id}",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 403


def test_search_members_by_first_name(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="Alice",
        last_name="Johnson",
        slug="alice-johnson",
    )

    response = client.get(
        "/members",
        params={"search": "Alice"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["first_name"] == "Alice"


def test_search_members_by_last_name(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="Alice",
        last_name="Johnson",
        slug="alice-johnson",
    )

    response = client.get(
        "/members",
        params={"search": "Johnson"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["last_name"] == "Johnson"


def test_search_members_by_position(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        position="Event Coordinator",
    )

    response = client.get(
        "/members",
        params={"search": "Coordinator"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["position"] == "Event Coordinator"


def test_search_members_by_bio(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        bio="Passionate about community development.",
    )

    response = client.get(
        "/members",
        params={"search": "community"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1


def test_archived_members_are_hidden_from_default_list(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        slug="archived-member",
        status=MemberStatus.ARCHIVED,
    )

    response = client.get("/members")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []


def test_inactive_members_are_visible(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        slug="inactive-member",
        status=MemberStatus.INACTIVE,
    )

    response = client.get("/members")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "inactive"


def test_filter_members_by_status(
    client: TestClient,
    db: Session,
    member_user: User,
):
    active_user = member_user

    inactive_user = User(
        email="inactive@example.com",
        password_hash="test-password-hash",
        role=active_user.role,
        status=active_user.status,
        is_email_verified=True,
    )

    db.add(inactive_user)
    db.flush()

    create_test_member(
        db,
        active_user,
        first_name="Active",
        last_name="Member",
        slug="active-member",
        status=MemberStatus.ACTIVE,
    )

    create_test_member(
        db,
        inactive_user,
        first_name="Inactive",
        last_name="Member",
        slug="inactive-member",
        status=MemberStatus.INACTIVE,
    )

    response = client.get(
        "/members",
        params={"status": "inactive"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["first_name"] == "Inactive"
    assert data["items"][0]["status"] == "inactive"


def test_member_list_pagination(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="Alice",
        last_name="Member",
        slug="alice-member",
    )

    user_two = User(
        email="member-two@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    user_three = User(
        email="member-three@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    db.add_all([user_two, user_three])
    db.flush()

    create_test_member(
        db,
        user_two,
        first_name="Bob",
        last_name="Member",
        slug="bob-member",
    )

    create_test_member(
        db,
        user_three,
        first_name="Charlie",
        last_name="Member",
        slug="charlie-member",
    )

    response = client.get(
        "/members",
        params={
            "skip": 1,
            "limit": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Bob"


def test_member_names_are_sorted(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="Zoe",
        last_name="Member",
        slug="zoe-member",
    )

    user_two = User(
        email="alice@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    user_three = User(
        email="michael@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    db.add_all([user_two, user_three])
    db.flush()

    create_test_member(
        db,
        user_two,
        first_name="Alice",
        last_name="Member",
        slug="alice-member",
    )

    create_test_member(
        db,
        user_three,
        first_name="Michael",
        last_name="Member",
        slug="michael-member",
    )

    response = client.get("/members")

    assert response.status_code == 200

    items = response.json()["items"]

    names = [
        item["first_name"]
        for item in items
    ]

    assert names == [
        "Alice",
        "Michael",
        "Zoe",
    ]


def test_member_slug_is_generated_when_name_changes(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="John",
        last_name="Doe",
        slug="john-doe",
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "Ghaith",
            "last_name": "Saidani",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Ghaith"
    assert data["last_name"] == "Saidani"
    assert data["slug"] == "ghaith-saidani"


def test_member_slug_handles_accents(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="José",
        last_name="García",
        slug="jose-garcia",
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "Élodie",
            "last_name": "Müller",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["slug"] == "elodie-muller"


def test_duplicate_member_slug_is_rejected(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="John",
        last_name="Doe",
        slug="john-doe",
    )

    second_user = User(
        email="second@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    db.add(second_user)
    db.flush()

    duplicate_member = Member(
        user_id=second_user.id,
        first_name="Jane",
        last_name="Smith",
        slug="john-doe",
    )

    db.add(duplicate_member)

    try:
        db.flush()
    except Exception:
        db.rollback()
        return

    raise AssertionError(
        "Duplicate member slug should violate the unique constraint."
    )


def test_duplicate_slug_is_automatically_resolved_on_name_change(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
        first_name="John",
        last_name="Doe",
        slug="john-doe",
    )

    second_user = User(
        email="second-john@example.com",
        password_hash="test-password-hash",
        role=member_user.role,
        status=member_user.status,
        is_email_verified=True,
    )

    db.add(second_user)
    db.flush()

    create_test_member(
        db,
        second_user,
        first_name="Jane",
        last_name="Smith",
        slug="jane-smith",
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "John",
            "last_name": "Doe",
        },
        headers=auth_headers(client, second_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["slug"] == "john-doe-2"


def test_member_update_validation_rejects_empty_first_name(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "first_name": "   ",
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 422


def test_member_update_validation_rejects_too_long_bio(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.patch(
        "/members/me",
        json={
            "bio": "a" * 2001,
        },
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 422


def test_staff_cannot_change_member_user_id(
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
            "user_id": str(staff_user.id),
        },
        headers=auth_headers(client, staff_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == str(member_user.id)


def test_member_created_at_and_updated_at_exist(
    client: TestClient,
    db: Session,
    member_user: User,
):
    create_test_member(
        db,
        member_user,
    )

    response = client.get(
        "/members/me",
        headers=auth_headers(client, member_user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["created_at"] is not None
    assert data["updated_at"] is not None