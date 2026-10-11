from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.models.user import User, UserRole
from backend.app.services import ml_risk


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


def _report_payload() -> dict:
    return {
        "model_type": "Hybrid Isolation Forest + deterministic risk scoring",
        "description": "Test report",
        "total_rows": 2,
        "http_rows": 1,
        "business_rows": 1,
        "risk_distribution": {
            "minimal": 1,
            "low": 0,
            "medium": 1,
        },
        "overall": {
            "rows": 2,
            "mean_risk_score": 0.3,
            "high_risk_count": 0,
            "medium_risk_count": 1,
            "low_risk_count": 0,
            "minimal_risk_count": 1,
        },
        "http": {"rows": 1, "mean_risk_score": 0.6},
        "business": {"rows": 1, "mean_risk_score": 0.0},
        "weights": {
            "authentication_failure": 0.25,
            "error_rate": 0.15,
            "activity_spike": 0.15,
            "unusual_method": 0.1,
            "unusual_endpoint": 0.1,
            "high_user_activity": 0.1,
            "behavioral_anomaly": 0.15,
        },
        "risk_levels": {
            "minimal": "< 0.20",
            "low": "0.20 - 0.449999",
            "medium": "0.45 - 0.749999",
            "high": ">= 0.75",
        },
        "behavioral_anomaly": {"model_type": "IsolationForest"},
        "temporal_detection": {
            "incident_count": 1,
            "incident_distribution": {"http_error_burst": 1},
            "incident_risk_distribution": {"high": 1},
        },
        "top_risks": [
            {
                "id": "risk-1",
                "risk_score": 0.8,
                "risk_level": "high",
                "action": "GET /auth/me",
            },
            {
                "id": "risk-2",
                "risk_score": 0.6,
                "risk_level": "medium",
                "action": "POST /auth/login",
            },
        ],
        "top_incidents": [
            {
                "incident_id": "HTTP-ERROR-0001",
                "incident_type": "http_error_burst",
                "event_count": 8,
                "risk_score": 0.8,
                "risk_level": "high",
                "reason": "HTTP error burst",
            }
        ],
    }


@pytest.fixture
def report_file(tmp_path, monkeypatch):
    path = tmp_path / "risk_scoring_report.json"
    path.write_text(
        json.dumps(_report_payload()),
        encoding="utf-8",
    )
    monkeypatch.setattr(ml_risk, "REPORT_PATH", path)
    return path


def test_ml_risk_endpoints_require_authentication(client: TestClient):
    for endpoint in (
        "/admin/ml/risk/summary",
        "/admin/ml/risk/observations",
        "/admin/ml/risk/incidents",
        "/admin/ml/risk/configuration",
        "/admin/ml/risk/health",
    ):
        response = client.get(endpoint)
        assert response.status_code == 401, endpoint


def test_ml_risk_endpoints_forbid_non_admin_users(
    client: TestClient,
    member_user: User,
    report_file,
):
    headers = _auth_headers(member_user)

    for endpoint in (
        "/admin/ml/risk/summary",
        "/admin/ml/risk/observations",
        "/admin/ml/risk/incidents",
        "/admin/ml/risk/configuration",
        "/admin/ml/risk/health",
    ):
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 403, endpoint


def test_ml_risk_summary_and_missing_distribution_level(
    client: TestClient,
    admin_user: User,
    report_file,
):
    response = client.get(
        "/admin/ml/risk/summary",
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 2
    assert body["risk_distribution"] == {
        "minimal": 1,
        "low": 0,
        "medium": 1,
        "high": 0,
    }


def test_ml_risk_observations_and_incidents_support_limits(
    client: TestClient,
    admin_user: User,
    report_file,
):
    headers = _auth_headers(admin_user)

    observations = client.get(
        "/admin/ml/risk/observations?limit=1",
        headers=headers,
    )
    assert observations.status_code == 200
    assert observations.json()["count"] == 1
    assert observations.json()["items"][0]["id"] == "risk-1"

    incidents = client.get(
        "/admin/ml/risk/incidents?limit=1",
        headers=headers,
    )
    assert incidents.status_code == 200
    assert incidents.json()["count"] == 1
    assert incidents.json()["items"][0]["incident_id"] == "HTTP-ERROR-0001"


def test_ml_risk_health_reports_available(
    client: TestClient,
    admin_user: User,
    report_file,
):
    response = client.get(
        "/admin/ml/risk/health",
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["available"] is True


def test_missing_ml_risk_report_returns_service_unavailable(
    client: TestClient,
    admin_user: User,
    tmp_path,
    monkeypatch,
):
    missing_path = tmp_path / "missing-report.json"
    monkeypatch.setattr(ml_risk, "REPORT_PATH", missing_path)

    response = client.get(
        "/admin/ml/risk/summary",
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 503

    health = client.get(
        "/admin/ml/risk/health",
        headers=_auth_headers(admin_user),
    )
    assert health.status_code == 200
    assert health.json()["available"] is False
