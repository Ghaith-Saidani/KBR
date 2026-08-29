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


# ============================================================
# Configuration
# ============================================================

DEFAULT_PASSWORD = "KBRdemo2026!"

UTC = timezone.utc


# ============================================================
# Helpers
# ============================================================


def utc_now() -> datetime:
    return datetime.now(UTC)


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
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )

    db.add(user)
    db.flush()

    return user, True


# ============================================================
# Users
# ============================================================


def seed_users(db) -> dict[str, User]:
    users: dict[str, User] = {}

    definitions = [
        (
            "admin@kbr.tn",
            UserRole.ADMIN,
        ),
        (
            "staff@kbr.tn",
            UserRole.STAFF,
        ),
        (
            "president@kbr.tn",
            UserRole.MEMBER,
        ),
        (
            "vicepresident@kbr.tn",
            UserRole.MEMBER,
        ),
        (
            "secretary@kbr.tn",
            UserRole.MEMBER,
        ),
        (
            "esports@kbr.tn",
            UserRole.MEMBER,
        ),
        (
            "community@kbr.tn",
            UserRole.MEMBER,
        ),
        (
            "media@kbr.tn",
            UserRole.MEMBER,
        ),
    ]

    created_count = 0

    for email, role in definitions:
        user, created = create_or_get_user(
            db,
            email=email,
            role=role,
        )

        users[email] = user

        if created:
            created_count += 1

    print(
        f"Users: {len(users)} "
        f"({created_count} created)"
    )

    return users


# ============================================================
# Members
# ============================================================


def seed_members(
    db,
    users: dict[str, User],
) -> int:
    members = [
        {
            "email": "president@kbr.tn",
            "first_name": "Ghaith",
            "last_name": "Saidani",
            "slug": "ghaith-saidani",
            "position": "Président",
            "phone": None,
            "profile_image": None,
            "bio": (
                "Président de KBR, engagé dans le développement "
                "de la communauté gaming et esports à Bizerte."
            ),
            "joined_at": datetime(
                2025,
                9,
                15,
                tzinfo=UTC,
            ).date(),
        },
        {
            "email": "vicepresident@kbr.tn",
            "first_name": "Ahmed",
            "last_name": "Ben Salah",
            "slug": "ahmed-ben-salah",
            "position": "Vice-président",
            "phone": None,
            "profile_image": None,
            "bio": (
                "Participe à la coordination des projets "
                "et au développement des activités de KBR."
            ),
            "joined_at": datetime(
                2025,
                10,
                1,
                tzinfo=UTC,
            ).date(),
        },
        {
            "email": "secretary@kbr.tn",
            "first_name": "Yassine",
            "last_name": "Trabelsi",
            "slug": "yassine-trabelsi",
            "position": "Secrétaire général",
            "phone": None,
            "profile_image": None,
            "bio": (
                "Responsable de l'organisation administrative "
                "et du suivi des activités de l'association."
            ),
            "joined_at": datetime(
                2025,
                10,
                10,
                tzinfo=UTC,
            ).date(),
        },
        {
            "email": "esports@kbr.tn",
            "first_name": "Mohamed",
            "last_name": "Khelifi",
            "slug": "mohamed-khelifi",
            "position": "Responsable Esports",
            "phone": None,
            "profile_image": None,
            "bio": (
                "Coordonne les compétitions, entraînements "
                "et initiatives esports de KBR."
            ),
            "joined_at": datetime(
                2025,
                11,
                5,
                tzinfo=UTC,
            ).date(),
        },
        {
            "email": "community@kbr.tn",
            "first_name": "Mariem",
            "last_name": "Jaziri",
            "slug": "mariem-jaziri",
            "position": "Responsable Communauté",
            "phone": None,
            "profile_image": None,
            "bio": (
                "Anime la communauté KBR et participe à "
                "l'organisation des rencontres et ateliers."
            ),
            "joined_at": datetime(
                2025,
                11,
                20,
                tzinfo=UTC,
            ).date(),
        },
        {
            "email": "media@kbr.tn",
            "first_name": "Aziz",
            "last_name": "Mansouri",
            "slug": "aziz-mansouri",
            "position": "Responsable Média",
            "phone": None,
            "profile_image": None,
            "bio": (
                "En charge de la communication digitale, "
                "des contenus et de la couverture des événements."
            ),
            "joined_at": datetime(
                2026,
                1,
                10,
                tzinfo=UTC,
            ).date(),
        },
    ]

    created_count = 0

    for data in members:
        user = users[data["email"]]

        member = get_member_by_slug(
            db,
            data["slug"],
        )

        if member is None:
            member = Member(
                user_id=user.id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                slug=data["slug"],
                position=data["position"],
                phone=data["phone"],
                profile_image=data["profile_image"],
                bio=data["bio"],
                joined_at=data["joined_at"],
                status=MemberStatus.ACTIVE,
            )

            db.add(member)
            created_count += 1

    db.flush()

    print(
        f"Members: {len(members)} "
        f"({created_count} created)"
    )

    return len(members)


