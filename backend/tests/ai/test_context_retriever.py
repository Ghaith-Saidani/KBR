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
from backend.app.models.user import UserRole
from backend.tests.conftest import create_test_user



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


def test_retriever_ranks_member_name_matches_first(
    db,
    member_user,
):
    second_member_user = create_test_user(
        db,
        role=UserRole.MEMBER,
    )

    first_member = Member(
        user_id=member_user.id,
        first_name="Ghaith",
        last_name="Developer",
        slug="ghaith-developer",
        position="Developer",
        bio="KBR developer.",
        status=MemberStatus.ACTIVE,
    )

    second_member = Member(
        user_id=second_member_user.id,
        first_name="Ahmed",
        last_name="Test",
        slug="ahmed-test",
        position="Community Manager",
        bio="Community manager.",
        status=MemberStatus.ACTIVE,
    )

    db.add_all(
        [
            first_member,
            second_member,
        ]
    )
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.MEMBERS,
        query="Tell me about Ghaith",
    )

    assert context.items[0].title == "Ghaith Developer"
    assert context.items[0].relevance > 0



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


def test_retriever_ranks_matching_event_first(
    db,
    admin_user,
):
    tournament = Event(
        title="KBR Esports Tournament",
        description="Competitive esports tournament.",
        location="Bizerte",
        start_at=(
            datetime.now(timezone.utc)
            + timedelta(days=14)
        ),
        status=EventStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    community_event = Event(
        title="KBR Community Meetup",
        description="A community gathering.",
        location="Bizerte",
        start_at=(
            datetime.now(timezone.utc)
            + timedelta(days=7)
        ),
        status=EventStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    db.add_all(
        [
            tournament,
            community_event,
        ]
    )
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.EVENTS,
        query="When is the esports tournament?",
    )

    assert context.items[0].title == "KBR Esports Tournament"
    assert context.items[0].relevance > 0


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


def test_retriever_ranks_matching_activity_first(
    db,
    admin_user,
):
    esports_activity = Activity(
        title="Esports Training",
        slug="esports-training",
        excerpt="Competitive esports training.",
        description="Training sessions for esports players.",
        status=ActivityStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    community_activity = Activity(
        title="Community Workshop",
        slug="community-workshop",
        excerpt="Community workshop.",
        description="A workshop for the KBR community.",
        status=ActivityStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    db.add_all(
        [
            esports_activity,
            community_activity,
        ]
    )
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.ACTIVITIES,
        query="Tell me about esports training",
    )

    assert context.items[0].title == "Esports Training"
    assert context.items[0].relevance > 0


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


def test_retriever_ranks_matching_news_first(
    db,
    admin_user,
):
    tournament_news = News(
        title="Esports Tournament Announcement",
        slug="esports-tournament-announcement",
        excerpt="Tournament announcement.",
        content="KBR announces a new esports tournament.",
        status=NewsStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    community_news = News(
        title="Community Update",
        slug="community-update",
        excerpt="Community update.",
        content="KBR shares a community update.",
        status=NewsStatus.PUBLISHED,
        created_by=admin_user.id,
    )

    db.add_all(
        [
            tournament_news,
            community_news,
        ]
    )
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.NEWS,
        query="Tell me about the esports tournament",
    )

    assert (
        context.items[0].title
        == "Esports Tournament Announcement"
    )
    assert context.items[0].relevance > 0


def test_retriever_does_not_expose_private_fields(
    db,
    member_user,
):
    member = Member(
        user_id=member_user.id,
        first_name="Private",
        last_name="Test",
        slug="private-test",
        position="Developer",
        bio="Public developer bio.",
        status=MemberStatus.ACTIVE,
    )

    db.add(member)
    db.flush()

    retriever = KBRContextRetriever(db)

    context = retriever.retrieve(
        intent=AIIntent.MEMBERS,
        query="Who is Private Test?",
    )

    prompt = context.to_prompt()

    assert "Private Test" in prompt
    assert "Public developer bio." in prompt
    assert "user_id" not in prompt
    assert "creator_id" not in prompt
    assert "password" not in prompt