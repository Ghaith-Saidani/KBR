from __future__ import annotations

import json

from pathlib import Path

import joblib
import pandas as pd

from backend.ml.features.activity_features import (

    build_activity_feature_dataset,

)

MODEL_DIR = Path("data/models")
REPORT_DIR = Path("data/reports")

HTTP_MODEL_PATH = MODEL_DIR / "http_anomaly_detector.joblib"
BUSINESS_MODEL_PATH = MODEL_DIR / "business_anomaly_detector.joblib"
ANOMALY_REPORT_PATH = REPORT_DIR / "anomaly_detection_report.json"

REPORT_PATH = REPORT_DIR / "risk_scoring_report.json"

# ---------------------------------------------------------------------------

# Per-event risk weights

# ---------------------------------------------------------------------------

WEIGHT_AUTH_FAILURE = 0.25

WEIGHT_ERROR_RATE = 0.15

WEIGHT_ACTIVITY_SPIKE = 0.15

WEIGHT_UNUSUAL_METHOD = 0.10

WEIGHT_UNUSUAL_ENDPOINT = 0.10

WEIGHT_HIGH_USER_ACTIVITY = 0.10

WEIGHT_BEHAVIORAL_ANOMALY = 0.15

HTTP_RISK_METHODS = {

    "TRACE",

    "CONNECT",

}

SUSPICIOUS_ENDPOINT_TOKENS = {

    "admin",

    "auth",

    "login",

    "token",

    "password",

    "reset",

    "upload",

}

# ---------------------------------------------------------------------------

# Temporal incident configuration

# ---------------------------------------------------------------------------

AUTH_BURST_WINDOW_SECONDS = 120

AUTH_BURST_MIN_FAILURES = 3

ERROR_BURST_WINDOW_SECONDS = 120

ERROR_BURST_MIN_ERRORS = 5

ACTIVITY_BURST_WINDOW_SECONDS = 300

ACTIVITY_BURST_MIN_REQUESTS = 10

def clamp(

    value: float,

    minimum: float = 0.0,

    maximum: float = 1.0,

) -> float:

    return max(

        minimum,

        min(maximum, value),

    )

def safe_float(

    value: object,

    default: float = 0.0,

) -> float:

    try:

        if pd.isna(value):

            return default

        return float(value)

    except (TypeError, ValueError):

        return default

def normalize_method(

    value: object,

) -> str:

    if value is None:

        return ""

    return str(value).strip().upper()

def normalize_endpoint(

    value: object,

) -> str:

    if value is None:

        return ""

    return str(value).strip().lower()

# ---------------------------------------------------------------------------

# Per-event signals

# ---------------------------------------------------------------------------

def _load_anomaly_report() -> dict:
    if not ANOMALY_REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Anomaly detection report not found: {ANOMALY_REPORT_PATH}"
        )

    with ANOMALY_REPORT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        report = json.load(file)

    if not isinstance(report, dict):
        raise ValueError(
            "Anomaly detection report must contain a JSON object."
        )

    return report


def _load_model_bundle(model_path: Path) -> dict:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Anomaly detector model not found: {model_path}"
        )

    bundle = joblib.load(model_path)

    if not isinstance(bundle, dict):
        raise ValueError(
            f"Invalid anomaly detector bundle: {model_path}"
        )

    required = {
        "model",
        "preprocessor",
        "numeric_features",
        "categorical_features",
    }

    missing = required - set(bundle)
    if missing:
        raise ValueError(
            f"Anomaly detector bundle is missing: "
            f"{', '.join(sorted(missing))}"
        )

    return bundle


