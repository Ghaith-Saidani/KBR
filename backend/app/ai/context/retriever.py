from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.ai.context.intent import AIIntent
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
    Retrieves only the KBR information relevant to the user's request.

    This is the database/RAG retrieval layer.

    The retriever deliberately does not return private database fields
    such as user IDs, creator IDs, authentication information, etc.
    """

    MAX_MEMBERS = 20
    MAX_EVENTS = 10
    MAX_ACTIVITIES = 10
    MAX_NEWS = 10

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
    ) -> dict[str, object]:
        """
        Retrieve context based on the detected intent.
        """

        if intent == AIIntent.EVENTS:
            return self._retrieve_events()

        if intent == AIIntent.MEMBERS:
            return self._retrieve_members()

        if intent == AIIntent.ACTIVITIES:
            return self._retrieve_activities()

        if intent == AIIntent.NEWS:
            return self._retrieve_news()

        if intent == AIIntent.ORGANIZATION:
            return self._retrieve_organization()

        if intent == AIIntent.JOIN:
            return self._retrieve_join_context()

        return self._retrieve_general_context()

    def _retrieve_events(self) -> dict[str, object]:
        """
        Retrieve published events.

        Upcoming events are prioritized.
        """

        now = datetime.now(timezone.utc)

        upcoming = self.db.scalars(
            select(Event)
            .where(
                Event.status == EventStatus.PUBLISHED,
                Event.start_at >= now,
            )
            .order_by(Event.start_at.asc())
            .limit(self.MAX_EVENTS)
        ).all()

        if not upcoming:
            recent = self.db.scalars(
                select(Event)
                .where(
                    Event.status == EventStatus.PUBLISHED,
                )
                .order_by(Event.start_at.desc())
                .limit(self.MAX_EVENTS)
            ).all()
        else:
            recent = []

        events = upcoming or recent

        return {
            "intent": AIIntent.EVENTS.value,
            "events": [
                self._serialize_event(event)
                for event in events
            ],
        }

    def _retrieve_members(self) -> dict[str, object]:
        members = self.db.scalars(
            select(Member)
            .where(
                Member.status == MemberStatus.ACTIVE,
            )
            .order_by(
                Member.first_name.asc(),
                Member.last_name.asc(),
            )
            .limit(self.MAX_MEMBERS)
        ).all()

        return {
            "intent": AIIntent.MEMBERS.value,
            "members": [
                self._serialize_member(member)
                for member in members
            ],
        }

    def _retrieve_activities(self) -> dict[str, object]:
        activities = self.db.scalars(
            select(Activity)
            .where(
                Activity.status == ActivityStatus.PUBLISHED,
            )
            .order_by(
                Activity.published_at.desc(),
                Activity.created_at.desc(),
            )
            .limit(self.MAX_ACTIVITIES)
        ).all()

        return {
            "intent": AIIntent.ACTIVITIES.value,
            "activities": [
                self._serialize_activity(activity)
                for activity in activities
            ],
        }

    def _retrieve_news(self) -> dict[str, object]:
        news_items = self.db.scalars(
            select(News)
            .where(
                News.status == NewsStatus.PUBLISHED,
            )
            .order_by(
                News.published_at.desc(),
                News.created_at.desc(),
            )
            .limit(self.MAX_NEWS)
        ).all()

        return {
            "intent": AIIntent.NEWS.value,
            "news": [
                self._serialize_news(item)
                for item in news_items
            ],
        }

    def _retrieve_organization(self) -> dict[str, object]:
        """
        Static organization context.

        There is currently no Organization database model, so this
        information comes from the official KBR configuration/prompt.
        """

        return {
            "intent": AIIntent.ORGANIZATION.value,
            "organization": {
                "name": "Knights of Bizertin Rise",
                "short_name": "KBR",
                "location": "Bizerte, Tunisia",
                "focus": [
                    "Esports",
                    "gaming culture",
                    "community activities",
                    "projects",
                    "events",
                    "local gaming ecosystem",
                ],
            },
        }

    def _retrieve_join_context(self) -> dict[str, object]:
        """
        Current public join information.

        We keep this conservative until a dedicated membership/join
        configuration exists in the database.
        """

        return {
            "intent": AIIntent.JOIN.value,
            "join": {
                "available": True,
                "organization": "Knights of Bizertin Rise",
                "location": "Bizerte, Tunisia",
                "note": (
                    "The application should provide the official "
                    "membership process when it is configured."
                ),
            },
        }

    def _retrieve_general_context(self) -> dict[str, object]:
        """
        General questions receive a deliberately small context.

        We do NOT dump the whole database into Gemini.
        """

        return {
            "intent": AIIntent.GENERAL.value,
            "organization": {
                "name": "Knights of Bizertin Rise",
                "short_name": "KBR",
                "location": "Bizerte, Tunisia",
                "focus": [
                    "Esports",
                    "gaming culture",
                    "community activities",
                    "projects",
                    "events",
                    "local gaming ecosystem",
                ],
            },
        }

    @staticmethod
    def _serialize_member(
        member: Member,
    ) -> dict[str, object]:
        return {
            "name": (
                f"{member.first_name} "
                f"{member.last_name}"
            ).strip(),
            "position": member.position,
            "bio": member.bio,
            "joined_at": (
                member.joined_at.isoformat()
                if member.joined_at
                else None
            ),
        }

    @staticmethod
    def _serialize_event(
        event: Event,
    ) -> dict[str, object]:
        return {
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "start_at": (
                event.start_at.isoformat()
                if event.start_at
                else None
            ),
            "end_at": (
                event.end_at.isoformat()
                if event.end_at
                else None
            ),
        }

    @staticmethod
    def _serialize_activity(
        activity: Activity,
    ) -> dict[str, object]:
        return {
            "title": activity.title,
            "excerpt": activity.excerpt,
            "description": activity.description,
            "location": activity.location,
            "start_at": (
                activity.start_at.isoformat()
                if activity.start_at
                else None
            ),
            "end_at": (
                activity.end_at.isoformat()
                if activity.end_at
                else None
            ),
            "published_at": (
                activity.published_at.isoformat()
                if activity.published_at
                else None
            ),
        }

    @staticmethod
    def _serialize_news(
        news: News,
    ) -> dict[str, object]:
        return {
            "title": news.title,
            "excerpt": news.excerpt,
            "content": news.content,
            "published_at": (
                news.published_at.isoformat()
                if news.published_at
                else None
            ),
        }


__all__ = [
    "KBRContextRetriever",
]