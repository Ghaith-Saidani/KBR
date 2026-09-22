from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.api.analytics import router
from backend.app.core.security import create_access_token
from backend.app.models.user import User


def create_test_app() -> FastAPI:
    app = FastAPI()

    app.include_router(
        router,
    )

    return app


def admin_headers(
    admin_user: User,
) -> dict[str, str]:
    """Build authorization headers for an admin test user."""

    token = create_access_token(
        subject=str(admin_user.id),
        role=admin_user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_analytics_query_endpoint_is_registered() -> None:
    app = create_test_app()

    openapi = app.openapi()

    assert "/admin/analytics/query" in openapi["paths"]

    assert (
        "post"
        in openapi["paths"]["/admin/analytics/query"]
    )


def test_analytics_query_requires_authentication() -> None:
    app = create_test_app()

    client = TestClient(
        app,
    )

    response = client.post(
        "/admin/analytics/query",
        json={
            "query": "How many events does KBR have?",
        },
    )

    assert response.status_code == 401


def test_analytics_query_total_events(
    client: TestClient,
    admin_user: User,
    db: Session,
) -> None:
    response = client.post(
        "/admin/analytics/query",
        headers=admin_headers(
            admin_user,
        ),
        json={
            "query": "How many events does KBR have?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supported"] is True

    result = data["result"]

    assert result is not None
    assert result["type"] == "metric"
    assert result["metric"] == "total_events"
    assert isinstance(
        result["value"],
        int,
    )
    assert result["value"] >= 0
    assert result["source"] == (
        "KBR PostgreSQL database"
    )


def test_analytics_query_events_in_august_2026(
    client: TestClient,
    admin_user: User,
    db: Session,
) -> None:
    response = client.post(
        "/admin/analytics/query",
        headers=admin_headers(
            admin_user,
        ),
        json={
            "query": (
                "How many events were created "
                "in August 2026?"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supported"] is True

    result = data["result"]

    assert result is not None
    assert result["type"] == "metric"
    assert result["metric"] == (
        "events_created_in_period"
    )
    assert result["value"] >= 0
    assert result["start_date"] == "2026-08-01"
    assert result["end_date"] == "2026-08-31"


def test_analytics_query_membership_trend(
    client: TestClient,
    admin_user: User,
    db: Session,
) -> None:
    response = client.post(
        "/admin/analytics/query",
        headers=admin_headers(
            admin_user,
        ),
        json={
            "query": "How has membership grown?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supported"] is True

    result = data["result"]

    assert result is not None
    assert result["type"] == "trend"
    assert result["metric"] == (
        "members_created_per_month"
    )

    months = result["months"]

    assert isinstance(
        months,
        list,
    )

    assert len(months) == 6

    for month, value in months:
        assert len(month) == 7
        assert value >= 0


def test_analytics_query_event_comparison(
    client: TestClient,
    admin_user: User,
    db: Session,
) -> None:
    response = client.post(
        "/admin/analytics/query",
        headers=admin_headers(
            admin_user,
        ),
        json={
            "query": (
                "Compare events between "
                "June and September."
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supported"] is True

    result = data["result"]

    assert result is not None
    assert result["type"] == "comparison"
    assert result["metric"] == (
        "events_created_comparison"
    )

    first_value = result["first_value"]
    second_value = result["second_value"]
    difference = result["difference"]

    assert first_value >= 0
    assert second_value >= 0

    assert difference == (
        second_value - first_value
    )

    assert (
        result["first_period_label"]
        == "juin 2026"
    )

    assert (
        result["second_period_label"]
        == "septembre 2026"
    )


def test_analytics_query_unsupported_metric(
    client: TestClient,
    admin_user: User,
    db: Session,
) -> None:
    response = client.post(
        "/admin/analytics/query",
        headers=admin_headers(
            admin_user,
        ),
        json={
            "query": (
                "What is the average age "
                "of KBR members?"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supported"] is False
    assert data["result"] is None