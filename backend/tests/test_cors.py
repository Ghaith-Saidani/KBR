from fastapi.testclient import TestClient

from backend.app.main import app


def test_cors_allows_localhost_frontend():
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_allows_127_0_0_1_frontend():
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://127.0.0.1:5173"
    )


def test_cors_rejects_unknown_origin():
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://malicious.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400