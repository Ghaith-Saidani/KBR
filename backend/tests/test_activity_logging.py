from backend.app.models.user_activity import UserActivity


def test_activity_middleware_logs_request(
    client,
    db,
):
    response = client.get("/health")

    assert response.status_code == 200

    activity = (
        db.query(UserActivity)
        .filter(
            UserActivity.endpoint == "/health",
            UserActivity.method == "GET",
        )
        .order_by(
            UserActivity.occurred_at.desc(),
        )
        .first()
    )

    assert activity is not None
    assert activity.action == "GET /health"
    assert activity.resource_type == "http_request"
    assert activity.details == "HTTP 200"
    assert activity.activity_metadata is not None
    assert activity.activity_metadata["status_code"] == 200


def test_activity_middleware_logs_query_parameters(
    client,
    db,
):
    response = client.get(
        "/health?source=test&foo=bar",
    )

    assert response.status_code == 200

    activity = (
        db.query(UserActivity)
        .filter(
            UserActivity.endpoint == "/health",
            UserActivity.method == "GET",
        )
        .order_by(
            UserActivity.occurred_at.desc(),
        )
        .first()
    )

    assert activity is not None
    assert activity.activity_metadata is not None

    query_params = activity.activity_metadata[
        "query_params"
    ]

    assert query_params == {
        "source": "test",
        "foo": "bar",
    }


def test_activity_middleware_records_client_information(
    client,
    db,
):
    response = client.get(
        "/health",
        headers={
            "user-agent": "KBR-Test-Agent",
        },
    )

    assert response.status_code == 200

    activity = (
        db.query(UserActivity)
        .filter(
            UserActivity.endpoint == "/health",
            UserActivity.method == "GET",
        )
        .order_by(
            UserActivity.occurred_at.desc(),
        )
        .first()
    )

    assert activity is not None
    assert activity.user_agent == "KBR-Test-Agent"
    assert activity.ip_address is not None


def test_activity_middleware_ignores_documentation_paths(
    client,
    db,
):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    activity = (
        db.query(UserActivity)
        .filter(
            UserActivity.endpoint == "/openapi.json",
        )
        .first()
    )

    assert activity is None