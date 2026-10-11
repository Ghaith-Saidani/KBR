from __future__ import annotations

import pandas as pd

from backend.ml.risk_scoring import (
    classify_risk,
    detect_temporal_incidents,
)


def _make_http_rows() -> pd.DataFrame:
    base = pd.Timestamp(
        "2026-01-01 12:00:00",
        tz="UTC",
    )

    rows: list[dict] = []

    # Four authentication failures inside the same
    # 120-second window.
    for index in range(4):
        rows.append(
            {
                "id": f"login-{index}",
                "occurred_at": base + pd.to_timedelta(
                    int(index * 5),
                    unit="s",
                ),
                "is_http_request": 1,
                "is_auth_failure": 1,
                "is_error_status": 1,
                "error_signal": 1,
                "activity_spike_signal": 0,
                "status_code": 401,
                "method": "POST",
                "endpoint_normalized": "/auth/login",
                "user_id": "user-1",
                "risk_score": 0.8,
            }
        )

    # Six additional authentication failures outside
    # the first burst.
    for index in range(6):
        rows.append(
            {
                "id": f"login-late-{index}",
                "occurred_at": base + pd.to_timedelta(
                    int(300 + index * 5),
                    unit="s",
                ),
                "is_http_request": 1,
                "is_auth_failure": 1,
                "is_error_status": 1,
                "error_signal": 1,
                "activity_spike_signal": 0,
                "status_code": 401,
                "method": "POST",
                "endpoint_normalized": "/auth/login",
                "user_id": "user-1",
                "risk_score": 0.8,
            }
        )

    # Normal HTTP activity overlapping the first
    # authentication/error burst.
    #
    # These rows are what create the activity spike.
    for index in range(20):
        rows.append(
            {
                "id": f"activity-{index}",
                "occurred_at": base + pd.to_timedelta(
                    int(60 + index),
                    unit="s",
                ),
                "is_http_request": 1,
                "is_auth_failure": 0,
                "is_error_status": 0,
                "error_signal": 0,
                "activity_spike_signal": 1,
                "status_code": 200,
                "method": "GET",
                "endpoint_normalized": "/activities",
                "user_id": f"user-{index}",
                "risk_score": 0.2,
            }
        )

    return pd.DataFrame(rows)


def test_classify_risk_boundaries() -> None:
    assert classify_risk(0.0) == "minimal"
    assert classify_risk(0.199999) == "minimal"
    assert classify_risk(0.20) == "low"
    assert classify_risk(0.449999) == "low"
    assert classify_risk(0.45) == "medium"
    assert classify_risk(0.749999) == "medium"
    assert classify_risk(0.75) == "high"
    assert classify_risk(1.0) == "high"


def test_temporal_signals_are_independent() -> None:
    results, incidents = detect_temporal_incidents(
        _make_http_rows()
    )

    assert len(incidents) >= 3

    incident_types = {
        incident["incident_type"]
        for incident in incidents
    }

    assert incident_types == {
        "authentication_failure_burst",
        "http_error_burst",
        "activity_burst",
    }

    # Authentication failures form an authentication burst.
    auth_rows = results[
        results["endpoint_normalized"]
        == "/auth/login"
    ]

    assert not auth_rows.empty

    assert (
        auth_rows["auth_burst_id"]
        .notna()
        .all()
    )

    assert (
        auth_rows["auth_burst_id"]
        .nunique()
        >= 1
    )

    # At least some authentication events also belong
    # to an independent HTTP error burst.
    assert (
        auth_rows["error_burst_id"]
        .notna()
        .any()
    )

    # The activity signal exists independently.
    assert (
        results["activity_burst_id"]
        .notna()
        .any()
    )

    # The three signals must remain represented by
    # separate identifiers.
    assert "auth_burst_id" in results.columns
    assert "error_burst_id" in results.columns
    assert "activity_burst_id" in results.columns

    # At least one event participates in two different
    # temporal signals simultaneously.
    multi_signal = results[
        (
            results[
                [
                    "auth_burst_id",
                    "error_burst_id",
                    "activity_burst_id",
                ]
            ]
            .notna()
            .sum(axis=1)
            >= 2
        )
    ]

    assert not multi_signal.empty


def test_activity_burst_can_overlap_specific_incidents() -> None:
    results, _ = detect_temporal_incidents(
        _make_http_rows()
    )

    overlapping = results[
        results["activity_burst_id"].notna()
        & (
            results["auth_burst_id"].notna()
            | results["error_burst_id"].notna()
        )
    ]

    assert not overlapping.empty

    assert (
        overlapping["activity_burst_id"]
        .notna()
        .all()
    )

    # At least one event belongs to all three independent
    # temporal signals.
    all_three = results[
        results["auth_burst_id"].notna()
        & results["error_burst_id"].notna()
        & results["activity_burst_id"].notna()
    ]

    assert not all_three.empty