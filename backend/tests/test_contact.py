import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.contact import ContactMessage, ContactMessageStatus
from backend.app.models.user import User, UserRole


client = TestClient(app)


def create_test_user(
    db: Session,
    role: UserRole = UserRole.MEMBER,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        password_hash="test-password-hash",
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_test_contact(
    db: Session,
    *,
    user_id: uuid.UUID | None = None,
    status: ContactMessageStatus = ContactMessageStatus.NEW,
) -> ContactMessage:
    message = ContactMessage(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        subject="Test Subject",
        message="This is a test contact message.",
        status=status,
        user_id=user_id,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def auth_headers(user: User) -> dict[str, str]:
    from backend.app.core.security import create_access_token

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def get_test_db():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_submit_contact_message():
    response = client.post(
        "/contact",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Hello KBR",
            "message": "I would like to contact the KBR team.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["subject"] == "Hello KBR"
    assert data["message"] == "I would like to contact the KBR team."
    assert data["status"] == "new"
    assert data["user_id"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_authenticated_user_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db)

        response = client.post(
            "/contact",
            headers=auth_headers(user),
            json={
                "name": "Authenticated User",
                "email": user.email,
                "subject": "Authenticated message",
                "message": "This message belongs to an authenticated user.",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["user_id"] == str(user.id)

    finally:
        db.close()


def test_member_cannot_list_contact_messages():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.MEMBER)

        response = client.get(
            "/contact",
            headers=auth_headers(user),
        )

        assert response.status_code == 403

    finally:
        db.close()


def test_staff_can_list_contact_messages():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)
        create_test_contact(db)

        response = client.get(
            "/contact",
            headers=auth_headers(user),
        )

        assert response.status_code == 200

        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

    finally:
        db.close()


def test_admin_can_list_contact_messages():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.ADMIN)
        create_test_contact(db)

        response = client.get(
            "/contact",
            headers=auth_headers(user),
        )

        assert response.status_code == 200

    finally:
        db.close()


def test_unauthenticated_cannot_list_contact_messages():
    response = client.get("/contact")

    assert response.status_code in (401, 403)


def test_staff_can_get_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)
        message = create_test_contact(db)

        response = client.get(
            f"/contact/{message.id}",
            headers=auth_headers(user),
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(message.id)
        assert data["subject"] == message.subject

    finally:
        db.close()


def test_missing_contact_message_returns_404():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)

        response = client.get(
            f"/contact/{uuid.uuid4()}",
            headers=auth_headers(user),
        )

        assert response.status_code == 404

    finally:
        db.close()


def test_staff_can_update_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)
        message = create_test_contact(db)

        response = client.patch(
            f"/contact/{message.id}",
            headers=auth_headers(user),
            json={
                "status": "read",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "read"

    finally:
        db.close()


def test_admin_can_update_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.ADMIN)
        message = create_test_contact(db)

        response = client.patch(
            f"/contact/{message.id}",
            headers=auth_headers(user),
            json={
                "status": "replied",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "replied"

    finally:
        db.close()


def test_member_cannot_update_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.MEMBER)
        message = create_test_contact(db)

        response = client.patch(
            f"/contact/{message.id}",
            headers=auth_headers(user),
            json={
                "status": "read",
            },
        )

        assert response.status_code == 403

    finally:
        db.close()


def test_staff_cannot_delete_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)
        message = create_test_contact(db)

        response = client.delete(
            f"/contact/{message.id}",
            headers=auth_headers(user),
        )

        assert response.status_code == 403

    finally:
        db.close()


def test_admin_can_delete_contact_message():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.ADMIN)
        message = create_test_contact(db)

        response = client.delete(
            f"/contact/{message.id}",
            headers=auth_headers(user),
        )

        assert response.status_code == 204

    finally:
        db.close()


def test_delete_missing_contact_message_returns_404():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.ADMIN)

        response = client.delete(
            f"/contact/{uuid.uuid4()}",
            headers=auth_headers(user),
        )

        assert response.status_code == 404

    finally:
        db.close()


def test_contact_message_search():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)

        ContactMessage(
            name="Alice Example",
            email="alice@example.com",
            subject="Partnership request",
            message="We would like to discuss a partnership.",
            status=ContactMessageStatus.NEW,
        )

        message = ContactMessage(
            name="Bob Example",
            email="bob@example.com",
            subject="General question",
            message="I have a question about KBR.",
            status=ContactMessageStatus.NEW,
        )

        db.add_all(
            [
                ContactMessage(
                    name="Alice Example",
                    email="alice@example.com",
                    subject="Partnership request",
                    message="We would like to discuss a partnership.",
                    status=ContactMessageStatus.NEW,
                ),
                message,
            ]
        )
        db.commit()

        response = client.get(
            "/contact",
            headers=auth_headers(user),
            params={"search": "Partnership"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] >= 1
        assert any(
            item["subject"] == "Partnership request"
            for item in data["items"]
        )

    finally:
        db.close()


def test_contact_message_status_filter():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)

        create_test_contact(
            db,
            status=ContactMessageStatus.NEW,
        )

        create_test_contact(
            db,
            status=ContactMessageStatus.READ,
        )

        response = client.get(
            "/contact",
            headers=auth_headers(user),
            params={"status": "read"},
        )

        assert response.status_code == 200

        data = response.json()

        assert all(
            item["status"] == "read"
            for item in data["items"]
        )

    finally:
        db.close()


def test_contact_message_pagination():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)

        for _ in range(5):
            create_test_contact(db)

        response = client.get(
            "/contact",
            headers=auth_headers(user),
            params={
                "skip": 1,
                "limit": 2,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["skip"] == 1
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    finally:
        db.close()


def test_contact_message_validation():
    response = client.post(
        "/contact",
        json={
            "name": "A",
            "email": "invalid-email",
            "subject": "",
            "message": "short",
        },
    )

    assert response.status_code == 422


def test_anonymous_contact_message():
    response = client.post(
        "/contact",
        json={
            "name": "Anonymous User",
            "email": "anonymous@example.com",
            "subject": "Anonymous contact",
            "message": "This message is submitted anonymously.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] is None


def test_status_can_be_archived():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.ADMIN)
        message = create_test_contact(db)

        response = client.patch(
            f"/contact/{message.id}",
            headers=auth_headers(user),
            json={
                "status": "archived",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "archived"

    finally:
        db.close()


def test_contact_message_timestamps_exist():
    from backend.app.core.database import SessionLocal

    db = SessionLocal()

    try:
        user = create_test_user(db, UserRole.STAFF)
        message = create_test_contact(db)

        response = client.get(
            f"/contact/{message.id}",
            headers=auth_headers(user),
        )

        assert response.status_code == 200

        data = response.json()

        assert data["created_at"] is not None
        assert data["updated_at"] is not None

        datetime.fromisoformat(
            data["created_at"].replace("Z", "+00:00")
        )

        datetime.fromisoformat(
            data["updated_at"].replace("Z", "+00:00")
        )

    finally:
        db.close()