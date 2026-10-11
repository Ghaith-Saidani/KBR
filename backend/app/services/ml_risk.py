from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPORT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "reports"
    / "risk_scoring_report.json"
)


class MLRiskReportNotFoundError(Exception):
    """Raised when the ML risk report has not been generated."""


class MLRiskReportInvalidError(Exception):
    """Raised when the ML risk report cannot be parsed."""


def load_risk_report() -> dict[str, Any]:
    if not REPORT_PATH.exists():
        raise MLRiskReportNotFoundError(
            "Risk-scoring report has not been generated."
        )

    try:
        with REPORT_PATH.open("r", encoding="utf-8") as file:
            report = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise MLRiskReportInvalidError(
            "Risk-scoring report could not be loaded."
        ) from exc

    if not isinstance(report, dict):
        raise MLRiskReportInvalidError(
            "Risk-scoring report must contain a JSON object."
        )

    return report


def get_risk_summary() -> dict[str, Any]:
    report = load_risk_report()
    raw_distribution = report.get("risk_distribution") or {}
    distribution = {
        "minimal": int(raw_distribution.get("minimal", 0)),
        "low": int(raw_distribution.get("low", 0)),
        "medium": int(raw_distribution.get("medium", 0)),
        "high": int(raw_distribution.get("high", 0)),
    }

    return {
        "model_type": str(report.get("model_type", "")),
        "description": str(report.get("description", "")),
        "total_rows": int(report.get("total_rows", 0)),
        "http_rows": int(report.get("http_rows", 0)),
        "business_rows": int(report.get("business_rows", 0)),
        "risk_distribution": distribution,
        "overall": report.get("overall") or {},
        "http": report.get("http") or {},
        "business": report.get("business") or {},
        "temporal_detection": report.get("temporal_detection") or {},
    }


def get_top_risks(limit: int = 20) -> list[dict[str, Any]]:
    report = load_risk_report()
    items = report.get("top_risks", [])
    if not isinstance(items, list):
        return []
    return [item for item in items[:limit] if isinstance(item, dict)]


def get_top_incidents(limit: int = 20) -> list[dict[str, Any]]:
    report = load_risk_report()
    items = report.get("top_incidents", [])
    if not isinstance(items, list):
        return []
    return [item for item in items[:limit] if isinstance(item, dict)]


def get_risk_configuration() -> dict[str, Any]:
    report = load_risk_report()
    behavioral = report.get("behavioral_anomaly") or {}
    return {
        "weights": report.get("weights") or {},
        "risk_levels": report.get("risk_levels") or {},
        "behavioral_anomaly": behavioral,
        "temporal_detection": report.get("temporal_detection") or {},
    }
