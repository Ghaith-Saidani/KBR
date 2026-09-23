from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models.activity import Activity, ActivityStatus
from backend.app.models.contact import (
    ContactMessage,
    ContactMessageStatus,
)
from backend.app.models.event import Event, EventStatus
from backend.app.models.member import Member, MemberStatus
from backend.app.models.news import News, NewsStatus
from backend.app.models.user import (
    User,
    UserRole,
    UserStatus,
)
from backend.app.models.user_activity import UserActivity


# ============================================================
# Configuration
# ============================================================

DEFAULT_PASSWORD = "KBRdemo2026!"

UTC = timezone.utc

SEED_START = datetime(
    2025,
    1,
    1,
    10,
    0,
    tzinfo=UTC,
)

SEED_END = datetime(
    2026,
    9,
    20,
    18,
    0,
    tzinfo=UTC,
)

SEED_AUDIT_PREFIX = "SEED:"

# Month-specific activity weights.
#
# This deliberately creates quiet and busy periods instead
# of distributing records uniformly.
MONTH_WEIGHTS = [
    (2025, 1, 3),
    (2025, 2, 2),
    (2025, 3, 4),
    (2025, 4, 1),
    (2025, 5, 3),
    (2025, 6, 4),
    (2025, 7, 2),
    (2025, 8, 5),
    (2025, 9, 3),
    (2025, 10, 2),
    (2025, 11, 4),
    (2025, 12, 2),
    (2026, 1, 3),
    (2026, 2, 4),
    (2026, 3, 2),
    (2026, 4, 4),
    (2026, 5, 3),
    (2026, 6, 5),
    (2026, 7, 4),
    (2026, 8, 9),
    (2026, 9, 4),
]


# ============================================================
# Helpers
# ============================================================


def utc_now() -> datetime:
    return datetime.now(UTC)


def historical_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
) -> datetime:
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=UTC,
    )


def get_user_by_email(
    db,
    email: str,
) -> User | None:
    return db.scalar(
        select(User).where(
            User.email == email,
        )
    )


def get_member_by_slug(
    db,
    slug: str,
) -> Member | None:
    return db.scalar(
        select(Member).where(
            Member.slug == slug,
        )
    )


def get_event_by_title(
    db,
    title: str,
) -> Event | None:
    return db.scalar(
        select(Event).where(
            Event.title == title,
        )
    )


def get_news_by_slug(
    db,
    slug: str,
) -> News | None:
    return db.scalar(
        select(News).where(
            News.slug == slug,
        )
    )


def get_activity_by_slug(
    db,
    slug: str,
) -> Activity | None:
    return db.scalar(
        select(Activity).where(
            Activity.slug == slug,
        )
    )


def create_or_get_user(
    db,
    *,
    email: str,
    role: UserRole,
    status: UserStatus = UserStatus.ACTIVE,
    created_at: datetime | None = None,
) -> tuple[User, bool]:
    user = get_user_by_email(
        db,
        email,
    )

    if user is not None:
        return user, False

    user = User(
        email=email,
        password_hash=hash_password(
            DEFAULT_PASSWORD,
        ),
        role=role,
        status=status,
        is_email_verified=(
            status != UserStatus.PENDING
        ),
    )

    if created_at is not None:
        user.created_at = created_at
        user.updated_at = created_at

    db.add(user)
    db.flush()

    return user, True


def set_created_at(
    instance,
    created_at: datetime,
) -> None:
    instance.created_at = created_at
    instance.updated_at = created_at


def month_date(
    year: int,
    month: int,
    day: int,
    offset_days: int = 0,
) -> datetime:
    value = datetime(
        year,
        month,
        day,
        10,
        0,
        tzinfo=UTC,
    )

    return value + timedelta(
        days=offset_days,
    )


def print_section(
    title: str,
) -> None:
    print()
    print("-" * 60)
    print(title)
    print("-" * 60)


# ============================================================
# Users
# ============================================================


