from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AnalyticsResult:
    """
    Deterministic analytical result produced from the KBR database.

    The AI model must treat these values as verified application
    data and must not replace them with estimates or guesses.
    """

    metric: str
    value: int
    label: str
    source: str = "KBR PostgreSQL database"
    start_date: date | None = None
    end_date: date | None = None

    def to_prompt(self) -> str:
        lines = [
            "ANALYTICS RESULT",
            f"Metric: {self.metric}",
            f"Value: {self.value}",
            f"Description: {self.label}",
            f"Source: {self.source}",
        ]

        if self.start_date is not None:
            lines.append(
                f"Start date: {self.start_date.isoformat()}"
            )

        if self.end_date is not None:
            lines.append(
                f"End date: {self.end_date.isoformat()}"
            )

        lines.extend(
            [
                "",
                "This value is calculated from the KBR database. "
                "Treat it as authoritative for this request. "
                "Do not invent or recalculate a different value.",
            ]
        )

        return "\n".join(lines)


@dataclass(frozen=True)
class AnalyticsTrendResult:
    """
    Deterministic monthly trend result produced from the KBR database.
    """

    metric: str
    months: list[tuple[str, int]]
    label: str
    source: str = "KBR PostgreSQL database"
    start_date: date | None = None
    end_date: date | None = None

    def to_prompt(self) -> str:
        lines = [
            "ANALYTICS TREND RESULT",
            f"Metric: {self.metric}",
            f"Description: {self.label}",
            f"Source: {self.source}",
        ]

        if self.start_date is not None:
            lines.append(
                f"Start date: {self.start_date.isoformat()}"
            )

        if self.end_date is not None:
            lines.append(
                f"End date: {self.end_date.isoformat()}"
            )

        lines.extend(
            [
                "",
                "Monthly values:",
            ]
        )

        for month, value in self.months:
            lines.append(
                f"- {month}: {value}"
            )

        lines.extend(
            [
                "",
                "These values are calculated from the KBR "
                "database. Treat them as authoritative. "
                "Do not invent or recalculate different values.",
            ]
        )

        return "\n".join(lines)


@dataclass(frozen=True)
class AnalyticsComparisonResult:
    """
    Deterministic comparison between two analytical periods.
    """

    metric: str
    first_period_label: str
    first_value: int
    second_period_label: str
    second_value: int
    difference: int
    percentage_change: float | None
    label: str
    source: str = "KBR PostgreSQL database"

    def to_prompt(self) -> str:
        percentage = (
            f"{self.percentage_change:.2f}%"
            if self.percentage_change is not None
            else "N/A"
        )

        return "\n".join(
            [
                "ANALYTICS COMPARISON RESULT",
                f"Metric: {self.metric}",
                f"Description: {self.label}",
                f"Source: {self.source}",
                "",
                (
                    f"{self.first_period_label}: "
                    f"{self.first_value}"
                ),
                (
                    f"{self.second_period_label}: "
                    f"{self.second_value}"
                ),
                f"Difference: {self.difference}",
                f"Percentage change: {percentage}",
                "",
                "These values are calculated from the KBR "
                "database. Treat them as authoritative. "
                "Do not invent or recalculate different values.",
            ]
        )


__all__ = [
    "AnalyticsResult",
    "AnalyticsTrendResult",
    "AnalyticsComparisonResult",
]