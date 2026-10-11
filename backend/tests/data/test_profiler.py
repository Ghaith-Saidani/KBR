import json

import pandas as pd

from backend.data.profile.profiler import profile_dataframe


def test_sensitive_columns_do_not_expose_top_values():
    df = pd.DataFrame(
        {
            "email": [
                "alice@example.com",
                "bob@example.com",
                "alice@example.com",
            ],
            "password_hash": [
                "hash-a",
                "hash-b",
                "hash-a",
            ],
            "role": [
                "ADMIN",
                "MEMBER",
                "ADMIN",
            ],
        }
    )

    profile = profile_dataframe(df, "users")

    columns = {
        column["name"]: column
        for column in profile["column_profiles"]
    }

    assert columns["email"]["sensitive"] is True
    assert columns["password_hash"]["sensitive"] is True

    assert "top_values" not in columns["email"]
    assert "top_values" not in columns["password_hash"]

    assert columns["role"]["sensitive"] is False
    assert columns["role"]["top_values"]


def test_nested_values_are_detected_without_exposing_contents():
    df = pd.DataFrame(
        {
            "id": ["1", "2"],
            "activity_metadata": [
                {"resource_name": "Event A", "changed_fields": ["title"]},
                {"resource_name": "Event B", "changed_fields": ["status"]},
            ],
        }
    )

    profile = profile_dataframe(df, "user_activities")

    assert "activity_metadata" in profile["nested_columns"]

    metadata_column = next(
        column
        for column in profile["column_profiles"]
        if column["name"] == "activity_metadata"
    )

    assert metadata_column["nested_values"] is True
    assert "top_values" not in metadata_column


def test_datetime_statistics_are_generated():
    df = pd.DataFrame(
        {
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-02-01T10:00:00Z",
                ],
                utc=True,
            )
        }
    )

    profile = profile_dataframe(df, "events")

    column = profile["column_profiles"][0]

    assert column["name"] == "created_at"
    assert column["statistics"]["min"] == "2026-01-01T10:00:00+00:00"
    assert column["statistics"]["max"] == "2026-02-01T10:00:00+00:00"


def test_numeric_statistics_are_generated():
    df = pd.DataFrame(
        {
            "value": [10, 20, 30, 40],
        }
    )

    profile = profile_dataframe(df, "metrics")

    column = profile["column_profiles"][0]
    statistics = column["statistics"]

    assert statistics["min"] == "10"
    assert statistics["max"] == "40"
    assert statistics["mean"] == 25.0
    assert statistics["median"] == 25.0


def test_profile_is_json_serializable():
    df = pd.DataFrame(
        {
            "role": ["ADMIN", "MEMBER"],
            "metadata": [
                {"source": "test"},
                {"source": "test"},
            ],
        }
    )

    profile = profile_dataframe(df, "test")

    serialized = json.dumps(profile)

    assert serialized