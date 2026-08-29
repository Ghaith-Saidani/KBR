from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ContextItem:
    """
    A single piece of public KBR information retrieved from the database.
    """

    type: str
    title: str
    content: str
    relevance: int = 0


@dataclass(frozen=True)
class KBRContext:
    """
    Collection of database information relevant to an AI request.
    """

    intent: str
    items: list[ContextItem] = field(
        default_factory=list,
    )

    def is_empty(self) -> bool:
        return not self.items

    def to_prompt(self) -> str:
        """
        Convert retrieved information into a compact model context.
        """

        if self.is_empty():
            return (
                "No relevant KBR database information was found "
                "for this request."
            )

        lines: list[str] = [
            "RETRIEVED KBR DATABASE CONTEXT",
            "",
            f"Detected intent: {self.intent}",
            "",
        ]

        for index, item in enumerate(
            self.items,
            start=1,
        ):
            lines.append(
                f"[{index}] {item.type.upper()}: {item.title}"
            )
            lines.append(item.content)
            lines.append("")

        return "\n".join(lines).strip()


@dataclass(frozen=True)
class EventContext:
    title: str
    description: str | None
    location: str | None
    start_at: datetime
    end_at: datetime | None


@dataclass(frozen=True)
class MemberContext:
    first_name: str
    last_name: str
    position: str | None
    bio: str | None


@dataclass(frozen=True)
class ActivityContext:
    title: str
    excerpt: str | None
    description: str
    location: str | None
    start_at: datetime | None
    end_at: datetime | None


@dataclass(frozen=True)
class NewsContext:
    title: str
    excerpt: str | None
    content: str
    published_at: datetime | None


__all__ = [
    "ContextItem",
    "KBRContext",
    "EventContext",
    "MemberContext",
    "ActivityContext",
    "NewsContext",
]