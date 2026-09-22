from backend.app.ai.prompts import KBR_SYSTEM_PROMPT


def test_kbr_system_prompt_contains_analytics_grounding() -> None:
    assert "ANALYTICS GROUNDING" in KBR_SYSTEM_PROMPT

    assert (
        "ANALYTICS RESULT"
        in KBR_SYSTEM_PROMPT
    )

    assert (
        "ANALYTICS TREND RESULT"
        in KBR_SYSTEM_PROMPT
    )

    assert (
        "ANALYTICS COMPARISON RESULT"
        in KBR_SYSTEM_PROMPT
    )


def test_kbr_system_prompt_requires_verified_values() -> None:
    assert (
        "Treat the supplied values as verified KBR data."
        in KBR_SYSTEM_PROMPT
    )

    assert (
        "Do not replace verified values with estimates or guesses."
        in KBR_SYSTEM_PROMPT
    )

    assert (
        "Do not contradict the supplied analytical values."
        in KBR_SYSTEM_PROMPT
    )


def test_kbr_system_prompt_prevents_unsupported_statistics() -> None:
    assert (
        "clearly explain that the statistic is currently unavailable"
        in KBR_SYSTEM_PROMPT
    )

    assert (
        "If analytical context states that a requested statistic is unsupported"
        in KBR_SYSTEM_PROMPT
    )


def test_kbr_system_prompt_protects_internal_analytics_details() -> None:
    assert "AnalyticsEngine" in KBR_SYSTEM_PROMPT
    assert "PostgreSQL" in KBR_SYSTEM_PROMPT
    assert "internal database queries" in KBR_SYSTEM_PROMPT


def test_kbr_system_prompt_preserves_kbr_identity() -> None:
    assert (
        "official AI assistant for Knights of Bizertin Rise (KBR)"
        in KBR_SYSTEM_PROMPT
    )

    assert (
        "Bizerte, Tunisia"
        in KBR_SYSTEM_PROMPT
    )