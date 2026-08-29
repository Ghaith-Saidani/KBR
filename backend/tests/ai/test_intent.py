from backend.app.ai.context import (
    AIIntent,
    IntentDetector,
)


def test_detect_events_intent():
    detector = IntentDetector()

    assert (
        detector.detect(
            "When is the next event?"
        )
        == AIIntent.EVENTS
    )


def test_detect_members_intent():
    detector = IntentDetector()

    assert (
        detector.detect(
            "Who are the KBR members?"
        )
        == AIIntent.MEMBERS
    )


def test_detect_organization_intent():
    detector = IntentDetector()

    assert (
        detector.detect(
            "Tell me about KBR"
        )
        == AIIntent.ORGANIZATION
    )


def test_detect_join_intent():
    detector = IntentDetector()

    assert (
        detector.detect(
            "How can I join KBR?"
        )
        == AIIntent.JOIN
    )


def test_detect_activities_intent():
    detector = IntentDetector()

    assert (
        detector.detect(
            "What projects does KBR have?"
        )
        == AIIntent.ACTIVITIES
    )


def test_detect_news_intent():
    detector = IntentDetector()

    assert (
        detector.detect(
            "What is the latest KBR news?"
        )
        == AIIntent.NEWS
    )


def test_unknown_question_is_general():
    detector = IntentDetector()

    assert (
        detector.detect(
            "What is the weather today?"
        )
        == AIIntent.GENERAL
    )