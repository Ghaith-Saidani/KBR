from fastapi.testclient import TestClient


def test_root(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "KBR API is running"
    assert data["version"] == "0.1.0"


def test_health(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "version": "0.1.0",
    }


def test_database_health(client: TestClient):
    response = client.get("/health/db")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "database": "connected",
    }