def seed_users(db) -> dict[str, User]:
    users: dict[str, User] = {}

    definitions = [
        (
            "admin@kbr.tn",
            UserRole.ADMIN,
            UserStatus.ACTIVE,
            historical_datetime(2025, 1, 8),
        ),
        (
            "staff@kbr.tn",
            UserRole.STAFF,
            UserStatus.ACTIVE,
            historical_datetime(2025, 1, 15),
        ),
        (
            "president@kbr.tn",
            UserRole.MEMBER,
            UserStatus.ACTIVE,
            historical_datetime(2025, 9, 15),
        ),
        (
            "vicepresident@kbr.tn",
            UserRole.MEMBER,
            UserStatus.ACTIVE,
            historical_datetime(2025, 10, 1),
        ),
        (
            "secretary@kbr.tn",
            UserRole.MEMBER,
            UserStatus.ACTIVE,
            historical_datetime(2025, 10, 10),
        ),
        (
            "esports@kbr.tn",
            UserRole.MEMBER,
            UserStatus.ACTIVE,
            historical_datetime(2025, 11, 5),
        ),
        (
            "community@kbr.tn",
            UserRole.MEMBER,
            UserStatus.ACTIVE,
            historical_datetime(2025, 11, 20),
        ),
        (
            "media@kbr.tn",
            UserRole.MEMBER,
            UserStatus.ACTIVE,
            historical_datetime(2026, 1, 10),
        ),
    ]

    # Additional development members.
    member_names = [
        ("Amine", "Ben Amor"),
        ("Sarra", "Mejri"),
        ("Youssef", "Gharbi"),
        ("Malek", "Trabelsi"),
        ("Rayen", "Mansour"),
        ("Omar", "Jlassi"),
        ("Seif", "Khelifi"),
        ("Ahmed", "Mrad"),
        ("Marwen", "Ben Youssef"),
        ("Nour", "Chaabane"),
        ("Sami", "Dridi"),
        ("Houssem", "Karray"),
        ("Aymen", "Ferchichi"),
        ("Mohamed", "Baccouche"),
        ("Anis", "Ben Salem"),
        ("Fares", "Haddad"),
        ("Walid", "Ayari"),
        ("Karim", "Jaziri"),
        ("Mehdi", "Tlili"),
        ("Bilel", "Kacem"),
        ("Rami", "Sassi"),
        ("Wassim", "Ben Romdhane"),
        ("Skander", "Mansouri"),
        ("Iheb", "Guesmi"),
    ]

    member_join_dates = [
        historical_datetime(2025, 1, 20),
        historical_datetime(2025, 2, 12),
        historical_datetime(2025, 3, 8),
        historical_datetime(2025, 3, 25),
        historical_datetime(2025, 5, 4),
        historical_datetime(2025, 6, 18),
        historical_datetime(2025, 6, 28),
        historical_datetime(2025, 8, 5),
        historical_datetime(2025, 8, 18),
        historical_datetime(2025, 9, 7),
        historical_datetime(2025, 10, 14),
        historical_datetime(2025, 11, 3),
        historical_datetime(2025, 11, 19),
        historical_datetime(2025, 12, 9),
        historical_datetime(2026, 1, 6),
        historical_datetime(2026, 1, 24),
        historical_datetime(2026, 2, 11),
        historical_datetime(2026, 3, 3),
        historical_datetime(2026, 3, 22),
        historical_datetime(2026, 4, 10),
        historical_datetime(2026, 5, 2),
        historical_datetime(2026, 6, 12),
        historical_datetime(2026, 7, 9),
        historical_datetime(2026, 8, 6),
    ]

    for index, ((first_name, last_name), created_at) in enumerate(
        zip(
            member_names,
            member_join_dates,
            strict=True,
        ),
        start=1,
    ):
        email = (
            f"member{index:02d}"
            "@kbr.tn"
        )

        user, created = create_or_get_user(
            db,
            email=email,
            role=UserRole.MEMBER,
            status=UserStatus.ACTIVE,
            created_at=created_at,
        )

        users[email] = user

        if created:
            print(
                f"  created user: {email}"
            )

    created_count = 0

    for (
        email,
        role,
        status,
        created_at,
    ) in definitions:
        user, created = create_or_get_user(
            db,
            email=email,
            role=role,
            status=status,
            created_at=created_at,
        )

        users[email] = user

        if created:
            created_count += 1

    # Additional staff accounts.
    staff_definitions = [
        (
            "events@kbr.tn",
            historical_datetime(2026, 2, 5),
        ),
        (
            "operations@kbr.tn",
            historical_datetime(2026, 4, 15),
        ),
    ]

    for email, created_at in staff_definitions:
        user, created = create_or_get_user(
            db,
            email=email,
            role=UserRole.STAFF,
            status=UserStatus.ACTIVE,
            created_at=created_at,
        )

        users[email] = user

        if created:
            created_count += 1

    print(
        f"Users: {len(users)} "
        f"({created_count} core/staff accounts created)"
    )

    return users


# ============================================================
# Members
# ============================================================


