from enum import Enum


class AIIntent(str, Enum):
    ANALYTICS = "analytics"
    EVENTS = "events"
    MEMBERS = "members"
    ACTIVITIES = "activities"
    NEWS = "news"
    ORGANIZATION = "organization"
    JOIN = "join"
    GENERAL = "general"


class IntentDetector:
    """
    Lightweight deterministic intent detector for KBR.

    The detector is intentionally rule-based for now.
    This avoids an additional LLM call just to determine intent.

    Analytics is checked before content-specific intents because
    questions such as "How many events does KBR have?" contain
    an entity keyword but require a database aggregation rather
    than content retrieval.
    """

    _ANALYTICS_KEYWORDS = (
        # Explicit analytics language
        "analytics",
        "analytic",
        "analyse",
        "analysis",
        "analytical",
        "data analysis",
        "analytics report",
        "statistical",

        # English quantitative questions
        "how many",
        "how much",
        "count",
        "number of",
        "total",
        "average",
        "avg",
        "mean",
        "median",
        "minimum",
        "maximum",
        "min",
        "max",

        # English analytics concepts
        "statistics",
        "statistic",
        "stats",
        "growth",
        "trend",
        "trends",
        "monthly",
        "month over month",
        "per month",
        "how has",
        "how have",
        "how did",
        "how is",
        "how are",
        "increase",
        "decrease",
        "change",
        "evolution",
        "distribution",
        "breakdown",
        "percentage",
        "percent",
        "compare",
        "comparison",
        "compared",
        "versus",
        "vs",
        "ranking",
        "rank",
        "ranked",
        "highest",
        "lowest",
        "top",
        "bottom",
        "most",
        "least",

        # English time-period analytics
        "this month",
        "last month",
        "previous month",
        "current month",
        "this year",
        "last year",
        "previous year",
        "past month",
        "past year",
        "last week",
        "previous week",
        "between",
        "from",
        "during",
        "in 2025",
        "in 2026",

        # French analytics language
        "combien",
        "nombre",
        "statistique",
        "statistiques",
        "croissance",
        "tendance",
        "tendances",
        "mensuel",
        "mensuelle",
        "mensuels",
        "mensuelles",
        "par mois",
        "augmentation",
        "diminution",
        "évolution",
        "analyse",
        "analytique",
        "statistique",
        "moyenne",
        "médiane",
        "minimum",
        "maximum",
        "répartition",
        "distribution",
        "comparaison",
        "comparer",
        "comparé",
        "classement",
        "classé",
        "plus élevé",
        "plus élevée",
        "plus bas",
        "plus basse",
        "le plus",
        "la plus",
        "pourcentage",
        "variation",
        "progression",
    )

    _EVENT_KEYWORDS = (
        "event",
        "events",
        "événement",
        "événements",
        "evenement",
        "evenements",
        "tournament",
        "tournoi",
        "competition",
        "compétition",
        "match",
        "when is",
        "quand",
        "next event",
        "prochain événement",
        "prochain evenement",
    )

    _MEMBER_KEYWORDS = (
        "member",
        "members",
        "membre",
        "membres",
        "team",
        "équipe",
        "equipe",
        "staff",
        "who are the members",
        "qui sont les membres",
    )

    _ACTIVITY_KEYWORDS = (
        "activity",
        "activities",
        "activité",
        "activités",
        "activite",
        "activites",
        "project",
        "projects",
        "projet",
        "projets",
    )

    _NEWS_KEYWORDS = (
        "news",
        "actualité",
        "actualités",
        "actualite",
        "actualites",
        "announcement",
        "announcements",
        "annonce",
        "annonces",
    )

    _JOIN_KEYWORDS = (
        "join",
        "joining",
        "membership",
        "become a member",
        "become member",
        "rejoindre",
        "adhérer",
        "adherer",
        "adhésion",
        "adhesion",
        "inscrire",
        "inscription",
        "comment rejoindre",
        "comment adhérer",
    )

    _ORGANIZATION_KEYWORDS = (
        "kbr",
        "knights of bizertin rise",
        "organization",
        "organisation",
        "mission",
        "about kbr",
        "tell me about kbr",
        "à propos",
        "a propos",
        "qui est kbr",
    )

    def detect(
        self,
        message: str,
    ) -> AIIntent:
        """
        Detect the most relevant KBR intent.

        Analytics is checked first because analytical questions
        often contain entity keywords such as "events", "members",
        or "news".
        """

        normalized = self._normalize(message)

        if self._contains_any(
            normalized,
            self._ANALYTICS_KEYWORDS,
        ):
            return AIIntent.ANALYTICS

        if self._contains_any(
            normalized,
            self._EVENT_KEYWORDS,
        ):
            return AIIntent.EVENTS

        if self._contains_any(
            normalized,
            self._MEMBER_KEYWORDS,
        ):
            return AIIntent.MEMBERS

        if self._contains_any(
            normalized,
            self._ACTIVITY_KEYWORDS,
        ):
            return AIIntent.ACTIVITIES

        if self._contains_any(
            normalized,
            self._NEWS_KEYWORDS,
        ):
            return AIIntent.NEWS

        if self._contains_any(
            normalized,
            self._JOIN_KEYWORDS,
        ):
            return AIIntent.JOIN

        if self._contains_any(
            normalized,
            self._ORGANIZATION_KEYWORDS,
        ):
            return AIIntent.ORGANIZATION

        return AIIntent.GENERAL

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
            keyword in value
            for keyword in keywords
        )


__all__ = [
    "AIIntent",
    "IntentDetector",
]