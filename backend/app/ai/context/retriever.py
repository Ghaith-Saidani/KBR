from __future__ import annotations

import re
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.ai.context.intent import AIIntent
from backend.app.ai.context.models import (
    ContextItem,
    KBRContext,
)
from backend.app.models import (
    Activity,
    ActivityStatus,
    Event,
    EventStatus,
    Member,
    MemberStatus,
    News,
    NewsStatus,
)


class KBRContextRetriever:
    """
    Retrieve public KBR information relevant to an AI request.

    Responsibilities:
    - query the database;
    - filter records that are safe for public AI use;
    - rank candidates against the user's query;
    - convert database records into ContextItem objects.

    The retriever never exposes private database fields such as:
    - user IDs;
    - creator IDs;
    - authentication information;
    - internal identifiers.

    Retrieval is intentionally deterministic and does not require
    another AI/LLM call.
    """

    MAX_MEMBERS = 20
    MAX_EVENTS = 10
    MAX_ACTIVITIES = 10
    MAX_NEWS = 10

    CANDIDATE_MULTIPLIER = 5

    _STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "at",
        "be",
        "can",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "when",
        "where",
        "who",
        "with",
        "you",
        "your",
        "de",
        "des",
        "du",
        "et",
        "est",
        "la",
        "le",
        "les",
        "un",
        "une",
        "pour",
        "dans",
        "sur",
        "avec",
        "qui",
        "que",
        "quoi",
        "comment",
        "quand",
        "où",
    }

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def retrieve(
        self,
        *,
        intent: AIIntent,
        query: str,
    ) -> KBRContext:
        """
        Retrieve structured KBR context based on intent and query.

        The query is used for deterministic relevance ranking.
        """

        if intent == AIIntent.EVENTS:
            return self._retrieve_events(query)

        if intent == AIIntent.MEMBERS:
            return self._retrieve_members(query)

        if intent == AIIntent.ACTIVITIES:
            return self._retrieve_activities(query)

        if intent == AIIntent.NEWS:
            return self._retrieve_news(query)

        if intent == AIIntent.ORGANIZATION:
            return self._retrieve_organization()

        if intent == AIIntent.JOIN:
            return self._retrieve_join_context()

        return self._retrieve_general_context()

    def _retrieve_events(
        self,
        query: str,
    ) -> KBRContext:
        """
        Retrieve published events.

        Upcoming events are preferred when available. Within the
        candidate set, query relevance is used for ranking while
        preserving a strong preference for upcoming events.
        """

        now = datetime.now(timezone.utc)

        upcoming = self.db.scalars(
            select(Event)
            .where(
                Event.status == EventStatus.PUBLISHED,
                Event.start_at >= now,
            )
            .order_by(Event.start_at.asc())
            .limit(
                self.MAX_EVENTS * self.CANDIDATE_MULTIPLIER
            )
        ).all()

        if upcoming:
            events = upcoming
        else:
            events = self.db.scalars(
                select(Event)
                .where(
                    Event.status == EventStatus.PUBLISHED,
                )
                .order_by(Event.start_at.desc())
                .limit(
                    self.MAX_EVENTS * self.CANDIDATE_MULTIPLIER
                )
            ).all()

        items = [
            ContextItem(
                type="event",
                title=event.title,
                content=self._event_content(event),
                relevance=self._event_relevance(
                    event,
                    query,
                    now,
                ),
            )
            for event in events
        ]

        items = self._rank_items(
            items,
            query=query,
            limit=self.MAX_EVENTS,
        )

        if not items:
            items.append(
                ContextItem(
                    type="event",
                    title="No published events",
                    content="No published KBR events were found.",
                )
            )

        return KBRContext(
            intent=AIIntent.EVENTS.value,
            items=items,
        )

    def _retrieve_members(
        self,
        query: str,
    ) -> KBRContext:
        members = self.db.scalars(
            select(Member)
            .where(
                Member.status == MemberStatus.ACTIVE,
            )
            .order_by(
                Member.first_name.asc(),
                Member.last_name.asc(),
            )
            .limit(
                self.MAX_MEMBERS * self.CANDIDATE_MULTIPLIER
            )
        ).all()

        items = [
            ContextItem(
                type="member",
                title=self._member_name(member),
                content=self._member_content(member),
                relevance=self._text_relevance(
                    query,
                    (
                        self._member_name(member),
                        member.position,
                        member.bio,
                    ),
                ),
            )
            for member in members
        ]

        items = self._rank_items(
            items,
            query=query,
            limit=self.MAX_MEMBERS,
        )

        if not items:
            items.append(
                ContextItem(
                    type="member",
                    title="No active members",
                    content="No active KBR members were found.",
                )
            )

        return KBRContext(
            intent=AIIntent.MEMBERS.value,
            items=items,
        )

    def _retrieve_activities(
        self,
        query: str,
    ) -> KBRContext:
        activities = self.db.scalars(
            select(Activity)
            .where(
                Activity.status == ActivityStatus.PUBLISHED,
            )
            .order_by(
                Activity.published_at.desc(),
                Activity.created_at.desc(),
            )
            .limit(
                self.MAX_ACTIVITIES * self.CANDIDATE_MULTIPLIER
            )
        ).all()

        items = [
            ContextItem(
                type="activity",
                title=activity.title,
                content=self._activity_content(activity),
                relevance=self._text_relevance(
                    query,
                    (
                        activity.title,
                        activity.excerpt,
                        activity.description,
                        activity.location,
                    ),
                ),
            )
            for activity in activities
        ]

        items = self._rank_items(
            items,
            query=query,
            limit=self.MAX_ACTIVITIES,
        )

        if not items:
            items.append(
                ContextItem(
                    type="activity",
                    title="No published activities",
                    content="No published KBR activities were found.",
                )
            )

        return KBRContext(
            intent=AIIntent.ACTIVITIES.value,
            items=items,
        )

    def _retrieve_news(
        self,
        query: str,
    ) -> KBRContext:
        news_items = self.db.scalars(
            select(News)
            .where(
                News.status == NewsStatus.PUBLISHED,
            )
            .order_by(
                News.published_at.desc(),
                News.created_at.desc(),
            )
            .limit(
                self.MAX_NEWS * self.CANDIDATE_MULTIPLIER
            )
        ).all()

        items = [
            ContextItem(
                type="news",
                title=news.title,
                content=self._news_content(news),
                relevance=self._text_relevance(
                    query,
                    (
                        news.title,
                        news.excerpt,
                        news.content,
                    ),
                ),
            )
            for news in news_items
        ]

        items = self._rank_items(
            items,
            query=query,
            limit=self.MAX_NEWS,
        )

        if not items:
            items.append(
                ContextItem(
                    type="news",
                    title="No published news",
                    content="No published KBR news was found.",
                )
            )

        return KBRContext(
            intent=AIIntent.NEWS.value,
            items=items,
        )

    def _retrieve_organization(self) -> KBRContext:
        """
        Static organization context.

        There is currently no Organization database model, so this
        information comes from the official KBR application context.
        """

        return KBRContext(
            intent=AIIntent.ORGANIZATION.value,
            items=[
                ContextItem(
                    type="organization",
                    title="Knights of Bizertin Rise",
                    content=(
                        "Short name: KBR\n"
                        "Location: Bizerte, Tunisia\n"
                        "Focus: Esports, gaming culture, community "
                        "activities, projects, events, and the local "
                        "gaming ecosystem."
                    ),
                ),
            ],
        )

    def _retrieve_join_context(self) -> KBRContext:
        """
        Current public join information.

        We keep this conservative until a dedicated membership/join
        configuration exists in the database.
        """

        return KBRContext(
            intent=AIIntent.JOIN.value,
            items=[
                ContextItem(
                    type="join",
                    title="Joining KBR",
                    content=(
                        "Membership is currently available.\n"
                        "Organization: Knights of Bizertin Rise\n"
                        "Location: Bizerte, Tunisia\n"
                        "The application should provide the official "
                        "membership process when it is configured."
                    ),
                ),
            ],
        )

    def _retrieve_general_context(self) -> KBRContext:
        """
        General questions receive deliberately small context.

        The whole database is never dumped into the AI context.
        """

        return KBRContext(
            intent=AIIntent.GENERAL.value,
            items=[
                ContextItem(
                    type="organization",
                    title="Knights of Bizertin Rise",
                    content=(
                        "Short name: KBR\n"
                        "Location: Bizerte, Tunisia\n"
                        "Focus: Esports, gaming culture, community "
                        "activities, projects, events, and the local "
                        "gaming ecosystem."
                    ),
                ),
            ],
        )

    @staticmethod
    def _member_name(
        member: Member,
    ) -> str:
        return (
            f"{member.first_name} "
            f"{member.last_name}"
        ).strip()

    @staticmethod
    def _member_content(
        member: Member,
    ) -> str:
        lines: list[str] = []

        if member.position:
            lines.append(
                f"Position: {member.position}"
            )

        if member.bio:
            lines.append(
                f"Bio: {member.bio}"
            )

        if member.joined_at:
            lines.append(
                f"Joined: "
                f"{KBRContextRetriever._format_date(member.joined_at)}"
            )

        return (
            "\n".join(lines)
            or "No additional public information."
        )

    @staticmethod
    def _event_content(
        event: Event,
    ) -> str:
        lines: list[str] = []

        if event.description:
            lines.append(
                f"Description: {event.description}"
            )

        if event.location:
            lines.append(
                f"Location: {event.location}"
            )

        if event.start_at:
            lines.append(
                f"Starts: "
                f"{KBRContextRetriever._format_datetime(event.start_at)}"
            )

        if event.end_at:
            lines.append(
                f"Ends: "
                f"{KBRContextRetriever._format_datetime(event.end_at)}"
            )

        return (
            "\n".join(lines)
            or "No additional public information."
        )

    @staticmethod
    def _activity_content(
        activity: Activity,
    ) -> str:
        lines: list[str] = []

        if activity.excerpt:
            lines.append(
                f"Summary: {activity.excerpt}"
            )

        lines.append(
            f"Description: {activity.description}"
        )

        if activity.location:
            lines.append(
                f"Location: {activity.location}"
            )

        if activity.start_at:
            lines.append(
                f"Starts: "
                f"{KBRContextRetriever._format_datetime(activity.start_at)}"
            )

        if activity.end_at:
            lines.append(
                f"Ends: "
                f"{KBRContextRetriever._format_datetime(activity.end_at)}"
            )

        if activity.published_at:
            lines.append(
                f"Published: "
                f"{KBRContextRetriever._format_datetime(activity.published_at)}"
            )

        return "\n".join(lines)

    @staticmethod
    def _news_content(
        news: News,
    ) -> str:
        lines: list[str] = []

        if news.excerpt:
            lines.append(
                f"Summary: {news.excerpt}"
            )

        lines.append(
            f"Content: {news.content}"
        )

        if news.published_at:
            lines.append(
                f"Published: "
                f"{KBRContextRetriever._format_datetime(news.published_at)}"
            )

        return "\n".join(lines)

    @classmethod
    def _text_relevance(
        cls,
        query: str,
        fields: tuple[object, ...],
    ) -> int:
        """
        Calculate deterministic relevance for a candidate.

        Scoring:
        - exact title token: strong weight;
        - field token match: moderate weight;
        - repeated matches: small additional weight.

        Common language stop words are ignored.
        """

        query_tokens = cls._tokenize(query)

        if not query_tokens:
            return 0

        title = str(fields[0] or "")
        title_tokens = set(cls._tokenize(title))

        other_tokens: set[str] = set()

        for field in fields[1:]:
            if field:
                other_tokens.update(
                    cls._tokenize(str(field))
                )

        score = 0

        for token in query_tokens:
            if token in title_tokens:
                score += 10
            elif token in other_tokens:
                score += 3

        return score

    @classmethod
    def _event_relevance(
        cls,
        event: Event,
        query: str,
        now: datetime,
    ) -> int:
        """
        Event relevance combines text matching with temporal relevance.

        Upcoming events receive a small base advantage so a question
        such as "next event" naturally keeps upcoming events first.
        """

        score = cls._text_relevance(
            query,
            (
                event.title,
                event.description,
                event.location,
            ),
        )

        if event.start_at:
            if event.start_at >= now:
                score += 2

                days_until = (
                    event.start_at - now
                ).total_seconds() / 86400

                if days_until <= 7:
                    score += 2
                elif days_until <= 30:
                    score += 1

        return score

    @classmethod
    def _rank_items(
        cls,
        items: list[ContextItem],
        *,
        query: str,
        limit: int,
    ) -> list[ContextItem]:
        """
        Rank context items by deterministic relevance.

        If the query has no meaningful tokens, preserve the original
        database ordering.
        """

        query_tokens = cls._tokenize(query)

        if not query_tokens:
            return items[:limit]

        return sorted(
            items,
            key=lambda item: item.relevance,
            reverse=True,
        )[:limit]

    @classmethod
    def _tokenize(
        cls,
        value: str,
    ) -> list[str]:
        """
        Normalize text into meaningful lowercase tokens.
        """

        normalized = value.lower()

        tokens = re.findall(
            r"[a-zA-ZÀ-ÿ0-9]+",
            normalized,
        )

        return [
            token
            for token in tokens
            if token not in cls._STOP_WORDS
            and len(token) > 1
        ]

    @staticmethod
    def _format_datetime(
        value: datetime,
    ) -> str:
        if value.tzinfo is not None:
            return value.strftime(
                "%B %d, %Y at %H:%M UTC"
            )

        return value.strftime(
            "%B %d, %Y at %H:%M"
        )

    @staticmethod
    def _format_date(
        value: date,
    ) -> str:
        return value.strftime(
            "%B %d, %Y"
        )


__all__ = [
    "KBRContextRetriever",
]