def seed_members(
    db,
    users: dict[str, User],
) -> int:
    definitions = [
        {
            "email": "president@kbr.tn",
            "first_name": "Ghaith",
            "last_name": "Saidani",
            "slug": "ghaith-saidani",
            "position": "Président",
            "joined_at": historical_datetime(
                2025,
                9,
                15,
            ).date(),
            "status": MemberStatus.ACTIVE,
        },
        {
            "email": "vicepresident@kbr.tn",
            "first_name": "Ahmed",
            "last_name": "Ben Salah",
            "slug": "ahmed-ben-salah",
            "position": "Vice-président",
            "joined_at": historical_datetime(
                2025,
                10,
                1,
            ).date(),
            "status": MemberStatus.ACTIVE,
        },
        {
            "email": "secretary@kbr.tn",
            "first_name": "Yassine",
            "last_name": "Trabelsi",
            "slug": "yassine-trabelsi",
            "position": "Secrétaire général",
            "joined_at": historical_datetime(
                2025,
                10,
                10,
            ).date(),
            "status": MemberStatus.ACTIVE,
        },
        {
            "email": "esports@kbr.tn",
            "first_name": "Mohamed",
            "last_name": "Khelifi",
            "slug": "mohamed-khelifi",
            "position": "Responsable Esports",
            "joined_at": historical_datetime(
                2025,
                11,
                5,
            ).date(),
            "status": MemberStatus.ACTIVE,
        },
        {
            "email": "community@kbr.tn",
            "first_name": "Mariem",
            "last_name": "Jaziri",
            "slug": "mariem-jaziri",
            "position": "Responsable Communauté",
            "joined_at": historical_datetime(
                2025,
                11,
                20,
            ).date(),
            "status": MemberStatus.ACTIVE,
        },
        {
            "email": "media@kbr.tn",
            "first_name": "Aziz",
            "last_name": "Mansouri",
            "slug": "aziz-mansouri",
            "position": "Responsable Média",
            "joined_at": historical_datetime(
                2026,
                1,
                10,
            ).date(),
            "status": MemberStatus.ACTIVE,
        },
    ]

    additional_names = [
        ("Amine", "Ben Amor"),
        ("Sarra", "Mejri"),
        ("Youssef", "Gharbi"),
        ("Malek", "Trabelsi"),
        ("Rayen", "Mansour"),
        ("Omar", "Jlassi"),
        ("Seif", "Khelifi"),
        ("Ahmed", "Mrad"),
        ("Marwen", "Ben Youssef"),
        ("Nour", "Chaabane"),
        ("Sami", "Dridi"),
        ("Houssem", "Karray"),
        ("Aymen", "Ferchichi"),
        ("Mohamed", "Baccouche"),
        ("Anis", "Ben Salem"),
        ("Fares", "Haddad"),
        ("Walid", "Ayari"),
        ("Karim", "Jaziri"),
        ("Mehdi", "Tlili"),
        ("Bilel", "Kacem"),
        ("Rami", "Sassi"),
        ("Wassim", "Ben Romdhane"),
        ("Skander", "Mansouri"),
        ("Iheb", "Guesmi"),
    ]

    join_dates = [
        datetime(2025, 1, 20, tzinfo=UTC).date(),
        datetime(2025, 2, 12, tzinfo=UTC).date(),
        datetime(2025, 3, 8, tzinfo=UTC).date(),
        datetime(2025, 3, 25, tzinfo=UTC).date(),
        datetime(2025, 5, 4, tzinfo=UTC).date(),
        datetime(2025, 6, 18, tzinfo=UTC).date(),
        datetime(2025, 6, 28, tzinfo=UTC).date(),
        datetime(2025, 8, 5, tzinfo=UTC).date(),
        datetime(2025, 8, 18, tzinfo=UTC).date(),
        datetime(2025, 9, 7, tzinfo=UTC).date(),
        datetime(2025, 10, 14, tzinfo=UTC).date(),
        datetime(2025, 11, 3, tzinfo=UTC).date(),
        datetime(2025, 11, 19, tzinfo=UTC).date(),
        datetime(2025, 12, 9, tzinfo=UTC).date(),
        datetime(2026, 1, 6, tzinfo=UTC).date(),
        datetime(2026, 1, 24, tzinfo=UTC).date(),
        datetime(2026, 2, 11, tzinfo=UTC).date(),
        datetime(2026, 3, 3, tzinfo=UTC).date(),
        datetime(2026, 3, 22, tzinfo=UTC).date(),
        datetime(2026, 4, 10, tzinfo=UTC).date(),
        datetime(2026, 5, 2, tzinfo=UTC).date(),
        datetime(2026, 6, 12, tzinfo=UTC).date(),
        datetime(2026, 7, 9, tzinfo=UTC).date(),
        datetime(2026, 8, 6, tzinfo=UTC).date(),
    ]

    positions = [
        "Membre",
        "Joueur Esports",
        "Créateur de contenu",
        "Community Member",
        "Bénévole",
        "Membre actif",
    ]

    for index, (
        (first_name, last_name),
        joined_at,
    ) in enumerate(
        zip(
            additional_names,
            join_dates,
            strict=True,
        ),
        start=1,
    ):
        email = f"member{index:02d}@kbr.tn"
        slug = (
            f"{first_name}-{last_name}"
            .lower()
            .replace(" ", "-")
        )

        member = get_member_by_slug(
            db,
            slug,
        )

        if member is not None:
            continue

        member = Member(
            user_id=users[email].id,
            first_name=first_name,
            last_name=last_name,
            slug=slug,
            position=positions[
                (index - 1) % len(positions)
            ],
            phone=None,
            profile_image=None,
            bio=(
                f"Membre de la communauté KBR "
                f"à Bizerte. Passionné par le gaming, "
                f"l'esports et les initiatives numériques."
            ),
            joined_at=joined_at,
            status=(
                MemberStatus.INACTIVE
                if index in {7, 17}
                else (
                    MemberStatus.ARCHIVED
                    if index == 22
                    else MemberStatus.ACTIVE
                )
            ),
        )

        created_at = datetime.combine(
            joined_at,
            datetime.min.time(),
            tzinfo=UTC,
        )

        set_created_at(
            member,
            created_at,
        )

        db.add(member)

    db.flush()

    created_count = 0

    for data in definitions:
        member = get_member_by_slug(
            db,
            data["slug"],
        )

        if member is not None:
            continue

        member = Member(
            user_id=users[data["email"]].id,
            first_name=data["first_name"],
            last_name=data["last_name"],
            slug=data["slug"],
            position=data["position"],
            phone=None,
            profile_image=None,
            bio=(
                "Membre actif de la communauté KBR "
                "à Bizerte et participant aux initiatives "
                "gaming et esports."
            ),
            joined_at=data["joined_at"],
            status=data["status"],
        )

        created_at = datetime.combine(
            data["joined_at"],
            datetime.min.time(),
            tzinfo=UTC,
        )

        set_created_at(
            member,
            created_at,
        )

        db.add(member)
        created_count += 1

    db.flush()

    total = db.scalar(
        select(Member.id)
    )

    print(
        f"Members seeded: {len(definitions) + len(additional_names)}"
    )

    return len(definitions) + len(additional_names)


