from sqlalchemy.orm import Session

from backend.app.ai.context import AIIntent, IntentDetector
from backend.app.analytics import AnalyticsEngine


def test_total_members_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How many members does KBR have?"
    )

    assert result is not None
    assert result.metric == "total_members"
    assert result.value >= 0


def test_active_members_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How many active members are there?"
    )

    assert result is not None
    assert result.metric == "active_members"
    assert result.value >= 0


def test_published_events_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How many published events are there?"
    )

    assert result is not None
    assert result.metric == "published_events"
    assert result.value >= 0


def test_upcoming_events_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How many upcoming events are there?"
    )

    assert result is not None
    assert result.metric == "upcoming_events"
    assert result.value >= 0


def test_published_activities_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How many published activities are there?"
    )

    assert result is not None
    assert result.metric == "published_activities"
    assert result.value >= 0


def test_published_news_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How many published news articles are there?"
    )

    assert result is not None
    assert result.metric == "published_news"
    assert result.value >= 0


def test_member_growth_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "How has membership grown?"
    )

    assert result is not None
    assert result.metric == "members_created_per_month"
    assert len(result.months) == 6

    for month, value in result.months:
        assert len(month) == 7
        assert value >= 0


def test_event_growth_analytics(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "Show me the event trends."
    )

    assert result is not None
    assert result.metric == "events_created_per_month"
    assert len(result.months) == 6


def test_unsupported_analytics_query_returns_none(
    db: Session,
) -> None:
    engine = AnalyticsEngine(db)

    result = engine.analyze(
        "What is the average age of KBR members?"
    )

    assert result is None


def test_intent_detector_routes_analytics_questions() -> None:
    detector = IntentDetector()

    assert (
        detector.detect(
            "How many members does KBR have?"
        )
        == AIIntent.ANALYTICS
    )

    assert (
        detector.detect(
            "How has membership grown?"
        )
        == AIIntent.ANALYTICS
    )

    def test_events_created_in_month_analytics(
        db: Session,
    ) -> None:
        engine = AnalyticsEngine(db)

        result = engine.analyze(
            "How many events were created in August 2026?"
        )

        assert result is not None
        assert result.metric == "events_created_in_period"
        assert result.start_date.isoformat() == "2026-08-01"
        assert result.end_date.isoformat() == "2026-08-31"
        assert result.value >= 0


    def test_members_created_last_three_months(
        db: Session,
    ) -> None:
        engine = AnalyticsEngine(db)

        result = engine.analyze(
            "How many members joined in the last 3 months?"
        )

        assert result is not None
        assert result.metric == "members_created_in_period"
        assert result.value >= 0
        assert result.start_date is not None
        assert result.end_date is not None


    def test_events_between_two_months(
        db: Session,
    ) -> None:
        engine = AnalyticsEngine(db)

        result = engine.analyze(
            "How many events were created between June and September?"
        )

        assert result is not None
        assert result.metric == "events_created_in_period"
        assert result.value >= 0


    def test_event_month_comparison(
        db: Session,
    ) -> None:
        engine = AnalyticsEngine(db)

        result = engine.analyze(
            "Compare events between June and September."
        )

        assert result is not None
        assert result.metric == "events_created_comparison"
        assert result.first_value >= 0
        assert result.second_value >= 0
        assert result.difference == (
            result.second_value - result.first_value
        )