from backend.app.ai.context.models import (
    ContextItem,
    KBRContext,
)


def test_empty_context_is_empty():
    context = KBRContext(
        intent="events",
    )

    assert context.is_empty()


def test_context_prompt_contains_retrieved_data():
    context = KBRContext(
        intent="events",
        items=[
            ContextItem(
                type="event",
                title="KBR Tournament",
                content=(
                    "Start: 2026-09-10T18:00:00+00:00\n"
                    "Location: Bizerte"
                ),
            )
        ],
    )

    prompt = context.to_prompt()

    assert "RETRIEVED KBR DATABASE CONTEXT" in prompt
    assert "KBR Tournament" in prompt
    assert "Bizerte" in prompt