def add_behavioral_anomaly_scores(
    features: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply the persisted HTTP/business Isolation Forest bundles to
    the complete feature dataset.
    """
    if features.empty:
        raise ValueError(
            "Cannot calculate behavioral anomaly scores "
            "for an empty dataset."
        )

    report = _load_anomaly_report()

    http_threshold = safe_float(
        report.get("http_model", {}).get("threshold"),
        default=float("nan"),
    )
    business_threshold = safe_float(
        report.get("business_model", {}).get("threshold"),
        default=float("nan"),
    )

    if pd.isna(http_threshold) or pd.isna(business_threshold):
        raise ValueError(
            "Anomaly thresholds are missing from the anomaly "
            "detection report."
        )

    http_bundle = _load_model_bundle(
        HTTP_MODEL_PATH
    )
    business_bundle = _load_model_bundle(
        BUSINESS_MODEL_PATH
    )

    results = features.copy()

    results["anomaly_score"] = pd.Series(
        float("nan"),
        index=results.index,
        dtype="float64",
    )
    results["anomaly_threshold"] = pd.Series(
        float("nan"),
        index=results.index,
        dtype="float64",
    )
    results["model_population"] = pd.Series(
        pd.NA,
        index=results.index,
        dtype="object",
    )

    def score_population(
        mask: pd.Series,
        bundle: dict,
        threshold: float,
        population: str,
    ) -> None:
        if not mask.any():
            return

        numeric_features = list(
            bundle["numeric_features"]
        )
        categorical_features = list(
            bundle["categorical_features"]
        )
        feature_columns = (
            numeric_features
            + categorical_features
        )

        missing = set(feature_columns) - set(results.columns)
        if missing:
            raise ValueError(
                f"Missing {population} anomaly features: "
                + ", ".join(sorted(missing))
            )

        population_frame = results.loc[
            mask,
            feature_columns,
        ].copy()

        transformed = bundle["preprocessor"].transform(
            population_frame
        )

        scores = -bundle["model"].decision_function(
            transformed
        )

        results.loc[
            mask,
            "anomaly_score",
        ] = scores

        results.loc[
            mask,
            "anomaly_threshold",
        ] = threshold

        results.loc[
            mask,
            "model_population",
        ] = population

    score_population(
        results["is_http_request"] == 1,
        http_bundle,
        http_threshold,
        "http",
    )

    score_population(
        results["is_http_request"] == 0,
        business_bundle,
        business_threshold,
        "business",
    )

    if results["anomaly_score"].isna().any():
        raise ValueError(
            "Some rows did not receive a behavioral anomaly score."
        )

    return results


def calculate_auth_failure_signal(

    row: pd.Series,

) -> float:

    is_auth_failure = safe_float(

        row.get("is_auth_failure", 0)

    )

    return 1.0 if is_auth_failure > 0 else 0.0

def calculate_error_signal(

    row: pd.Series,

) -> float:

    status_code = int(

        safe_float(

            row.get("status_code", 0)

        )

    )

    if status_code >= 500:

        return 1.0

    if status_code >= 400:

        return 0.65

    return 0.0

def calculate_activity_spike_signal(

    row: pd.Series,

) -> float:

    activity_5m = safe_float(

        row.get("activity_count_5m", 0)

    )

    activity_1h = safe_float(

        row.get("activity_count_1h", 0)

    )

    if activity_1h <= 0:

        return 0.0

    expected_5m = activity_1h / 12.0

    if expected_5m <= 0:

        return 0.0

    ratio = activity_5m / expected_5m

    if ratio <= 1.5:

        return 0.0

    signal = (

        ratio - 1.5

    ) / 3.0

    return clamp(signal)

def calculate_method_signal(

    row: pd.Series,

) -> float:

    method = normalize_method(

        row.get("method")

    )

    if method in HTTP_RISK_METHODS:

        return 1.0

    return 0.0

def calculate_endpoint_signal(

    row: pd.Series,

) -> float:

    endpoint = normalize_endpoint(

        row.get("endpoint_normalized")

    )

    if not endpoint:

        return 0.0

    matched_tokens = [

        token

        for token in SUSPICIOUS_ENDPOINT_TOKENS

        if token in endpoint

    ]

    if not matched_tokens:

        return 0.0

    return clamp(

        len(matched_tokens) / 2.0

    )

def calculate_user_activity_signal(

    row: pd.Series,

) -> float:

    user_activity_1h = safe_float(

        row.get("user_activity_count_1h", 0)

    )

    if user_activity_1h <= 20:

        return 0.0

    if user_activity_1h >= 100:

        return 1.0

    return clamp(

        (user_activity_1h - 20.0)

        / 80.0

    )

def calculate_behavioral_anomaly_signal(
    row: pd.Series,
) -> float:
    score = safe_float(
        row.get("anomaly_score"),
        default=float("nan"),
    )

    if pd.isna(score):
        return 0.0

    threshold = safe_float(
        row.get("anomaly_threshold"),
        default=float("nan"),
    )

    if pd.isna(threshold):
        return 0.0

    distance = score - threshold

    if distance <= 0:
        return 0.0

    # The anomaly signal is calibrated against the trained
    # population-specific threshold. A distance of 0.04 or more
    # is treated as a maximum behavioral-anomaly signal.
    return clamp(distance / 0.04)


def calculate_risk_score(

    *,

    auth_failure_signal: float,

    error_signal: float,

    activity_spike_signal: float,

    method_signal: float,

    endpoint_signal: float,

    user_activity_signal: float,

    behavioral_anomaly_signal: float,

) -> float:

    score = (

        auth_failure_signal

        * WEIGHT_AUTH_FAILURE

        + error_signal

        * WEIGHT_ERROR_RATE

        + activity_spike_signal

        * WEIGHT_ACTIVITY_SPIKE

        + method_signal

        * WEIGHT_UNUSUAL_METHOD

        + endpoint_signal

        * WEIGHT_UNUSUAL_ENDPOINT

        + user_activity_signal

        * WEIGHT_HIGH_USER_ACTIVITY

        + behavioral_anomaly_signal

        * WEIGHT_BEHAVIORAL_ANOMALY

    )

    return clamp(score)

def classify_risk(

    risk_score: float,

) -> str:

    if risk_score >= 0.75:

        return "high"

    if risk_score >= 0.45:

        return "medium"

    if risk_score >= 0.20:

        return "low"

    return "minimal"

def build_risk_reasons(
    *,
    auth_failure_signal: float,
    error_signal: float,
    activity_spike_signal: float,
    method_signal: float,
    endpoint_signal: float,
    user_activity_signal: float,
    behavioral_anomaly_signal: float = 0.0,
) -> list[str]:
    reasons: list[str] = []

    if auth_failure_signal >= 0.75:
        reasons.append("strong authentication failure signal")
    elif auth_failure_signal >= 0.35:
        reasons.append("authentication failure signal")

    if error_signal >= 0.75:
        reasons.append("strong HTTP error signal")
    elif error_signal >= 0.35:
        reasons.append("HTTP error signal")

    if activity_spike_signal >= 0.75:
        reasons.append("strong activity spike")
    elif activity_spike_signal >= 0.35:
        reasons.append("activity spike")

    if method_signal >= 0.75:
        reasons.append("strong unusual HTTP method")
    elif method_signal >= 0.35:
        reasons.append("unusual HTTP method")

    if endpoint_signal >= 0.75:
        reasons.append("strong unusual endpoint")
    elif endpoint_signal >= 0.35:
        reasons.append("unusual endpoint")

    if user_activity_signal >= 0.75:
        reasons.append("strong high user activity")
    elif user_activity_signal >= 0.35:
        reasons.append("high user activity")

    if behavioral_anomaly_signal >= 0.75:
        reasons.append("strong behavioral anomaly")
    elif behavioral_anomaly_signal >= 0.35:
        reasons.append("behavioral anomaly")

    return reasons

# ---------------------------------------------------------------------------

# Per-event scoring

# ---------------------------------------------------------------------------

def score_activity_dataset(

    features: pd.DataFrame,

) -> pd.DataFrame:

    if features.empty:

        raise ValueError(

            "Cannot calculate risk scores "

            "for an empty dataset."

        )

    results = features.copy()

    if "anomaly_score" not in results.columns:
        results = add_behavioral_anomaly_scores(
            results
        )

    results["auth_failure_signal"] = (

        results.apply(

            calculate_auth_failure_signal,

            axis=1,

        )

    )

    results["error_signal"] = (

        results.apply(

            calculate_error_signal,

            axis=1,

        )

    )

    results["activity_spike_signal"] = (

        results.apply(

            calculate_activity_spike_signal,

            axis=1,

        )

    )

    results["method_signal"] = (

        results.apply(

            calculate_method_signal,

            axis=1,

        )

    )

    results["endpoint_signal"] = (

        results.apply(

            calculate_endpoint_signal,

            axis=1,

        )

    )

    results["user_activity_signal"] = (

        results.apply(

            calculate_user_activity_signal,

            axis=1,

        )

    )

    results["behavioral_anomaly_signal"] = (

        results.apply(

            calculate_behavioral_anomaly_signal,

            axis=1,

        )

    )

    results["risk_score"] = results.apply(

        lambda row: calculate_risk_score(

            auth_failure_signal=safe_float(

                row.get(

                    "auth_failure_signal",

                    0,

                )

            ),

            error_signal=safe_float(

                row.get(

                    "error_signal",

                    0,

                )

            ),

            activity_spike_signal=safe_float(

                row.get(

                    "activity_spike_signal",

                    0,

                )

            ),

            method_signal=safe_float(

                row.get(

                    "method_signal",

                    0,

                )

            ),

            endpoint_signal=safe_float(

                row.get(

                    "endpoint_signal",

                    0,

                )

            ),

            user_activity_signal=safe_float(

                row.get(

                    "user_activity_signal",

                    0,

                )

            ),
            behavioral_anomaly_signal=safe_float(

                row.get(

                    "behavioral_anomaly_signal",

                    0,

                )

            ),

        ),

        axis=1,

    )

    results["risk_level"] = (

        results["risk_score"]

        .apply(classify_risk)

    )

    results["risk_reasons"] = results.apply(

        lambda row: build_risk_reasons(

            auth_failure_signal=safe_float(

                row.get(

                    "auth_failure_signal",

                    0,

                )

            ),

            error_signal=safe_float(

                row.get(

                    "error_signal",

                    0,

                )

            ),

            activity_spike_signal=safe_float(

                row.get(

                    "activity_spike_signal",

                    0,

                )

            ),

            method_signal=safe_float(

                row.get(

                    "method_signal",

                    0,

                )

            ),

            endpoint_signal=safe_float(

                row.get(

                    "endpoint_signal",

                    0,

                )

            ),

            user_activity_signal=safe_float(

                row.get(

                    "user_activity_signal",

                    0,

                )

            ),
            behavioral_anomaly_signal=safe_float(

                row.get(

                    "behavioral_anomaly_signal",

                    0,

                )

            ),

        ),

        axis=1,

    )

    results["occurred_at"] = pd.to_datetime(

        results["occurred_at"],

        format="mixed",

        utc=True,

    )

    return results

# ---------------------------------------------------------------------------

# Temporal helpers

# ---------------------------------------------------------------------------

def _calculate_auth_burst_signal(

    failure_count: int,

) -> float:

    if failure_count < AUTH_BURST_MIN_FAILURES:

        return 0.0

    signal = (

        failure_count

        - AUTH_BURST_MIN_FAILURES

        + 1

    ) / 7.0

    return clamp(

        max(0.4, signal)

    )

def _calculate_error_burst_signal(

    error_count: int,

) -> float:

    if error_count < ERROR_BURST_MIN_ERRORS:

        return 0.0

    signal = (

        error_count

        - ERROR_BURST_MIN_ERRORS

        + 1

    ) / 10.0

    return clamp(

        max(0.3, signal)

    )

def _calculate_activity_burst_signal(

    request_count: int,

) -> float:

    if request_count < ACTIVITY_BURST_MIN_REQUESTS:

        return 0.0

    signal = (

        request_count

        - ACTIVITY_BURST_MIN_REQUESTS

    ) / 40.0

    return clamp(

        max(0.2, signal)

    )

# ---------------------------------------------------------------------------

# Temporal incident detection

# ---------------------------------------------------------------------------

def detect_temporal_incidents(

    results: pd.DataFrame,

) -> tuple[pd.DataFrame, list[dict]]:

    """

    Detect independent temporal signals.

    Authentication failures, HTTP errors, and generic activity bursts are

    intentionally evaluated independently. A single event may belong to

    multiple temporal incidents at the same time.

    """

    if results.empty:

        return results.copy(), []

    work = results.copy()

    work["occurred_at"] = pd.to_datetime(

        work["occurred_at"],

        utc=True,

    )

    work = (

        work

        .sort_values("occurred_at")

        .reset_index(drop=True)

    )

    temporal_columns = [

        "auth_burst_id",

        "auth_burst_risk_score",

        "auth_burst_risk_level",

        "auth_burst_reason",

        "error_burst_id",

        "error_burst_risk_score",

        "error_burst_risk_level",

        "error_burst_reason",

        "activity_burst_id",

        "activity_burst_risk_score",

        "activity_burst_risk_level",

        "activity_burst_reason",

    ]

    for column in temporal_columns:

        if column.endswith("_risk_score"):

            work[column] = pd.Series(

                float("nan"),

                index=work.index,

                dtype="float64",

            )

        else:

            work[column] = pd.Series(

                pd.NA,

                index=work.index,

                dtype="object",

            )

    incidents: list[dict] = []

    next_incident_number = 1

    incident_prefix = {

        "authentication_failure_burst": "AUTH-BURST",

        "http_error_burst": "HTTP-ERROR",

        "activity_burst": "ACTIVITY-BURST",

    }

    incident_column_prefix = {

        "authentication_failure_burst": "auth_burst",

        "http_error_burst": "error_burst",

        "activity_burst": "activity_burst",

    }

    def next_incident_id(incident_type: str) -> str:

        nonlocal next_incident_number

        prefix = incident_prefix[incident_type]

        incident_id = f"{prefix}-{next_incident_number:04d}"

        next_incident_number += 1

        return incident_id

    def assign_temporal_signal(

        cluster: pd.DataFrame,

        *,

        incident_type: str,

        risk_score: float,

        reason: str,

        incident_id: str,

    ) -> None:

        prefix = incident_column_prefix[incident_type]

        work.loc[cluster.index, f"{prefix}_id"] = incident_id

        work.loc[cluster.index, f"{prefix}_risk_score"] = risk_score

        work.loc[cluster.index, f"{prefix}_risk_level"] = classify_risk(risk_score)

        work.loc[cluster.index, f"{prefix}_reason"] = reason

    def create_incident(

        cluster: pd.DataFrame,

        *,

        incident_type: str,

        base_risk: float,

        burst_signal: float,

        reason: str,

        endpoint: str | None = None,

        failure_count: int | None = None,

        error_count: int | None = None,

    ) -> dict:

        incident_id = next_incident_id(incident_type)

        incident_score = clamp(

            base_risk * 0.65

            + burst_signal * 0.35

        )

        # Generic activity bursts describe traffic intensity rather than

        # automatically representing a security incident.

        if incident_type == "activity_burst":

            incident_score = min(incident_score, 0.70)

        incident_level = classify_risk(incident_score)

        start_time = cluster["occurred_at"].min()

        end_time = cluster["occurred_at"].max()

        incident = {

            "incident_id": incident_id,

            "incident_type": incident_type,

            "start_time": str(start_time),

            "end_time": str(end_time),

            "duration_seconds": round(

                (end_time - start_time).total_seconds(),

                3,

            ),

            "event_count": int(len(cluster)),

            "risk_score": round(incident_score, 6),

            "risk_level": incident_level,

            "reason": reason,

        }

        if endpoint is not None:

            incident["endpoint"] = endpoint

        if failure_count is not None:

            incident["failure_count"] = int(failure_count)

        if error_count is not None:

            incident["error_count"] = int(error_count)

        assign_temporal_signal(

            cluster,

            incident_type=incident_type,

            risk_score=incident_score,

            reason=reason,

            incident_id=incident_id,

        )

        incidents.append(incident)

        return incident

    def build_fixed_windows(

        frame: pd.DataFrame,

        *,

        window_seconds: int,

    ) -> list[pd.DataFrame]:

        """Build non-overlapping fixed windows from chronologically ordered events."""

        if frame.empty:

            return []

        ordered = frame.sort_values("occurred_at").copy()

        timestamps = ordered["occurred_at"].tolist()

        windows: list[pd.DataFrame] = []

        start_position = 0

        for position in range(1, len(ordered)):

            elapsed = (

                timestamps[position] - timestamps[start_position]

            ).total_seconds()

            if elapsed > window_seconds:

                windows.append(

                    ordered.iloc[start_position:position].copy()

                )

                start_position = position

        windows.append(ordered.iloc[start_position:].copy())

        return windows

    http = work[work["is_http_request"] == 1].copy()

    if http.empty:

        return work, incidents

    # =========================================================

    # 1. AUTHENTICATION FAILURE BURSTS

    # =========================================================

    auth_failures = http[http["is_auth_failure"] > 0].copy()

    if not auth_failures.empty:

        group_columns: list[str] = []

        if "user_id" in auth_failures.columns:

            group_columns.append("user_id")

        group_columns.append("endpoint_normalized")

        for _, group in auth_failures.groupby(

            group_columns,

            dropna=False,

        ):

            for cluster in build_fixed_windows(

                group,

                window_seconds=AUTH_BURST_WINDOW_SECONDS,

            ):

                failure_count = len(cluster)

                if failure_count < AUTH_BURST_MIN_FAILURES:

                    continue

                endpoint = str(

                    cluster["endpoint_normalized"].iloc[0]

                )

                base_risk = float(cluster["risk_score"].max())

                burst_signal = _calculate_auth_burst_signal(

                    failure_count

                )

                create_incident(

                    cluster,

                    incident_type="authentication_failure_burst",

                    base_risk=base_risk,

                    burst_signal=burst_signal,

                    reason="authentication failure burst",

                    endpoint=endpoint,

                    failure_count=failure_count,

                )

    # =========================================================

    # 2. HTTP ERROR BURSTS

    # =========================================================

    error_events = http[http["error_signal"] > 0].copy()

    if not error_events.empty:

        for _, group in error_events.groupby(

            ["endpoint_normalized"],

            dropna=False,

        ):

            for cluster in build_fixed_windows(

                group,

                window_seconds=ERROR_BURST_WINDOW_SECONDS,

            ):

                error_count = len(cluster)

                if error_count < ERROR_BURST_MIN_ERRORS:

                    continue

                endpoint = str(

                    cluster["endpoint_normalized"].iloc[0]

                )

                base_risk = float(cluster["risk_score"].max())

                burst_signal = _calculate_error_burst_signal(

                    error_count

                )

                create_incident(

                    cluster,

                    incident_type="http_error_burst",

                    base_risk=base_risk,

                    burst_signal=burst_signal,

                    reason="HTTP error burst",

                    endpoint=endpoint,

                    error_count=error_count,

                )

    # =========================================================

    # 3. GENERIC ACTIVITY BURSTS

    # =========================================================

    # This detector is deliberately independent from authentication and

    # HTTP-error detection. The same events may therefore carry all three

    # temporal signals when the evidence supports it.

    activity_candidates = http.copy()

    for cluster in build_fixed_windows(

        activity_candidates,

        window_seconds=ACTIVITY_BURST_WINDOW_SECONDS,

    ):

        request_count = len(cluster)

        if request_count < ACTIVITY_BURST_MIN_REQUESTS:

            continue

        activity_spike = float(

            cluster["activity_spike_signal"].max()

        )

        if activity_spike < 0.35:

            continue

        base_risk = float(cluster["risk_score"].max())

        burst_signal = _calculate_activity_burst_signal(

            request_count

        )

        create_incident(

            cluster,

            incident_type="activity_burst",

            base_risk=base_risk,

            burst_signal=burst_signal,

            reason="short-term HTTP activity burst",

        )

    incidents.sort(

        key=lambda incident: (

            incident["risk_score"],

            incident["event_count"],

        ),

        reverse=True,

    )

    return work, incidents

# ---------------------------------------------------------------------------

# Reporting

# ---------------------------------------------------------------------------

def build_report(

    results: pd.DataFrame,

    incidents: list[dict],

) -> dict:

    http_results = results[

        results["is_http_request"] == 1

    ].copy()

    business_results = results[

        results["is_http_request"] == 0

    ].copy()

    risk_distribution = (

        results["risk_level"]

        .value_counts()

        .to_dict()

    )

    incident_distribution: dict[

        str,

        int,

    ] = {}

    incident_risk_distribution: dict[

        str,

        int,

    ] = {}

    for incident in incidents:

        incident_type = incident[

            "incident_type"

        ]

        risk_level = incident[

            "risk_level"

        ]

        incident_distribution[

            incident_type

        ] = (

            incident_distribution.get(

                incident_type,

                0,

            )

            + 1

        )

        incident_risk_distribution[

            risk_level

        ] = (

            incident_risk_distribution.get(

                risk_level,

                0,

            )

            + 1

        )

    def build_population_report(

        population: pd.DataFrame,

    ) -> dict:

        if population.empty:

            return {

                "rows": 0,

                "mean_risk_score": 0.0,

                "high_risk_count": 0,

                "medium_risk_count": 0,

                "low_risk_count": 0,

                "minimal_risk_count": 0,

            }

        return {

            "rows": int(len(population)),

            "mean_risk_score": round(

                float(

                    population[

                        "risk_score"

                    ].mean()

                ),

                6,

            ),

            "high_risk_count": int(

                (

                    population["risk_level"]

                    == "high"

                ).sum()

            ),

            "medium_risk_count": int(

                (

                    population["risk_level"]

                    == "medium"

                ).sum()

            ),

            "low_risk_count": int(

                (

                    population["risk_level"]

                    == "low"

                ).sum()

            ),

            "minimal_risk_count": int(

                (

                    population["risk_level"]

                    == "minimal"

                ).sum()

            ),

        }

    top_columns = [

        "id",

        "occurred_at",

        "risk_score",

        "risk_level",

        "risk_reasons",

        "anomaly_score",

        "anomaly_threshold",

        "behavioral_anomaly_signal",

        "auth_burst_id",

        "auth_burst_risk_score",

        "auth_burst_risk_level",

        "auth_burst_reason",

        "error_burst_id",

        "error_burst_risk_score",

        "error_burst_risk_level",

        "error_burst_reason",

        "activity_burst_id",

        "activity_burst_risk_score",

        "activity_burst_risk_level",

        "activity_burst_reason",

        "is_http_request",

        "action",

        "resource_type",

    ]

    optional_http_columns = [

        "method",

        "endpoint_normalized",

        "status_code",

        "is_error_status",

        "is_auth_failure",

    ]

    available_columns = [

        column

        for column in (

            top_columns

            + optional_http_columns

        )

        if column in results.columns

    ]

    top_risks = (

        results.sort_values(

            "risk_score",

            ascending=False,

        )

        [available_columns]

        .head(20)

        .copy()

    )

    if "occurred_at" in top_risks.columns:

        top_risks["occurred_at"] = (

            top_risks["occurred_at"]

            .astype(str)

        )

    if "risk_reasons" in top_risks.columns:

        top_risks["risk_reasons"] = (

            top_risks["risk_reasons"]

            .apply(

                lambda value:

                list(value)

                if isinstance(

                    value,

                    list,

                )

                else []

            )

        )

    return {

         "model_type": (
            "Hybrid Isolation Forest + deterministic "
            "explainable risk scoring with temporal "
            "incident aggregation"
        ),
        "description": (
            "Combines population-specific Isolation Forest "
            "behavioral anomaly scores with deterministic "
            "per-event risk signals and temporal clustering "
            "of authentication failures, HTTP errors, and "
            "short-term activity bursts."
        ),

        "total_rows": int(len(results)),

        "http_rows": int(len(http_results)),

        "business_rows": int(len(business_results)),

        "risk_distribution": {

            str(key): int(value)

            for key, value

            in risk_distribution.items()

        },

        "overall": build_population_report(

            results

        ),

        "http": build_population_report(

            http_results

        ),

        "business": build_population_report(

            business_results

        ),

        "weights": {

            "authentication_failure": (

                WEIGHT_AUTH_FAILURE

            ),

            "error_rate": (

                WEIGHT_ERROR_RATE

            ),

            "activity_spike": (

                WEIGHT_ACTIVITY_SPIKE

            ),

            "unusual_method": (

                WEIGHT_UNUSUAL_METHOD

            ),

            "unusual_endpoint": (

                WEIGHT_UNUSUAL_ENDPOINT

            ),

            "high_user_activity": (

                WEIGHT_HIGH_USER_ACTIVITY

            ),

            "behavioral_anomaly": (

                WEIGHT_BEHAVIORAL_ANOMALY

            ),

        },

        "behavioral_anomaly": {
            "model_type": "IsolationForest",
            "http_model_path": str(HTTP_MODEL_PATH),
            "business_model_path": str(BUSINESS_MODEL_PATH),
            "report_path": str(ANOMALY_REPORT_PATH),
            "signal_method": (
                "max(0, anomaly_score - calibrated_threshold) "
                "/ 0.04, clipped to [0, 1]"
            ),
            "http_threshold": safe_float(
                _load_anomaly_report()
                .get("http_model", {})
                .get("threshold", 0.0)
            ),
            "business_threshold": safe_float(
                _load_anomaly_report()
                .get("business_model", {})
                .get("threshold", 0.0)
            ),
        },

        "risk_levels": {

            "minimal": "< 0.20",

            "low": "0.20 - 0.449999",

            "medium": "0.45 - 0.749999",

            "high": ">= 0.75",

        },

        "temporal_detection": {

            "authentication_burst_window_seconds": (

                AUTH_BURST_WINDOW_SECONDS

            ),

            "authentication_burst_min_failures": (

                AUTH_BURST_MIN_FAILURES

            ),

            "error_burst_window_seconds": (

                ERROR_BURST_WINDOW_SECONDS

            ),

            "error_burst_min_errors": (

                ERROR_BURST_MIN_ERRORS

            ),

            "activity_burst_window_seconds": (

                ACTIVITY_BURST_WINDOW_SECONDS

            ),

            "activity_burst_min_requests": (

                ACTIVITY_BURST_MIN_REQUESTS

            ),

            "incident_count": int(

                len(incidents)

            ),

            "incident_distribution": (

                incident_distribution

            ),

            "incident_risk_distribution": (

                incident_risk_distribution

            ),

        },

        "top_risks": (

            top_risks.to_dict(

                orient="records"

            )

        ),

        "top_incidents": incidents[:20],

    }

def print_summary(

    results: pd.DataFrame,

    incidents: list[dict],

) -> None:

    print("\nRisk distribution:")

    distribution = (

        results["risk_level"]

        .value_counts()

    )

    for level in [

        "high",

        "medium",

        "low",

        "minimal",

    ]:

        print(

            f"  {level:8}: "

            f"{int(distribution.get(level, 0))}"

        )

    print(

        f"\nTemporal incidents: "

        f"{len(incidents)}"

    )

    if incidents:

        incident_distribution = {}

        for incident in incidents:

            incident_type = incident[

                "incident_type"

            ]

            incident_distribution[

                incident_type

            ] = (

                incident_distribution.get(

                    incident_type,

                    0,

                )

                + 1

            )

        print(

            "Incident types:"

        )

        for incident_type, count in sorted(

            incident_distribution.items()

        ):

            print(

                f"  {incident_type}: "

                f"{count}"

            )

    print("\nTop incidents:")

    if not incidents:

        print(

            "  No temporal incidents detected."

        )

    else:

        for incident in incidents[:10]:

            print(

                f"  "

                f"{incident['incident_id']} | "

                f"{incident['risk_level'].upper():6} | "

                f"{incident['risk_score']:.3f} | "

                f"{incident['event_count']} events | "

                f"{incident['reason']}"

            )

            if "endpoint" in incident:

                print(

                    f"    endpoint: "

                    f"{incident['endpoint']}"

                )

            if "failure_count" in incident:

                print(

                    f"    failures: "

                    f"{incident['failure_count']}"

                )

    print("\nTop risk observations:")

    columns = [

        "occurred_at",

        "risk_score",

        "risk_level",

        "auth_burst_id",

        "auth_burst_risk_level",

        "error_burst_id",

        "error_burst_risk_level",

        "activity_burst_id",

        "activity_burst_risk_level",

        "risk_reasons",

    ]

    optional_columns = [

        "method",

        "endpoint_normalized",

        "status_code",

        "action",

        "resource_type",

    ]

    selected_columns = [

        column

        for column in (

            columns

            + optional_columns

        )

        if column in results.columns

    ]

    display = (

        results.sort_values(

            "risk_score",

            ascending=False,

        )

        [selected_columns]

        .head(15)

        .copy()

    )

    print(

        display.to_string(

            index=False

        )

    )

# ---------------------------------------------------------------------------

# Main

# ---------------------------------------------------------------------------

def main() -> None:

    print("=" * 70)

    print("KBR ML RISK SCORING")

    print("=" * 70)

    print(

        "\n[1/4] Building feature dataset..."

    )

    features = (

        build_activity_feature_dataset()

    )

    print(

        f"Feature rows: {len(features)}"

    )

    print(

        "\n[2/5] Scoring behavioral anomalies..."

    )

    features = add_behavioral_anomaly_scores(

        features

    )

    print(

        f"Anomaly-scored rows: {len(features)}"

    )

    print(

        "\n[3/5] Calculating per-event risk..."

    )

    results = score_activity_dataset(

        features

    )

    print(

        f"Scored rows: {len(results)}"

    )

    print(

        "\n[4/5] Detecting temporal incidents..."

    )

    results, incidents = (

        detect_temporal_incidents(

            results

        )

    )

    print_summary(

        results,

        incidents,

    )

    print(

        "\n[5/5] Writing report..."

    )

    REPORT_DIR.mkdir(

        parents=True,

        exist_ok=True,

    )

    report = build_report(

        results,

        incidents,

    )

    REPORT_PATH.write_text(

        json.dumps(

            report,

            indent=2,

            default=str,

        ),

        encoding="utf-8",

    )

    print(

        f"Report: {REPORT_PATH}"

    )

    print("\n" + "=" * 70)

    print("RISK SCORING COMPLETED")

    print("=" * 70)

if __name__ == "__main__":

    main()