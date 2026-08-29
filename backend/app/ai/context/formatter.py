from __future__ import annotations

from backend.app.ai.context.models import KBRContext


class KBRContextFormatter:
    """
    Convert structured KBR context into the prompt representation
    consumed by the AI service.

    Retrieval and formatting are intentionally separate responsibilities.
    """

    @staticmethod
    def format(
        context: KBRContext,
    ) -> str:
        if not context:
            return ""

        return context.to_prompt()


__all__ = [
    "KBRContextFormatter",
]