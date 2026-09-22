from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.analytics.models import (
    AnalyticsComparisonResult,
    AnalyticsResult,
    AnalyticsTrendResult,
)
from backend.app.services.statistics import (
    get_statistics_overview,
    get_statistics_trends,
)


class AnalyticsEngine:
    """
    Deterministic analytics engine for KBR.

    The engine is deliberately independent from the LLM.

    Responsibilities:
    - interpret supported analytical requests;
    - interpret supported time periods;
    - obtain verified statistics from the database;
    - return structured analytical results.

    The engine does not generate natural-language answers.
    """

    DEFAULT_TREND_MONTHS = 6

    _TREND_KEYWORDS = (
        "trend",
        "trends",
        "growth",
        "grew",
        "grown",
        "growing",
        "increase",
        "increased",
        "increasing",
        "decrease",
        "decreased",
        "decreasing",
        "change",
        "changed",
        "changing",
        "evolution",
        "evolution",
        "evolve",
        "evolves",
        "evolved",
        "evolue",
        "evoluent",
        "évolution",
        "évolue",
        "évoluent",
        "évolué",
        "monthly",
        "month",
        "months",
        "per month",
        "par mois",
        "mensuel",
        "mensuelle",
        "mensuels",
        "mensuelles",
        "croissance",
        "croître",
        "croissance",
        "tendance",
        "tendances",
        "augmentation",
        "diminution",
        "variation",
        "au fil du temps",
        "over time",
    )

    _MEMBER_KEYWORDS = (
        "member",
        "members",
        "membre",
        "membres",
        "membership",
        "memberships",
        "adhesion",
        "adhésions",
        "adhésion",
        "adhésions",
    )

    _USER_KEYWORDS = (
        "user",
        "users",
        "utilisateur",
        "utilisateurs",
    )

    _EVENT_KEYWORDS = (
        "event",
        "events",
        "evenement",
        "evenements",
        "événement",
        "événements",
    )

    _ACTIVITY_KEYWORDS = (
        "activity",
        "activities",
        "activite",
        "activites",
        "activité",
        "activités",
    )

    _NEWS_KEYWORDS = (
        "news",
        "article",
        "articles",
        "actualite",
        "actualites",
        "actualité",
        "actualités",
    )

    _COUNT_KEYWORDS = (
        "how many",
        "how much",
        "count",
        "number of",
        "total",
        "statistics",
        "statistic",
        "stats",
        "combien",
        "nombre",
        "statistique",
        "statistiques",
    )

    _MONTHS = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12,
    }

    _MONTH_LABELS = {
        1: "janvier",
        2: "février",
        3: "mars",
        4: "avril",
        5: "mai",
        6: "juin",
        7: "juillet",
        8: "août",
        9: "septembre",
        10: "octobre",
        11: "novembre",
        12: "décembre",
    }

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def analyze(
        self,
        query: str,
    ) -> (
        AnalyticsResult
        | AnalyticsTrendResult
        | AnalyticsComparisonResult
        | None
    ):
        """
        Analyze a supported analytical query.
        """

        normalized = self._normalize(query)

        comparison = self._analyze_comparison(
            normalized,
        )

        if comparison is not None:
            return comparison

        period = self._extract_period(
            normalized,
        )

        if self._is_trend_query(normalized):
            return self._analyze_trend(
                normalized,
                period=period,
            )

        if not self._is_count_query(normalized):
            return None

        return self._analyze_count(
            normalized,
            period=period,
        )

    def _analyze_count(
        self,
        query: str,
        period: tuple[date, date] | None = None,
    ) -> AnalyticsResult | None:
        overview = get_statistics_overview(
            self.db,
        )

        if self._contains_any(
            query,
            self._MEMBER_KEYWORDS,
        ):
            if period is not None:
                value = self._count_created_records(
                    "members",
                    period[0],
                    period[1],
                )

                return AnalyticsResult(
                    metric="members_created_in_period",
                    value=value,
                    label=(
                        "Nombre de membres créés pendant "
                        "la période demandée."
                    ),
                    start_date=period[0],
                    end_date=period[1],
                )

            if self._contains_any(
                query,
                (
                    "active",
                    "actif",
                    "actifs",
                    "active members",
                    "membres actifs",
                ),
            ):
                return AnalyticsResult(
                    metric="active_members",
                    value=overview.members.active,
                    label="Nombre de membres actuellement actifs.",
                )

            if self._contains_any(
                query,
                (
                    "pending",
                    "en attente",
                    "pending members",
                    "membres en attente",
                ),
            ):
                return AnalyticsResult(
                    metric="pending_members",
                    value=overview.members.pending,
                    label="Nombre de membres actuellement en attente.",
                )

            if self._contains_any(
                query,
                (
                    "suspended",
                    "suspendu",
                    "suspendus",
                    "suspendues",
                ),
            ):
                return AnalyticsResult(
                    metric="suspended_members",
                    value=overview.members.suspended,
                    label="Nombre de membres actuellement suspendus.",
                )

            if self._contains_any(
                query,
                (
                    "inactive",
                    "inactif",
                    "inactifs",
                    "inactives",
                ),
            ):
                return AnalyticsResult(
                    metric="inactive_members",
                    value=overview.members.inactive,
                    label="Nombre de membres actuellement inactifs.",
                )

            if self._contains_any(
                query,
                (
                    "archived",
                    "archive",
                    "archives",
                    "archivé",
                    "archivés",
                    "archived members",
                    "membres archivés",
                ),
            ):
                return AnalyticsResult(
                    metric="archived_members",
                    value=overview.members.archived,
                    label="Nombre de membres archivés.",
                )

            return AnalyticsResult(
                metric="total_members",
                value=overview.members.total,
                label="Nombre total de membres KBR.",
            )

        if self._contains_any(
            query,
            self._USER_KEYWORDS,
        ):
            if self._contains_any(
                query,
                (
                    "admin",
                    "admins",
                    "administrator",
                    "administrators",
                    "administrateur",
                    "administrateurs",
                ),
            ):
                return AnalyticsResult(
                    metric="admin_users",
                    value=overview.users.admins,
                    label="Nombre d'utilisateurs administrateurs.",
                )

            if self._contains_any(
                query,
                ("staff",),
            ):
                return AnalyticsResult(
                    metric="staff_users",
                    value=overview.users.staff,
                    label="Nombre d'utilisateurs staff.",
                )

            return AnalyticsResult(
                metric="total_users",
                value=overview.users.total,
                label="Nombre total d'utilisateurs.",
            )

        if self._contains_any(
            query,
            self._EVENT_KEYWORDS,
        ):
            if period is not None:
                value = self._count_created_records(
                    "events",
                    period[0],
                    period[1],
                )

                return AnalyticsResult(
                    metric="events_created_in_period",
                    value=value,
                    label=(
                        "Nombre d'événements créés pendant "
                        "la période demandée."
                    ),
                    start_date=period[0],
                    end_date=period[1],
                )

            if self._contains_any(
                query,
                (
                    "published",
                    "publish",
                    "publié",
                    "publiés",
                    "publiées",
                    "événements publiés",
                    "evenements publies",
                ),
            ):
                return AnalyticsResult(
                    metric="published_events",
                    value=overview.events.published,
                    label="Nombre d'événements KBR publiés.",
                )

            if self._contains_any(
                query,
                (
                    "upcoming",
                    "next",
                    "future",
                    "à venir",
                    "a venir",
                    "prochain",
                    "prochains",
                    "prochaine",
                    "prochaines",
                ),
            ):
                return AnalyticsResult(
                    metric="upcoming_events",
                    value=overview.events.upcoming,
                    label=(
                        "Nombre d'événements KBR publiés "
                        "à venir."
                    ),
                )

            if self._contains_any(
                query,
                (
                    "cancelled",
                    "canceled",
                    "cancel",
                    "annulé",
                    "annulés",
                    "annulées",
                ),
            ):
                return AnalyticsResult(
                    metric="cancelled_events",
                    value=overview.events.cancelled,
                    label="Nombre d'événements KBR annulés.",
                )

            if self._contains_any(
                query,
                (
                    "draft",
                    "drafts",
                    "brouillon",
                    "brouillons",
                ),
            ):
                return AnalyticsResult(
                    metric="draft_events",
                    value=overview.events.draft,
                    label="Nombre d'événements KBR en brouillon.",
                )

            return AnalyticsResult(
                metric="total_events",
                value=overview.events.total,
                label="Nombre total d'événements KBR.",
            )

        if self._contains_any(
            query,
            self._ACTIVITY_KEYWORDS,
        ):
            if period is not None:
                value = self._count_created_records(
                    "activities",
                    period[0],
                    period[1],
                )

                return AnalyticsResult(
                    metric="activities_created_in_period",
                    value=value,
                    label=(
                        "Nombre d'activités créées pendant "
                        "la période demandée."
                    ),
                    start_date=period[0],
                    end_date=period[1],
                )

            if self._contains_any(
                query,
                (
                    "published",
                    "publish",
                    "publiée",
                    "publiées",
                    "publiees",
                ),
            ):
                return AnalyticsResult(
                    metric="published_activities",
                    value=overview.activities.published,
                    label="Nombre d'activités KBR publiées.",
                )

            if self._contains_any(
                query,
                (
                    "upcoming",
                    "next",
                    "future",
                    "à venir",
                    "a venir",
                ),
            ):
                return AnalyticsResult(
                    metric="upcoming_activities",
                    value=overview.activities.upcoming,
                    label=(
                        "Nombre d'activités KBR publiées "
                        "à venir."
                    ),
                )

            if self._contains_any(
                query,
                (
                    "draft",
                    "drafts",
                    "brouillon",
                    "brouillons",
                ),
            ):
                return AnalyticsResult(
                    metric="draft_activities",
                    value=overview.activities.draft,
                    label="Nombre d'activités KBR en brouillon.",
                )

            return AnalyticsResult(
                metric="total_activities",
                value=overview.activities.total,
                label="Nombre total d'activités KBR.",
            )

        if self._contains_any(
            query,
            self._NEWS_KEYWORDS,
        ):
            if period is not None:
                value = self._count_created_records(
                    "news",
                    period[0],
                    period[1],
                )

                return AnalyticsResult(
                    metric="news_created_in_period",
                    value=value,
                    label=(
                        "Nombre d'articles d'actualité créés "
                        "pendant la période demandée."
                    ),
                    start_date=period[0],
                    end_date=period[1],
                )

            if self._contains_any(
                query,
                (
                    "published",
                    "publish",
                    "publiées",
                    "publiés",
                    "actualités publiées",
                    "actualites publiees",
                ),
            ):
                return AnalyticsResult(
                    metric="published_news",
                    value=overview.news.published,
                    label="Nombre d'actualités KBR publiées.",
                )

            if self._contains_any(
                query,
                (
                    "draft",
                    "drafts",
                    "brouillon",
                    "brouillons",
                ),
            ):
                return AnalyticsResult(
                    metric="draft_news",
                    value=overview.news.draft,
                    label="Nombre d'actualités KBR en brouillon.",
                )

            return AnalyticsResult(
                metric="total_news",
                value=overview.news.total,
                label="Nombre total d'articles d'actualité KBR.",
            )

        return None

    def _analyze_trend(
        self,
        query: str,
        period: tuple[date, date] | None = None,
    ) -> AnalyticsTrendResult | None:
        months = self.DEFAULT_TREND_MONTHS

        if period is not None:
            months = self._number_of_months(
                period[0],
                period[1],
            )

        trends = get_statistics_trends(
            self.db,
            months=months,
        )

        if self._contains_any(
            query,
            self._MEMBER_KEYWORDS,
        ):
            return AnalyticsTrendResult(
                metric="members_created_per_month",
                months=[
                    (
                        point.month,
                        point.members,
                    )
                    for point in trends.months
                ],
                label=(
                    "Évolution mensuelle du nombre de "
                    f"membres créés sur les {months} "
                    "derniers mois."
                ),
                start_date=period[0] if period else None,
                end_date=period[1] if period else None,
            )

        if self._contains_any(
            query,
            self._EVENT_KEYWORDS,
        ):
            return AnalyticsTrendResult(
                metric="events_created_per_month",
                months=[
                    (
                        point.month,
                        point.events,
                    )
                    for point in trends.months
                ],
                label=(
                    "Évolution mensuelle du nombre "
                    f"d'événements créés sur les {months} "
                    "derniers mois."
                ),
                start_date=period[0] if period else None,
                end_date=period[1] if period else None,
            )

        if self._contains_any(
            query,
            self._ACTIVITY_KEYWORDS,
        ):
            return AnalyticsTrendResult(
                metric="activities_created_per_month",
                months=[
                    (
                        point.month,
                        point.activities,
                    )
                    for point in trends.months
                ],
                label=(
                    "Évolution mensuelle du nombre "
                    f"d'activités créées sur les {months} "
                    "derniers mois."
                ),
                start_date=period[0] if period else None,
                end_date=period[1] if period else None,
            )

        if self._contains_any(
            query,
            self._NEWS_KEYWORDS,
        ):
            return AnalyticsTrendResult(
                metric="news_created_per_month",
                months=[
                    (
                        point.month,
                        point.news,
                    )
                    for point in trends.months
                ],
                label=(
                    "Évolution mensuelle du nombre "
                    f"d'articles d'actualité créés sur les "
                    f"{months} derniers mois."
                ),
                start_date=period[0] if period else None,
                end_date=period[1] if period else None,
            )

        return None

    def _analyze_comparison(
        self,
        query: str,
    ) -> AnalyticsComparisonResult | None:
        """
        Handle simple period comparisons such as:

        - compare June and September events
        - compare member growth between June and September
        """

        if "compare" not in query and "compar" not in query:
            return None

        month_numbers = [
            month
            for name, month in self._MONTHS.items()
            if re.search(
                rf"\b{re.escape(name)}\b",
                query,
            )
        ]

        month_numbers = list(
            dict.fromkeys(month_numbers),
        )

        if len(month_numbers) < 2:
            return None

        first_month = month_numbers[0]
        second_month = month_numbers[1]

        year = datetime.now(
            timezone.utc,
        ).year

        first_start = date(
            year,
            first_month,
            1,
        )

        first_end = date(
            year,
            first_month,
            calendar.monthrange(
                year,
                first_month,
            )[1],
        )

        second_start = date(
            year,
            second_month,
            1,
        )

        second_end = date(
            year,
            second_month,
            calendar.monthrange(
                year,
                second_month,
            )[1],
        )

        domain = self._detect_domain(
            query,
        )

        if domain is None:
            return None

        first_value = self._count_created_records(
            domain,
            first_start,
            first_end,
        )

        second_value = self._count_created_records(
            domain,
            second_start,
            second_end,
        )

        difference = second_value - first_value

        percentage_change = None

        if first_value != 0:
            percentage_change = (
                difference / first_value
            ) * 100

        return AnalyticsComparisonResult(
            metric=f"{domain}_created_comparison",
            first_period_label=self._format_month_label(
                first_month,
                year,
            ),
            first_value=first_value,
            second_period_label=self._format_month_label(
                second_month,
                year,
            ),
            second_value=second_value,
            difference=difference,
            percentage_change=percentage_change,
            label=(
                f"Comparaison des {self._domain_label(domain)} "
                "créés entre les deux mois demandés."
            ),
        )

    def _extract_period(
        self,
        query: str,
    ) -> tuple[date, date] | None:
        """
        Extract supported periods from natural-language queries.

        Supported examples:

        - in August
        - in August 2026
        - last 3 months
        - past 6 months
        - last month
        - this month
        - this year
        - between June and September
        """

        now = datetime.now(
            timezone.utc,
        ).date()

        month_match = re.search(
            r"\b("
            + "|".join(
                re.escape(month)
                for month in self._MONTHS
            )
            + r")"
            r"(?:\s+(\d{4}))?\b",
            query,
        )

        if month_match:
            month_name = month_match.group(1)
            year_text = month_match.group(2)

            month = self._MONTHS[
                month_name
            ]

            year = (
                int(year_text)
                if year_text
                else now.year
            )

            start = date(
                year,
                month,
                1,
            )

            end = date(
                year,
                month,
                calendar.monthrange(
                    year,
                    month,
                )[1],
            )

            return start, end

        relative_match = re.search(
            r"\b(?:last|past|previous|derniers?|"
            r"dernières?|dernieres?)\s+"
            r"(\d+)\s+"
            r"(?:months?|mois)\b",
            query,
        )

        if relative_match:
            count = int(
                relative_match.group(1),
            )

            count = max(
                1,
                min(count, 24),
            )

            first_month = (
                now.replace(
                    day=1,
                )
                - timedelta(
                    days=1,
                )
            )

            for _ in range(
                count - 1,
            ):
                first_month = (
                    first_month.replace(
                        day=1,
                    )
                    - timedelta(
                        days=1,
                    )
                )

            start = first_month.replace(
                day=1,
            )

            return start, now

        if re.search(
            r"\b(?:last|past|previous|dernier|"
            r"dernière|derniere)\s+month\b",
            query,
        ):
            first_day_this_month = now.replace(
                day=1,
            )

            end = (
                first_day_this_month
                - timedelta(
                    days=1,
                )
            )

            start = end.replace(
                day=1,
            )

            return start, end

        if re.search(
            r"\b(?:this|current)\s+month\b",
            query,
        ):
            start = now.replace(
                day=1,
            )

            end = now

            return start, end

        if re.search(
            r"\b(?:this|current)\s+year\b",
            query,
        ):
            return (
                date(
                    now.year,
                    1,
                    1,
                ),
                now,
            )

        between_match = re.search(
            r"\bbetween\s+"
            r"([a-zéûôàèù]+)"
            r"(?:\s+and\s+|\s+et\s+)"
            r"([a-zéûôàèù]+)"
            r"(?:\s+(\d{4}))?\b",
            query,
        )

        if between_match:
            first_name = between_match.group(1)
            second_name = between_match.group(2)

            if (
                first_name in self._MONTHS
                and second_name in self._MONTHS
            ):
                year_text = between_match.group(3)

                year = (
                    int(year_text)
                    if year_text
                    else now.year
                )

                first_month = self._MONTHS[
                    first_name
                ]

                second_month = self._MONTHS[
                    second_name
                ]

                start = date(
                    year,
                    first_month,
                    1,
                )

                end = date(
                    year,
                    second_month,
                    calendar.monthrange(
                        year,
                        second_month,
                    )[1],
                )

                return start, end

        return None

    def _count_created_records(
        self,
        domain: str,
        start_date: date,
        end_date: date,
    ) -> int:
        from backend.app.models.activity import Activity
        from backend.app.models.event import Event
        from backend.app.models.news import News
        from backend.app.models.user import User

        models = {
            "members": User,
            "events": Event,
            "activities": Activity,
            "news": News,
        }

        model = models.get(domain)

        if model is None:
            return 0

        start_datetime = datetime.combine(
            start_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        query = (
            self.db.query(model)
            .filter(
                model.created_at >= start_datetime,
                model.created_at < end_datetime,
            )
        )

        if domain == "members":
            try:
                from backend.app.models.user import UserRole

                query = query.filter(
                    model.role == UserRole.MEMBER,
                )
            except ImportError:
                pass

        return query.count()

    def _detect_domain(
        self,
        query: str,
    ) -> str | None:
        if self._contains_any(
            query,
            self._MEMBER_KEYWORDS,
        ):
            return "members"

        if self._contains_any(
            query,
            self._EVENT_KEYWORDS,
        ):
            return "events"

        if self._contains_any(
            query,
            self._ACTIVITY_KEYWORDS,
        ):
            return "activities"

        if self._contains_any(
            query,
            self._NEWS_KEYWORDS,
        ):
            return "news"

        return None

    def _number_of_months(
        self,
        start: date,
        end: date,
    ) -> int:
        return (
            (end.year - start.year) * 12
            + end.month
            - start.month
            + 1
        )

    def _is_count_query(
        self,
        query: str,
    ) -> bool:
        return self._contains_any(
            query,
            self._COUNT_KEYWORDS,
        )

    def _is_trend_query(
        self,
        query: str,
    ) -> bool:
        """
        Determine whether the user is asking for a trend.

        This explicitly handles French constructions such as:

        - Comment évolue le nombre de membres ?
        - Comment évoluent les événements ?
        - Quelle est l'évolution des membres ?
        - Comment les membres évoluent-ils ?
        """

        if self._contains_any(
            query,
            self._TREND_KEYWORDS,
        ):
            return True

        has_member_domain = self._contains_any(
            query,
            self._MEMBER_KEYWORDS,
        )

        has_change_language = self._contains_any(
            query,
            (
                "how has",
                "how is",
                "how are",
                "over time",
                "au fil du temps",
                "comment évolue",
                "comment evolue",
                "comment évoluent",
                "comment evoluent",
                "comment a évolué",
                "comment a evolue",
                "a évolué",
                "a evolue",
                "évolution",
                "evolution",
            ),
        )

        return (
            has_member_domain
            and has_change_language
        )

    @classmethod
    def _format_month_label(
        cls,
        month: int,
        year: int,
    ) -> str:
        return (
            f"{cls._MONTH_LABELS[month]} {year}"
        )

    @staticmethod
    def _domain_label(
        domain: str,
    ) -> str:
        labels = {
            "members": "membres",
            "events": "événements",
            "activities": "activités",
            "news": "articles d'actualité",
        }

        return labels.get(
            domain,
            domain,
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            value.strip().lower().split()
        )

    @staticmethod
    def _contains_any(
        value: str,
        keywords: tuple[str, ...],
    ) -> bool:
        return any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                value,
            )
            for keyword in keywords
        )


__all__ = [
    "AnalyticsEngine",
]