# ============================================================
# Events
# ============================================================


def seed_events(
    db,
    users: dict[str, User],
) -> int:
    now = utc_now()

    events = [
        {
            "title": "KBR Community Meetup",
            "description": (
                "Une rencontre ouverte aux passionnés de gaming, "
                "d'esports et de technologie. L'occasion de découvrir "
                "KBR, rencontrer la communauté et échanger autour "
                "des prochains projets."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": now + timedelta(days=14),
            "end_at": now + timedelta(days=14, hours=3),
            "status": EventStatus.PUBLISHED,
            "created_by": users["staff@kbr.tn"].id,
        },
        {
            "title": "KBR Esports Tournament",
            "description": (
                "Tournoi esports organisé par KBR réunissant les "
                "joueurs de la communauté autour d'une compétition "
                "conviviale et structurée."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": now + timedelta(days=30),
            "end_at": now + timedelta(days=30, hours=8),
            "status": EventStatus.PUBLISHED,
            "created_by": users["esports@kbr.tn"].id,
        },
        {
            "title": "Gaming Night KBR",
            "description": (
                "Une soirée dédiée au gaming et à la communauté KBR. "
                "Sessions de jeu, rencontres entre membres et "
                "activités communautaires."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": now + timedelta(days=45),
            "end_at": now + timedelta(days=45, hours=5),
            "status": EventStatus.PUBLISHED,
            "created_by": users["community@kbr.tn"].id,
        },
        {
            "title": "Atelier Création de Contenu",
            "description": (
                "Atelier consacré à la création de contenu autour "
                "du gaming : streaming, communication digitale, "
                "montage vidéo et identité en ligne."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": now + timedelta(days=60),
            "end_at": now + timedelta(days=60, hours=3),
            "status": EventStatus.PUBLISHED,
            "created_by": users["media@kbr.tn"].id,
        },
        {
            "title": "KBR Annual Community Gathering",
            "description": (
                "Grand rendez-vous annuel de la communauté KBR pour "
                "faire le bilan des activités, présenter les projets "
                "à venir et réunir les membres et partenaires."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": now + timedelta(days=90),
            "end_at": now + timedelta(days=90, hours=5),
            "status": EventStatus.DRAFT,
            "created_by": users["president@kbr.tn"].id,
        },
    ]

    created_count = 0

    for data in events:
        existing = get_event_by_title(
            db,
            data["title"],
        )

        if existing is not None:
            continue

        event = Event(
            title=data["title"],
            description=data["description"],
            location=data["location"],
            start_at=data["start_at"],
            end_at=data["end_at"],
            cover_image=None,
            status=data["status"],
            created_by=data["created_by"],
        )

        db.add(event)
        created_count += 1

    db.flush()

    print(
        f"Events: {len(events)} "
        f"({created_count} created)"
    )

    return len(events)


# ============================================================
# Activities
# ============================================================


def seed_activities(
    db,
    users: dict[str, User],
) -> int:
    now = utc_now()

    activities = [
        {
            "title": "Développement de l'Esports",
            "slug": "developpement-esports",
            "excerpt": (
                "Développer la pratique compétitive et "
                "accompagner les joueurs de la communauté."
            ),
            "description": (
                "KBR développe des activités dédiées à l'esports "
                "afin d'accompagner les joueurs, organiser des "
                "compétitions et créer un environnement favorable "
                "à la progression des talents locaux."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": datetime(
                2026,
                1,
                15,
                tzinfo=UTC,
            ),
            "end_at": None,
            "status": ActivityStatus.PUBLISHED,
            "published_at": datetime(
                2026,
                1,
                15,
                tzinfo=UTC,
            ),
            "created_by": users["esports@kbr.tn"].id,
        },
        {
            "title": "Communauté Gaming",
            "slug": "communaute-gaming",
            "excerpt": (
                "Créer un espace de rencontre et d'échange "
                "pour les passionnés de gaming."
            ),
            "description": (
                "Cette activité vise à rassembler les joueurs "
                "et passionnés de gaming autour de rencontres, "
                "discussions et événements communautaires."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": datetime(
                2026,
                2,
                1,
                tzinfo=UTC,
            ),
            "end_at": None,
            "status": ActivityStatus.PUBLISHED,
            "published_at": datetime(
                2026,
                2,
                1,
                tzinfo=UTC,
            ),
            "created_by": users["community@kbr.tn"].id,
        },
        {
            "title": "Ateliers Jeunesse et Technologie",
            "slug": "ateliers-jeunesse-technologie",
            "excerpt": (
                "Sensibiliser les jeunes aux usages créatifs "
                "et responsables du numérique."
            ),
            "description": (
                "KBR souhaite proposer des ateliers permettant "
                "aux jeunes de découvrir les différentes facettes "
                "du numérique, du gaming et de la création digitale."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": datetime(
                2026,
                3,
                1,
                tzinfo=UTC,
            ),
            "end_at": None,
            "status": ActivityStatus.PUBLISHED,
            "published_at": datetime(
                2026,
                3,
                1,
                tzinfo=UTC,
            ),
            "created_by": users["staff@kbr.tn"].id,
        },
        {
            "title": "Création de Contenu Digital",
            "slug": "creation-contenu-digital",
            "excerpt": (
                "Développer les compétences de la communauté "
                "dans la création de contenu gaming."
            ),
            "description": (
                "Cette initiative accompagne les membres intéressés "
                "par le streaming, la vidéo, les réseaux sociaux "
                "et la communication autour de l'esports."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": datetime(
                2026,
                4,
                1,
                tzinfo=UTC,
            ),
            "end_at": None,
            "status": ActivityStatus.PUBLISHED,
            "published_at": datetime(
                2026,
                4,
                1,
                tzinfo=UTC,
            ),
            "created_by": users["media@kbr.tn"].id,
        },
        {
            "title": "Programme Compétitif KBR",
            "slug": "programme-competitif-kbr",
            "excerpt": (
                "Un programme destiné à structurer "
                "l'accompagnement des joueurs compétitifs."
            ),
            "description": (
                "Le programme compétitif KBR a pour objectif de "
                "structurer les entraînements, favoriser la création "
                "d'équipes et accompagner les joueurs souhaitant "
                "participer à des compétitions."
            ),
            "location": "Bizerte, Tunisie",
            "start_at": datetime(
                2026,
                9,
                15,
                tzinfo=UTC,
            ),
            "end_at": None,
            "status": ActivityStatus.DRAFT,
            "published_at": None,
            "created_by": users["president@kbr.tn"].id,
        },
    ]

    created_count = 0

    for data in activities:
        existing = get_activity_by_slug(
            db,
            data["slug"],
        )

        if existing is not None:
            continue

        activity = Activity(
            title=data["title"],
            slug=data["slug"],
            excerpt=data["excerpt"],
            description=data["description"],
            cover_image=None,
            status=data["status"],
            start_at=data["start_at"],
            end_at=data["end_at"],
            location=data["location"],
            published_at=data["published_at"],
            created_by=data["created_by"],
        )

        db.add(activity)
        created_count += 1

    db.flush()

    print(
        f"Activities: {len(activities)} "
        f"({created_count} created)"
    )

    return len(activities)


# ============================================================
# News
# ============================================================


def seed_news(
    db,
    users: dict[str, User],
) -> int:
    news = [
        {
            "title": "KBR lance une nouvelle saison communautaire",
            "slug": "kbr-lance-nouvelle-saison-communautaire",
            "excerpt": (
                "KBR démarre une nouvelle saison dédiée au gaming, "
                "à l'esports et au développement de sa communauté."
            ),
            "content": (
                "KBR démarre une nouvelle saison avec l'objectif "
                "de renforcer les activités gaming et esports à "
                "Bizerte. Plusieurs rencontres, ateliers et "
                "compétitions seront progressivement proposés "
                "à la communauté."
            ),
        },
        {
            "title": "KBR développe ses activités esports",
            "slug": "kbr-developpe-activites-esports",
            "excerpt": (
                "De nouvelles initiatives sont prévues pour "
                "accompagner les joueurs compétitifs."
            ),
            "content": (
                "Le développement de l'esports constitue l'un des "
                "axes principaux de KBR. Le club travaille sur "
                "des entraînements, des rencontres compétitives "
                "et des événements permettant aux joueurs de "
                "progresser dans un cadre structuré."
            ),
        },
        {
            "title": "Une communauté au cœur du projet KBR",
            "slug": "communaute-au-coeur-projet-kbr",
            "excerpt": (
                "KBR souhaite construire une communauté active, "
                "inclusive et passionnée."
            ),
            "content": (
                "Au-delà de la compétition, KBR souhaite créer "
                "un véritable espace communautaire. Les rencontres "
                "et activités permettent aux membres de partager "
                "leur passion et de construire ensemble de nouveaux "
                "projets."
            ),
        },
        {
            "title": "KBR organise son prochain Community Meetup",
            "slug": "kbr-prochain-community-meetup",
            "excerpt": (
                "Une nouvelle rencontre communautaire sera bientôt "
                "organisée à Bizerte."
            ),
            "content": (
                "Le prochain KBR Community Meetup réunira les membres "
                "et les personnes intéressées par les activités du "
                "club. La rencontre permettra de présenter les "
                "projets à venir et d'échanger avec la communauté."
            ),
        },
        {
            "title": "La création de contenu rejoint les activités KBR",
            "slug": "creation-contenu-rejoint-activites-kbr",
            "excerpt": (
                "KBR développe désormais davantage d'activités "
                "autour de la création de contenu digital."
            ),
            "content": (
                "Le gaming moderne ne se limite plus à la compétition. "
                "La création de contenu, le streaming et la communication "
                "digitale occupent une place importante dans l'écosystème. "
                "KBR souhaite permettre à ses membres de développer "
                "leurs compétences dans ces domaines."
            ),
        },
        {
            "title": "KBR prépare ses prochains projets",
            "slug": "kbr-prepare-prochains-projets",
            "excerpt": (
                "De nouveaux projets communautaires et esports "
                "sont en préparation."
            ),
            "content": (
                "L'équipe KBR travaille actuellement sur plusieurs "
                "projets destinés à renforcer les activités du club. "
                "Les prochaines annonces seront publiées sur le site "
                "officiel et sur les différents canaux de communication "
                "de KBR."
            ),
        },
    ]

    published_date = datetime(
        2026,
        8,
        1,
        tzinfo=UTC,
    )

    created_count = 0

    for index, data in enumerate(news):
        existing = get_news_by_slug(
            db,
            data["slug"],
        )

        if existing is not None:
            continue

        article = News(
            title=data["title"],
            slug=data["slug"],
            excerpt=data["excerpt"],
            content=data["content"],
            cover_image=None,
            status=NewsStatus.PUBLISHED,
            published_at=published_date + timedelta(
                days=index,
            ),
            created_by=users["media@kbr.tn"].id,
        )

        db.add(article)
        created_count += 1

    db.flush()

    print(
        f"News: {len(news)} "
        f"({created_count} created)"
    )

    return len(news)


# ============================================================
# Contact messages
# ============================================================


def seed_contact_messages(
    db,
    users: dict[str, User],
) -> int:
    messages = [
        {
            "name": "Amine Ben Amor",
            "email": "amine.benamor@example.com",
            "subject": "Comment rejoindre KBR ?",
            "message": (
                "Bonjour, je souhaite rejoindre la communauté KBR "
                "et participer aux prochaines activités. Pouvez-vous "
                "m'indiquer comment procéder ?"
            ),
            "status": ContactMessageStatus.NEW,
            "user_id": None,
        },
        {
            "name": "Sarra Mejri",
            "email": "sarra.mejri@example.com",
            "subject": "Informations sur le prochain tournoi",
            "message": (
                "Bonjour, je voudrais avoir plus d'informations "
                "concernant le prochain tournoi KBR et les modalités "
                "d'inscription."
            ),
            "status": ContactMessageStatus.READ,
            "user_id": None,
        },
        {
            "name": "Tech Community Bizerte",
            "email": "contact@tech-community.example",
            "subject": "Proposition de partenariat",
            "message": (
                "Bonjour, notre communauté souhaiterait discuter "
                "d'une éventuelle collaboration avec KBR autour "
                "d'un événement gaming et technologique."
            ),
            "status": ContactMessageStatus.REPLIED,
            "user_id": None,
        },
        {
            "name": "KBR Member",
            "email": "community@kbr.tn",
            "subject": "Suggestion pour une activité",
            "message": (
                "Je souhaiterais proposer une nouvelle activité "
                "autour de la création de contenu et du streaming "
                "pour les membres de KBR."
            ),
            "status": ContactMessageStatus.NEW,
            "user_id": users["community@kbr.tn"].id,
        },
    ]

    created_count = 0

    for data in messages:
        existing = db.scalar(
            select(ContactMessage).where(
                ContactMessage.email == data["email"],
                ContactMessage.subject == data["subject"],
            )
        )

        if existing is not None:
            continue

        contact = ContactMessage(
            name=data["name"],
            email=data["email"],
            subject=data["subject"],
            message=data["message"],
            status=data["status"],
            user_id=data["user_id"],
        )

        db.add(contact)
        created_count += 1

    db.flush()

    print(
        f"Contact messages: {len(messages)} "
        f"({created_count} created)"
    )

    return len(messages)


# ============================================================
# Main
# ============================================================


def main() -> None:
    print()
    print("=" * 60)
    print("KBR DATABASE SEED")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        users = seed_users(db)

        seed_members(
            db,
            users,
        )

        seed_events(
            db,
            users,
        )

        seed_activities(
            db,
            users,
        )

        seed_news(
            db,
            users,
        )

        seed_contact_messages(
            db,
            users,
        )

        db.commit()

        print()
        print("=" * 60)
        print("KBR DATABASE SEED COMPLETED")
        print("=" * 60)
        print()
        print(
            "Demo account password:"
        )
        print(
            f"  {DEFAULT_PASSWORD}"
        )
        print()
        print(
            "Demo accounts:"
        )
        print(
            "  admin@kbr.tn"
        )
        print(
            "  staff@kbr.tn"
        )
        print(
            "  president@kbr.tn"
        )
        print(
            "  vicepresident@kbr.tn"
        )
        print(
            "  secretary@kbr.tn"
        )
        print(
            "  esports@kbr.tn"
        )
        print(
            "  community@kbr.tn"
        )
        print(
            "  media@kbr.tn"
        )
        print()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()