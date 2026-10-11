from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MLRiskSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model_type: str
    description: str
    total_rows: int
    http_rows: int
    business_rows: int
    risk_distribution: dict[str, int]
    overall: dict[str, Any]
    http: dict[str, Any]
    business: dict[str, Any]
    temporal_detection: dict[str, Any]


class MLRiskObservationsResponse(BaseModel):
    items: list[dict[str, Any]]
    count: int


class MLRiskIncidentsResponse(BaseModel):
    items: list[dict[str, Any]]
    count: int


class MLRiskConfigurationResponse(BaseModel):
    weights: dict[str, float]
    risk_levels: dict[str, str]
    behavioral_anomaly: dict[str, Any] = Field(default_factory=dict)
    temporal_detection: dict[str, Any] = Field(default_factory=dict)


class MLRiskHealthResponse(BaseModel):
    available: bool
    report_path: str
    message: str