# ============================================================
# Events
# ============================================================


def seed_events(
    db,
    users: dict[str, User],
) -> int:
    definitions = [
        (
            "KBR Community Meetup 2025",
            "Rencontre communautaire autour du gaming et de l'esports.",
            "Bizerte, Tunisie",
            datetime(2025, 2, 22, 14, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2025, 1, 20, tzinfo=UTC),
        ),
        (
            "KBR Spring Gaming Night",
            "Soirée gaming et rencontres entre membres.",
            "Bizerte, Tunisie",
            datetime(2025, 3, 29, 18, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2025, 3, 5, tzinfo=UTC),
        ),
        (
            "KBR Esports Cup #1",
            "Première coupe esports de la saison.",
            "Bizerte, Tunisie",
            datetime(2025, 4, 26, 10, tzinfo=UTC),
            EventStatus.CANCELLED,
            "esports@kbr.tn",
            datetime(2025, 4, 1, tzinfo=UTC),
        ),
        (
            "Workshop Streaming",
            "Atelier pratique consacré au streaming.",
            "Bizerte, Tunisie",
            datetime(2025, 5, 17, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2025, 5, 2, tzinfo=UTC),
        ),
        (
            "KBR Summer Tournament",
            "Tournoi communautaire d'été.",
            "Bizerte, Tunisie",
            datetime(2025, 6, 21, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2025, 6, 1, tzinfo=UTC),
        ),
        (
            "Community Meetup June",
            "Rencontre mensuelle de la communauté.",
            "Bizerte, Tunisie",
            datetime(2025, 6, 28, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2025, 6, 10, tzinfo=UTC),
        ),
        (
            "KBR Gaming Night July",
            "Soirée gaming communautaire.",
            "Bizerte, Tunisie",
            datetime(2025, 7, 19, 18, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2025, 7, 2, tzinfo=UTC),
        ),
        (
            "KBR Esports Cup #2",
            "Deuxième compétition esports de la saison.",
            "Bizerte, Tunisie",
            datetime(2025, 8, 9, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2025, 7, 20, tzinfo=UTC),
        ),
        (
            "Content Creator Meetup",
            "Rencontre dédiée aux créateurs de contenu.",
            "Bizerte, Tunisie",
            datetime(2025, 8, 23, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2025, 8, 2, tzinfo=UTC),
        ),
        (
            "KBR Community Day",
            "Journée communautaire KBR.",
            "Bizerte, Tunisie",
            datetime(2025, 9, 13, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "president@kbr.tn",
            datetime(2025, 8, 25, tzinfo=UTC),
        ),
        (
            "Autumn Esports Workshop",
            "Atelier de préparation aux compétitions.",
            "Bizerte, Tunisie",
            datetime(2025, 10, 11, 14, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2025, 9, 25, tzinfo=UTC),
        ),
        (
            "KBR Digital Communication Lab",
            "Atelier communication digitale.",
            "Bizerte, Tunisie",
            datetime(2025, 11, 8, 14, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2025, 10, 20, tzinfo=UTC),
        ),
        (
            "KBR Year-End Meetup",
            "Dernière rencontre communautaire de l'année.",
            "Bizerte, Tunisie",
            datetime(2025, 12, 20, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2025, 11, 30, tzinfo=UTC),
        ),
        (
            "KBR New Year Community Meetup",
            "Première rencontre communautaire de 2026.",
            "Bizerte, Tunisie",
            datetime(2026, 1, 24, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2026, 1, 5, tzinfo=UTC),
        ),
        (
            "KBR Winter Esports Cup",
            "Compétition esports hivernale.",
            "Bizerte, Tunisie",
            datetime(2026, 2, 21, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2026, 2, 1, tzinfo=UTC),
        ),
        (
            "Women in Gaming Meetup",
            "Rencontre communautaire autour de la diversité dans le gaming.",
            "Bizerte, Tunisie",
            datetime(2026, 3, 14, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2026, 2, 20, tzinfo=UTC),
        ),
        (
            "Spring Content Workshop",
            "Atelier de création de contenu.",
            "Bizerte, Tunisie",
            datetime(2026, 4, 18, 14, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2026, 4, 1, tzinfo=UTC),
        ),
        (
            "KBR Community Tournament",
            "Tournoi communautaire de printemps.",
            "Bizerte, Tunisie",
            datetime(2026, 5, 23, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2026, 5, 2, tzinfo=UTC),
        ),
        (
            "KBR Summer Kickoff",
            "Lancement de la programmation estivale.",
            "Bizerte, Tunisie",
            datetime(2026, 6, 13, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2026, 6, 1, tzinfo=UTC),
        ),
        (
            "KBR Summer Esports Cup",
            "Grande compétition estivale.",
            "Bizerte, Tunisie",
            datetime(2026, 7, 18, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2026, 7, 1, tzinfo=UTC),
        ),
        (
            "KBR Gaming Festival",
            "Festival gaming et esports de la communauté.",
            "Bizerte, Tunisie",
            datetime(2026, 8, 15, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "president@kbr.tn",
            datetime(2026, 8, 1, tzinfo=UTC),
        ),
        (
            "KBR Creator Day",
            "Journée dédiée aux créateurs de contenu.",
            "Bizerte, Tunisie",
            datetime(2026, 8, 22, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2026, 8, 5, tzinfo=UTC),
        ),
        (
            "KBR Community Meetup August",
            "Rencontre mensuelle de la communauté.",
            "Bizerte, Tunisie",
            datetime(2026, 8, 29, 15, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2026, 8, 10, tzinfo=UTC),
        ),
        (
            "KBR September Tournament",
            "Tournoi de rentrée de la communauté.",
            "Bizerte, Tunisie",
            datetime(2026, 9, 19, 10, tzinfo=UTC),
            EventStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2026, 8, 28, tzinfo=UTC),
        ),
        (
            "KBR Autumn Planning",
            "Réunion de préparation des projets d'automne.",
            "Bizerte, Tunisie",
            datetime(2026, 10, 10, 15, tzinfo=UTC),
            EventStatus.DRAFT,
            "staff@kbr.tn",
            datetime(2026, 9, 5, tzinfo=UTC),
        ),
        (
            "KBR Annual Gathering 2026",
            "Grand rassemblement annuel de la communauté.",
            "Bizerte, Tunisie",
            datetime(2026, 12, 12, 10, tzinfo=UTC),
            EventStatus.DRAFT,
            "president@kbr.tn",
            datetime(2026, 9, 12, tzinfo=UTC),
        ),
    ]

    created_count = 0

    for (
        title,
        description,
        location,
        start_at,
        status,
        creator_email,
        created_at,
    ) in definitions:
        existing = get_event_by_title(
            db,
            title,
        )

        if existing is not None:
            continue

        end_at = start_at + timedelta(
            hours=3,
        )

        event = Event(
            title=title,
            description=description,
            location=location,
            start_at=start_at,
            end_at=end_at,
            cover_image=None,
            status=status,
            created_by=users[creator_email].id,
        )

        set_created_at(
            event,
            created_at,
        )

        db.add(event)
        created_count += 1

    db.flush()

    print(
        f"Events: {len(definitions)} "
        f"({created_count} created)"
    )

    return len(definitions)


# ============================================================
# Activities
# ============================================================


def seed_activities(
    db,
    users: dict[str, User],
) -> int:
    definitions = [
        (
            "Développement de l'Esports",
            "developpement-esports",
            "Développer la pratique compétitive.",
            datetime(2025, 2, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2025, 1, 20, tzinfo=UTC),
        ),
        (
            "Communauté Gaming",
            "communaute-gaming",
            "Créer un espace de rencontre gaming.",
            datetime(2025, 3, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2025, 2, 10, tzinfo=UTC),
        ),
        (
            "Ateliers Jeunesse et Technologie",
            "ateliers-jeunesse-technologie",
            "Sensibiliser les jeunes au numérique.",
            datetime(2025, 4, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2025, 3, 15, tzinfo=UTC),
        ),
        (
            "Création de Contenu Digital",
            "creation-contenu-digital",
            "Développer les compétences de création digitale.",
            datetime(2025, 5, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2025, 4, 10, tzinfo=UTC),
        ),
        (
            "Programme Compétitif KBR",
            "programme-competitif-kbr",
            "Structurer l'accompagnement des joueurs.",
            datetime(2025, 6, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2025, 5, 15, tzinfo=UTC),
        ),
        (
            "Initiation au Streaming",
            "initiation-streaming",
            "Découvrir les bases du streaming.",
            datetime(2025, 7, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2025, 6, 12, tzinfo=UTC),
        ),
        (
            "Atelier Tournoi et Organisation",
            "atelier-tournoi-organisation",
            "Apprendre à organiser une compétition.",
            datetime(2025, 8, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2025, 7, 8, tzinfo=UTC),
        ),
        (
            "Mentorat Joueurs",
            "mentorat-joueurs",
            "Accompagnement des joueurs de la communauté.",
            datetime(2025, 9, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2025, 8, 4, tzinfo=UTC),
        ),
        (
            "KBR Media Lab",
            "kbr-media-lab",
            "Création et production de contenus.",
            datetime(2025, 10, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2025, 9, 9, tzinfo=UTC),
        ),
        (
            "Community Volunteer Program",
            "community-volunteer-program",
            "Programme de bénévolat communautaire.",
            datetime(2025, 11, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2025, 10, 12, tzinfo=UTC),
        ),
        (
            "KBR Digital Skills",
            "kbr-digital-skills",
            "Ateliers autour des compétences numériques.",
            datetime(2025, 12, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2025, 11, 6, tzinfo=UTC),
        ),
        (
            "Esports Training 2026",
            "esports-training-2026",
            "Sessions structurées d'entraînement esports.",
            datetime(2026, 1, 15, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2026, 1, 4, tzinfo=UTC),
        ),
        (
            "Community Mentoring",
            "community-mentoring",
            "Mentorat entre membres.",
            datetime(2026, 2, 15, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2026, 2, 4, tzinfo=UTC),
        ),
        (
            "Women in Gaming Initiative",
            "women-in-gaming",
            "Initiative communautaire autour du gaming.",
            datetime(2026, 3, 15, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "staff@kbr.tn",
            datetime(2026, 3, 2, tzinfo=UTC),
        ),
        (
            "Content Creator Program",
            "content-creator-program",
            "Programme pour les créateurs de contenu.",
            datetime(2026, 4, 15, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "media@kbr.tn",
            datetime(2026, 4, 3, tzinfo=UTC),
        ),
        (
            "Summer Gaming Program",
            "summer-gaming-program",
            "Programmation gaming estivale.",
            datetime(2026, 6, 1, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "community@kbr.tn",
            datetime(2026, 5, 8, tzinfo=UTC),
        ),
        (
            "KBR Competitive Academy",
            "kbr-competitive-academy",
            "Programme avancé pour joueurs compétitifs.",
            datetime(2026, 7, 15, tzinfo=UTC),
            ActivityStatus.PUBLISHED,
            "esports@kbr.tn",
            datetime(2026, 7, 1, tzinfo=UTC),
        ),
        (
            "KBR Autumn Competitive Program",
            "kbr-autumn-competitive-program",
            "Programme compétitif de rentrée.",
            datetime(2026, 9, 15, tzinfo=UTC),
            ActivityStatus.DRAFT,
            "president@kbr.tn",
            datetime(2026, 9, 3, tzinfo=UTC),
        ),
    ]

    created_count = 0

    for (
        title,
        slug,
        excerpt,
        start_at,
        status,
        creator_email,
        created_at,
    ) in definitions:
        existing = get_activity_by_slug(
            db,
            slug,
        )

        if existing is not None:
            continue

        published_at = (
            created_at
            if status == ActivityStatus.PUBLISHED
            else None
        )

        activity = Activity(
            title=title,
            slug=slug,
            excerpt=excerpt,
            description=(
                f"{excerpt} Cette initiative fait partie "
                f"des activités de développement de KBR "
                f"à Bizerte."
            ),
            cover_image=None,
            status=status,
            start_at=start_at,
            end_at=None,
            location="Bizerte, Tunisie",
            published_at=published_at,
            created_by=users[creator_email].id,
        )

        set_created_at(
            activity,
            created_at,
        )

        db.add(activity)
        created_count += 1

    db.flush()

    print(
        f"Activities: {len(definitions)} "
        f"({created_count} created)"
    )

    return len(definitions)


# ============================================================
# News
# ============================================================


def seed_news(
    db,
    users: dict[str, User],
) -> int:
    definitions = [
        (
            "KBR lance une nouvelle saison communautaire",
            "kbr-lance-nouvelle-saison-communautaire",
            datetime(2025, 1, 25, tzinfo=UTC),
        ),
        (
            "KBR développe ses activités esports",
            "kbr-developpe-activites-esports",
            datetime(2025, 2, 18, tzinfo=UTC),
        ),
        (
            "Une communauté au cœur du projet KBR",
            "communaute-au-coeur-projet-kbr",
            datetime(2025, 3, 20, tzinfo=UTC),
        ),
        (
            "KBR organise son premier Community Meetup",
            "kbr-premier-community-meetup",
            datetime(2025, 5, 10, tzinfo=UTC),
        ),
        (
            "La création de contenu rejoint KBR",
            "creation-contenu-rejoint-kbr",
            datetime(2025, 6, 8, tzinfo=UTC),
        ),
        (
            "KBR prépare son tournoi d'été",
            "kbr-prepare-tournoi-ete",
            datetime(2025, 6, 25, tzinfo=UTC),
        ),
        (
            "Retour sur la Summer Gaming Night",
            "retour-summer-gaming-night",
            datetime(2025, 7, 24, tzinfo=UTC),
        ),
        (
            "KBR annonce sa deuxième Esports Cup",
            "kbr-deuxieme-esports-cup",
            datetime(2025, 8, 1, tzinfo=UTC),
        ),
        (
            "KBR renforce son équipe communautaire",
            "kbr-renforce-equipe-communautaire",
            datetime(2025, 9, 12, tzinfo=UTC),
        ),
        (
            "Nouveaux ateliers pour les membres",
            "nouveaux-ateliers-membres",
            datetime(2025, 10, 5, tzinfo=UTC),
        ),
        (
            "KBR développe son programme compétitif",
            "kbr-programme-competitif",
            datetime(2025, 11, 12, tzinfo=UTC),
        ),
        (
            "Bilan de la saison 2025",
            "bilan-saison-2025",
            datetime(2025, 12, 20, tzinfo=UTC),
        ),
        (
            "KBR démarre 2026 avec de nouveaux projets",
            "kbr-demarre-2026-nouveaux-projets",
            datetime(2026, 1, 12, tzinfo=UTC),
        ),
        (
            "Ouverture du programme de mentorat",
            "ouverture-programme-mentorat",
            datetime(2026, 2, 8, tzinfo=UTC),
        ),
        (
            "KBR soutient les initiatives Women in Gaming",
            "kbr-women-in-gaming",
            datetime(2026, 3, 10, tzinfo=UTC),
        ),
        (
            "Nouveau programme de création de contenu",
            "nouveau-programme-creation-contenu",
            datetime(2026, 4, 15, tzinfo=UTC),
        ),
        (
            "KBR prépare la saison estivale",
            "kbr-prepare-saison-estivale",
            datetime(2026, 5, 20, tzinfo=UTC),
        ),
        (
            "La KBR Competitive Academy ouvre ses portes",
            "kbr-competitive-academy",
            datetime(2026, 7, 5, tzinfo=UTC),
        ),
        (
            "Retour sur le KBR Gaming Festival",
            "retour-kbr-gaming-festival",
            datetime(2026, 8, 18, tzinfo=UTC),
        ),
        (
            "KBR prépare la rentrée esports",
            "kbr-prepare-rentree-esports",
            datetime(2026, 8, 28, tzinfo=UTC),
        ),
        (
            "KBR annonce son tournoi de septembre",
            "kbr-tournoi-septembre",
            datetime(2026, 9, 5, tzinfo=UTC),
        ),
        (
            "Les prochains projets de KBR",
            "prochains-projets-kbr",
            datetime(2026, 9, 15, tzinfo=UTC),
        ),
    ]

    created_count = 0

    for (
        title,
        slug,
        created_at,
    ) in definitions:
        existing = get_news_by_slug(
            db,
            slug,
        )

        if existing is not None:
            continue

        article = News(
            title=title,
            slug=slug,
            excerpt=(
                f"{title}. Retrouvez les dernières "
                f"actualités de la communauté KBR."
            ),
            content=(
                f"{title}. KBR poursuit le développement "
                f"de ses activités gaming, esports, "
                f"communautaires et numériques à Bizerte."
            ),
            cover_image=None,
            status=NewsStatus.PUBLISHED,
            published_at=created_at,
            created_by=users["media@kbr.tn"].id,
        )

        set_created_at(
            article,
            created_at,
        )

        db.add(article)
        created_count += 1

    db.flush()

    print(
        f"News: {len(definitions)} "
        f"({created_count} created)"
    )

    return len(definitions)


# ============================================================
# Contact messages
# ============================================================


def seed_contact_messages(
    db,
    users: dict[str, User],
) -> int:
    definitions = [
        (
            "Amine Ben Amor",
            "amine.benamor@example.com",
            "Comment rejoindre KBR ?",
            ContactMessageStatus.NEW,
            None,
            datetime(2025, 2, 5, tzinfo=UTC),
        ),
        (
            "Sarra Mejri",
            "sarra.mejri@example.com",
            "Informations sur le prochain tournoi",
            ContactMessageStatus.READ,
            None,
            datetime(2025, 6, 10, tzinfo=UTC),
        ),
        (
            "Tech Community Bizerte",
            "contact@tech-community.example",
            "Proposition de partenariat",
            ContactMessageStatus.REPLIED,
            None,
            datetime(2025, 8, 18, tzinfo=UTC),
        ),
        (
            "KBR Member",
            "community@kbr.tn",
            "Suggestion pour une activité",
            ContactMessageStatus.NEW,
            users["community@kbr.tn"].id,
            datetime(2026, 3, 15, tzinfo=UTC),
        ),
        (
            "Gaming Community",
            "gaming-community@example.com",
            "Demande de partenariat",
            ContactMessageStatus.READ,
            None,
            datetime(2026, 7, 10, tzinfo=UTC),
        ),
    ]

    created_count = 0

    for (
        name,
        email,
        subject,
        status,
        user_id,
        created_at,
    ) in definitions:
        existing = db.scalar(
            select(ContactMessage).where(
                ContactMessage.email == email,
                ContactMessage.subject == subject,
            )
        )

        if existing is not None:
            continue

        contact = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=(
                f"Message de démonstration KBR : {subject}."
            ),
            status=status,
            user_id=user_id,
        )

        set_created_at(
            contact,
            created_at,
        )

        db.add(contact)
        created_count += 1

    db.flush()

    print(
        f"Contact messages: {len(definitions)} "
        f"({created_count} created)"
    )

    return len(definitions)


# ============================================================
# Audit / User activities
# ============================================================


def seed_user_activities(
    db,
    users: dict[str, User],
) -> int:
    """
    Generate deterministic business-oriented audit data.

    Records use a SEED: prefix so the function can be safely
    rerun without creating duplicates.
    """

    existing_seeded = db.scalar(
        select(UserActivity.id).where(
            UserActivity.details.like(
                f"{SEED_AUDIT_PREFIX}%"
            )
        ).limit(1)
    )

    if existing_seeded is not None:
        print(
            "Audit logs: seeded audit data already exists"
        )
        return 0

    admin_id = users["admin@kbr.tn"].id
    staff_id = users["staff@kbr.tn"].id
    esports_id = users["esports@kbr.tn"].id
    community_id = users["community@kbr.tn"].id
    media_id = users["media@kbr.tn"].id

    actions = [
        (
            "LOGIN",
            admin_id,
            None,
            None,
            "Authentication réussie",
        ),
        (
            "LOGIN",
            staff_id,
            None,
            None,
            "Authentication réussie",
        ),
        (
            "MEMBER_UPDATED",
            admin_id,
            "member",
            None,
            "Membre mis à jour",
        ),
        (
            "EVENT_CREATED",
            staff_id,
            "event",
            None,
            "Événement créé",
        ),
        (
            "EVENT_PUBLISHED",
            esports_id,
            "event",
            None,
            "Événement publié",
        ),
        (
            "ACTIVITY_CREATED",
            staff_id,
            "activity",
            None,
            "Activité créée",
        ),
        (
            "NEWS_CREATED",
            media_id,
            "news",
            None,
            "Article créé",
        ),
        (
            "NEWS_PUBLISHED",
            media_id,
            "news",
            None,
            "Article publié",
        ),
        (
            "MEMBER_REACTIVATED",
            admin_id,
            "member",
            None,
            "Membre réactivé",
        ),
        (
            "EVENT_UPDATED",
            staff_id,
            "event",
            None,
            "Événement mis à jour",
        ),
    ]

    created_count = 0

    for index in range(160):
        year, month, weight = MONTH_WEIGHTS[
            index % len(MONTH_WEIGHTS)
        ]

        # Use the month as the deterministic anchor.
        day = 2 + (index % 24)

        if (
            year == 2026
            and month == 9
            and day > 20
        ):
            day = 20

        occurred_at = datetime(
            year,
            month,
            day,
            9 + (index % 9),
            (index * 7) % 60,
            tzinfo=UTC,
        )

        action, user_id, resource_type, _, label = (
            actions[index % len(actions)]
        )

        details = (
            f"{SEED_AUDIT_PREFIX}"
            f"{occurred_at:%Y-%m-%d}: "
            f"{label} #{index + 1}"
        )

        activity = UserActivity(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=None,
            method=(
                "POST"
                if action.endswith("CREATED")
                else "PATCH"
            ),
            endpoint="/seed/development",
            ip_address="127.0.0.1",
            user_agent="KBR Development Seed",
            details=details,
            activity_metadata={
                "seed": True,
                "seed_index": index + 1,
                "period": f"{year:04d}-{month:02d}",
                "weight": weight,
            },
            occurred_at=occurred_at,
        )

        set_created_at(
            activity,
            occurred_at,
        )

        db.add(activity)
        created_count += 1

    db.flush()

    print(
        f"Audit logs: {created_count} created"
    )

    return created_count


# ============================================================
# Statistics
# ============================================================


def print_seed_summary(db) -> None:
    user_count = db.scalar(
        select(User.id)
    )

    member_count = db.scalar(
        select(Member.id)
    )

    event_count = db.scalar(
        select(Event.id)
    )

    activity_count = db.scalar(
        select(Activity.id)
    )

    news_count = db.scalar(
        select(News.id)
    )

    audit_count = db.scalar(
        select(UserActivity.id)
    )

    # The scalar queries above intentionally only verify that
    # records exist. Detailed counts are obtained below with
    # SQLAlchemy count expressions.
    from sqlalchemy import func

    counts = {
        "Users": db.scalar(
            select(func.count(User.id))
        ),
        "Members": db.scalar(
            select(func.count(Member.id))
        ),
        "Events": db.scalar(
            select(func.count(Event.id))
        ),
        "Activities": db.scalar(
            select(func.count(Activity.id))
        ),
        "News": db.scalar(
            select(func.count(News.id))
        ),
        "Audit logs": db.scalar(
            select(func.count(UserActivity.id))
        ),
        "Contacts": db.scalar(
            select(func.count(ContactMessage.id))
        ),
    }

    print_section(
        "DATABASE SUMMARY"
    )

    for label, count in counts.items():
        print(
            f"{label:<15}: {count}"
        )


def print_creation_timeline(db) -> None:
    """
    Print monthly creation timelines without relying on PostgreSQL
    GROUP BY/date_trunc expression matching.

    The seed data is already committed before this reporting step,
    so this function is intentionally read-only. Fetching timestamps
    and aggregating them in Python also avoids PostgreSQL treating
    repeated date_trunc() bind parameters as different expressions.
    """
    from collections import Counter

    print_section(
        "CREATION TIMELINE"
    )

    def print_model_timeline(
        label: str,
        model,
    ) -> None:
        rows = db.execute(
            select(model.created_at)
        ).scalars().all()

        counts = Counter(
            created_at.strftime("%Y-%m")
            for created_at in rows
            if created_at is not None
        )

        print(f"{label}:")

        for month, count in sorted(
            counts.items()
        ):
            print(
                f"  {month}: {count}"
            )

    print_model_timeline(
        "Users",
        User,
    )

    print()

    print_model_timeline(
        "Events",
        Event,
    )

    print()

    print_model_timeline(
        "Activities",
        Activity,
    )

    print()

    print_model_timeline(
        "News",
        News,
    )


# ============================================================
# Main
# ============================================================


def main() -> None:
    print()
    print("=" * 60)
    print("KBR DATABASE SEED")
    print("=" * 60)
    print()
    print(
        "Historical range:"
        f" {SEED_START:%Y-%m-%d}"
        f" → {SEED_END:%Y-%m-%d}"
    )

    db = SessionLocal()

    try:
        print_section(
            "USERS"
        )

        users = seed_users(db)

        print_section(
            "MEMBERS"
        )

        seed_members(
            db,
            users,
        )

        print_section(
            "EVENTS"
        )

        seed_events(
            db,
            users,
        )

        print_section(
            "ACTIVITIES"
        )

        seed_activities(
            db,
            users,
        )

        print_section(
            "NEWS"
        )

        seed_news(
            db,
            users,
        )

        print_section(
            "CONTACT MESSAGES"
        )

        seed_contact_messages(
            db,
            users,
        )

        print_section(
            "AUDIT LOGS"
        )

        seed_user_activities(
            db,
            users,
        )

        db.commit()

        print_seed_summary(
            db
        )

        print_creation_timeline(
            db
        )

        print()
        print("=" * 60)
        print("KBR DATABASE SEED COMPLETED")
        print("=" * 60)
        print()
        print(
            "Demo password:"
        )
        print(
            f"  {DEFAULT_PASSWORD}"
        )
        print()
        print(
            "Core demo accounts:"
        )

        for email in [
            "admin@kbr.tn",
            "staff@kbr.tn",
            "president@kbr.tn",
            "vicepresident@kbr.tn",
            "secretary@kbr.tn",
            "esports@kbr.tn",
            "community@kbr.tn",
            "media@kbr.tn",
        ]:
            print(
                f"  {email}"
            )

        print()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()