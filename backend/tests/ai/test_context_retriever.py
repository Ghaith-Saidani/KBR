from datetime import datetime, timedelta, timezone

from backend.app.ai.context import (
    AIIntent,
    KBRContext,
    KBRContextRetriever,
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


def test_retriever_returns_active_members(
    db,
    member_user,
):
    member = Member(
        user_id=member_user.id,
        first_name="Ghaith",
        last_name="Test",
        slug="ghaith-test",
        position="Developer",
        bio="KBR developer.",
        status=MemberStatus.ACTIVE,
    )

    db.add(member)
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.MEMBERS,
        query="Who are the KBR members?",
    )

    assert isinstance(context, KBRContext)
    assert context.intent == "members"
    assert len(context.items) == 1

    item = context.items[0]

    assert item.type == "member"
    assert item.title == "Ghaith Test"
    assert "Position: Developer" in item.content
    assert "Bio: KBR developer." in item.content


def test_retriever_returns_published_events(
    db,
    admin_user,
):
    event = Event(
        title="KBR Esports Tournament",
        description="A KBR tournament.",
        location="Bizerte",
        start_at=(
            datetime.now(timezone.utc)
            + timedelta(days=7)
        ),
        status=EventStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    db.add(event)
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.EVENTS,
        query="When is the next event?",
    )

    assert isinstance(context, KBRContext)
    assert context.intent == "events"
    assert len(context.items) == 1

    item = context.items[0]

    assert item.type == "event"
    assert item.title == "KBR Esports Tournament"
    assert "A KBR tournament." in item.content
    assert "Bizerte" in item.content


def test_retriever_excludes_draft_events(
    db,
    admin_user,
):
    event = Event(
        title="Private KBR Event",
        description="Draft event.",
        location="Bizerte",
        start_at=(
            datetime.now(timezone.utc)
            + timedelta(days=7)
        ),
        status=EventStatus.DRAFT,
        created_by=admin_user.id,
    )

    db.add(event)
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.EVENTS,
        query="What events are coming?",
    )

    assert context.intent == "events"
    assert len(context.items) == 1

    item = context.items[0]

    assert item.title == "No published events"
    assert "No published KBR events were found." in item.content


def test_retriever_returns_published_activities(
    db,
    admin_user,
):
    activity = Activity(
        title="KBR Community Project",
        slug="kbr-community-project",
        excerpt="Community project.",
        description="A KBR community project.",
        status=ActivityStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    db.add(activity)
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.ACTIVITIES,
        query="What activities does KBR have?",
    )

    assert isinstance(context, KBRContext)
    assert context.intent == "activities"
    assert len(context.items) == 1

    item = context.items[0]

    assert item.type == "activity"
    assert item.title == "KBR Community Project"
    assert "Community project." in item.content
    assert "A KBR community project." in item.content


def test_retriever_returns_published_news(
    db,
    admin_user,
):
    news = News(
        title="KBR Announcement",
        slug="kbr-announcement",
        excerpt="An announcement.",
        content="KBR has an announcement.",
        status=NewsStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    db.add(news)
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.NEWS,
        query="What is the latest KBR news?",
    )

    assert isinstance(context, KBRContext)
    assert context.intent == "news"
    assert len(context.items) == 1

    item = context.items[0]

    assert item.type == "news"
    assert item.title == "KBR Announcement"
    assert "An announcement." in item.content
    assert "KBR has an announcement." in item.content