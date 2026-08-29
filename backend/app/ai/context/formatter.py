from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.ai.context.models import KBRContext


class KBRContextFormatter:
    """
    Convert retrieved KBR information into compact,
    human-readable model context.

    The formatter deliberately avoids exposing internal database
    identifiers and converts ISO timestamps into readable dates.
    """

    @staticmethod
    def format(
        context: dict[str, Any] | KBRContext,
    ) -> str:
        if not context:
            return ""

        if isinstance(context, KBRContext):
            return context.to_prompt()

        lines: list[str] = [
            "RETRIEVED KBR DATABASE CONTEXT",
            "The following information was retrieved from the "
            "KBR application database.",
            "Use it as authoritative information for dynamic KBR data.",
            "Do not invent information that is not present here.",
            "",
        ]

        intent = context.get("intent")

        if intent:
            lines.append(f"Detected intent: {intent}")
            lines.append("")

        if "organization" in context:
            lines.extend(
                KBRContextFormatter._format_organization(
                    context["organization"],
                )
            )

        if "members" in context:
            lines.extend(
                KBRContextFormatter._format_members(
                    context["members"],
                )
            )

        if "events" in context:
            lines.extend(
                KBRContextFormatter._format_events(
                    context["events"],
                )
            )

        if "activities" in context:
            lines.extend(
                KBRContextFormatter._format_activities(
                    context["activities"],
                )
            )

        if "news" in context:
            lines.extend(
                KBRContextFormatter._format_news(
                    context["news"],
                )
            )

        if "join" in context:
            lines.extend(
                KBRContextFormatter._format_join(
                    context["join"],
                )
            )

        return "\n".join(lines).strip()

    @staticmethod
    def _format_organization(
        organization: Any,
    ) -> list[str]:
        if not isinstance(organization, dict):
            return []

        lines = [
            "ORGANIZATION",
            f"Name: {organization.get('name', '')}",
            f"Short name: {organization.get('short_name', '')}",
            f"Location: {organization.get('location', '')}",
        ]

        focus = organization.get("focus")

        if isinstance(focus, list) and focus:
            lines.append(
                "Focus: " + ", ".join(str(item) for item in focus)
            )

        lines.append("")
        return lines

    @staticmethod
    def _format_members(
        members: Any,
    ) -> list[str]:
        if not isinstance(members, list):
            return []

        lines = ["MEMBERS"]

        if not members:
            lines.append("No active KBR members were found.")
            lines.append("")
            return lines

        for index, member in enumerate(members, start=1):
            if not isinstance(member, dict):
                continue

            name = member.get("name") or "Unknown"
            position = member.get("position")
            bio = member.get("bio")
            joined_at = KBRContextFormatter._format_datetime(
                member.get("joined_at")
            )

            lines.append(f"[{index}] {name}")

            if position:
                lines.append(f"Position: {position}")

            if bio:
                lines.append(f"Bio: {bio}")

            if joined_at:
                lines.append(f"Joined: {joined_at}")

            lines.append("")

        return lines

    @staticmethod
    def _format_events(
        events: Any,
    ) -> list[str]:
        if not isinstance(events, list):
            return []

        lines = ["EVENTS"]

        if not events:
            lines.append("No published events were found.")
            lines.append("")
            return lines

        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                continue

            title = event.get("title") or "Untitled event"

            lines.append(f"[{index}] {title}")

            description = event.get("description")
            if description:
                lines.append(f"Description: {description}")

            location = event.get("location")
            if location:
                lines.append(f"Location: {location}")

            start_at = KBRContextFormatter._format_datetime(
                event.get("start_at")
            )
            if start_at:
                lines.append(f"Starts: {start_at}")

            end_at = KBRContextFormatter._format_datetime(
                event.get("end_at")
            )
            if end_at:
                lines.append(f"Ends: {end_at}")

            lines.append("")

        return lines

    @staticmethod
    def _format_activities(
        activities: Any,
    ) -> list[str]:
        if not isinstance(activities, list):
            return []

        lines = ["ACTIVITIES"]

        if not activities:
            lines.append("No published activities were found.")
            lines.append("")
            return lines

        for index, activity in enumerate(activities, start=1):
            if not isinstance(activity, dict):
                continue

            title = activity.get("title") or "Untitled activity"

            lines.append(f"[{index}] {title}")

            excerpt = activity.get("excerpt")
            if excerpt:
                lines.append(f"Summary: {excerpt}")

            description = activity.get("description")
            if description:
                lines.append(f"Description: {description}")

            location = activity.get("location")
            if location:
                lines.append(f"Location: {location}")

            start_at = KBRContextFormatter._format_datetime(
                activity.get("start_at")
            )
            if start_at:
                lines.append(f"Starts: {start_at}")

            end_at = KBRContextFormatter._format_datetime(
                activity.get("end_at")
            )
            if end_at:
                lines.append(f"Ends: {end_at}")

            published_at = KBRContextFormatter._format_datetime(
                activity.get("published_at")
            )
            if published_at:
                lines.append(f"Published: {published_at}")

            lines.append("")

        return lines

    @staticmethod
    def _format_news(
        news_items: Any,
    ) -> list[str]:
        if not isinstance(news_items, list):
            return []

        lines = ["NEWS"]

        if not news_items:
            lines.append("No published news was found.")
            lines.append("")
            return lines

        for index, news in enumerate(news_items, start=1):
            if not isinstance(news, dict):
                continue

            title = news.get("title") or "Untitled news"

            lines.append(f"[{index}] {title}")

            excerpt = news.get("excerpt")
            if excerpt:
                lines.append(f"Summary: {excerpt}")

            content = news.get("content")
            if content:
                lines.append(f"Content: {content}")

            published_at = KBRContextFormatter._format_datetime(
                news.get("published_at")
            )
            if published_at:
                lines.append(f"Published: {published_at}")

            lines.append("")

        return lines

    @staticmethod
    def _format_join(
        join: Any,
    ) -> list[str]:
        if not isinstance(join, dict):
            return []

        lines = [
            "JOIN KBR",
            f"Available: {join.get('available', False)}",
        ]

        organization = join.get("organization")
        if organization:
            lines.append(f"Organization: {organization}")

        location = join.get("location")
        if location:
            lines.append(f"Location: {location}")

        note = join.get("note")
        if note:
            lines.append(f"Note: {note}")

        lines.append("")
        return lines

    @staticmethod
    def _format_datetime(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.strftime("%B %d, %Y at %H:%M UTC")

        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )

                if parsed.tzinfo is not None:
                    return parsed.strftime(
                        "%B %d, %Y at %H:%M UTC"
                    )

                return parsed.strftime(
                    "%B %d, %Y at %H:%M"
                )

            except ValueError:
                return value

        return str(value)


__all__ = [
    "KBRContextFormatter",
]