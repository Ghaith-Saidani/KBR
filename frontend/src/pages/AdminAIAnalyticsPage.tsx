import {
  useMemo,
  useState,
} from "react";
import type { FormEvent, ReactNode } from "react";

import { Link } from "react-router-dom";

import {
  useRecentBusinessActivity,
  useStatisticsOverview,
  useStatisticsTrends,
} from "../features/statistics/statistics.hooks";

import { useAnalyticsQuery } from "../features/analytics/analytics.hooks";

import type { AnalyticsResult } from "../features/analytics/analytics.types";

import type { RecentBusinessActivity } from "../features/statistics/statistics.types";

function formatNumber(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat("fr-FR").format(value);
}

function formatMonth(month: string): string {
  const [year, monthNumber] = month.split("-");

  const date = new Date(
    Number(year),
    Number(monthNumber) - 1,
    1,
  );

  return new Intl.DateTimeFormat("fr-FR", {
    month: "short",
  })
    .format(date)
    .replace(".", "");
}

function formatPercentage(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(1)} %`;
}

function calculateMonthChange(
  current: number,
  previous: number,
): number | null {
  if (previous === 0) {
    return current === 0 ? 0 : null;
  }

  return ((current - previous) / previous) * 100;
}

function getChangeLabel(
  current: number,
  previous: number,
): string {
  if (current === previous) {
    return "Stable par rapport au mois dernier";
  }

  if (previous === 0) {
    return current > 0
      ? "Nouvelle activité ce mois-ci"
      : "Aucune activité";
  }

  return current > previous
    ? "En hausse par rapport au mois dernier"
    : "En baisse par rapport au mois dernier";
}

function getChangeClassName(
  current: number,
  previous: number,
): string {
  if (current === previous) {
    return "text-slate-500";
  }

  if (current > previous) {
    return "text-emerald-400";
  }

  return "text-red-400";
}

interface KpiCardProps {
  label: string;
  value: number;
  currentMonth: number;
  previousMonth: number;
  description: string;
}

function KpiCard({
  label,
  value,
  currentMonth,
  previousMonth,
  description,
}: KpiCardProps) {
  const change = calculateMonthChange(
    currentMonth,
    previousMonth,
  );

  const changeClassName = getChangeClassName(
    currentMonth,
    previousMonth,
  );

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition hover:border-white/20 hover:bg-white/[0.055]">
      <div className="flex items-start justify-between gap-4">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
          {label}
        </p>

        <span className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Total
        </span>
      </div>

      <p className="mt-3 text-4xl font-black tracking-tight text-white">
        {formatNumber(value)}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>

      <div className="mt-5 border-t border-white/10 pt-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-white/10 bg-white/[0.025] p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
              Mois en cours
            </p>
            <p className="mt-2 text-lg font-black text-white">
              {formatNumber(currentMonth)}
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
              Mois précédent
            </p>
            <p className="mt-2 text-lg font-semibold text-slate-400">
              {formatNumber(previousMonth)}
            </p>
          </div>
        </div>
        <div className="mt-3 flex min-h-8 items-center justify-between gap-3">
          <span className={`text-xs font-medium ${changeClassName}`}>
            {getChangeLabel(currentMonth, previousMonth)}
          </span>
          {change === null ? (
            <span className="shrink-0 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[10px] font-bold text-slate-500">
              Base 0
            </span>
          ) : (
            <span className={`shrink-0 whitespace-nowrap rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs font-black ${changeClassName}`}>
              {formatPercentage(change)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

interface TrendChartProps {
  months: {
    month: string;
    members: number;
    events: number;
    activities: number;
    news: number;
  }[];
}

const TREND_SERIES = [
  {
    key: "members",
    label: "Membres",
    color: "bg-blue-500",
    hoverColor: "hover:bg-blue-400",
  },
  {
    key: "events",
    label: "Événements",
    color: "bg-[#f5c400]",
    hoverColor: "hover:bg-[#ffd21a]",
  },
  {
    key: "activities",
    label: "Activités",
    color: "bg-purple-500",
    hoverColor: "hover:bg-purple-400",
  },
  {
    key: "news",
    label: "Actualités",
    color: "bg-emerald-500",
    hoverColor: "hover:bg-emerald-400",
  },
] as const;

type TrendSeriesKey =
  (typeof TREND_SERIES)[number]["key"];

function TrendChart({
  months,
}: TrendChartProps) {
  const maximum = useMemo(() => {
    const values = months.flatMap((item) => [
      item.members,
      item.events,
      item.activities,
      item.news,
    ]);

    return Math.max(...values, 1);
  }, [months]);

  const scale = useMemo(() => {
    const step = Math.max(
      1,
      Math.ceil(maximum / 4),
    );

    const top = step * 4;

    return {
      step,
      top,
      values: [
        top,
        step * 3,
        step * 2,
        step,
        0,
      ],
    };
  }, [maximum]);

  if (months.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.02]">
        <p className="text-sm text-slate-500">
          Aucune donnée de tendance disponible.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[820px] rounded-2xl border border-white/10 bg-white/[0.02] p-6">
        <div className="mb-6 flex flex-wrap justify-center gap-x-6 gap-y-3">
          {TREND_SERIES.map((series) => (
            <LegendItem
              key={series.key}
              label={series.label}
              color={series.color}
            />
          ))}
        </div>

        <div className="relative">
          <div className="flex">
            <div className="relative mr-4 h-56 w-10 shrink-0">
              {scale.values.map((value, index) => {
                const position =
                  index === 0
                    ? "top-0"
                    : index === 1
                      ? "top-1/4 -translate-y-1/2"
                      : index === 2
                        ? "top-1/2 -translate-y-1/2"
                        : index === 3
                          ? "top-3/4 -translate-y-1/2"
                          : "bottom-0";

                return (
                  <span
                    key={value}
                    className={`absolute right-0 text-[10px] font-medium text-slate-600 ${position}`}
                  >
                    {formatNumber(value)}
                  </span>
                );
              })}
            </div>

            <div className="relative flex-1">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-56">
                <div className="absolute inset-x-0 top-0 border-t border-white/[0.06]" />
                <div className="absolute inset-x-0 top-1/4 border-t border-white/[0.04]" />
                <div className="absolute inset-x-0 top-1/2 border-t border-white/[0.04]" />
                <div className="absolute inset-x-0 top-3/4 border-t border-white/[0.04]" />
                <div className="absolute inset-x-0 bottom-0 border-t border-white/[0.06]" />
              </div>

              <div className="relative flex h-72 items-end gap-5">
                {months.map((item, index) => {
                  const values: Record<
                    TrendSeriesKey,
                    number
                  > = {
                    members: item.members,
                    events: item.events,
                    activities: item.activities,
                    news: item.news,
                  };

                  const isFirstMonth =
                    index === 0;

                  const isLastMonth =
                    index === months.length - 1;

                  const tooltipPosition =
                    isFirstMonth
                      ? "left-0 translate-x-0"
                      : isLastMonth
                        ? "right-0 translate-x-0"
                        : "left-1/2 -translate-x-1/2";

                  return (
                    <div
                      key={item.month}
                      className="group relative flex min-w-[86px] flex-1 flex-col items-center justify-end"
                    >
                      <div
                        className={`pointer-events-none absolute bottom-[calc(100%-3.5rem)] z-30 w-52 rounded-xl border border-white/10 bg-[#101010] p-4 shadow-2xl opacity-0 transition duration-150 group-hover:translate-y-0 group-hover:opacity-100 ${tooltipPosition} translate-y-2`}
                      >
                        <p className="text-xs font-bold uppercase tracking-[0.15em] text-[#f5c400]">
                          {formatMonth(item.month)}{" "}
                          {item.month.slice(0, 4)}
                        </p>

                        <div className="mt-3 space-y-2">
                          {TREND_SERIES.map(
                            (series) => (
                              <div
                                key={series.key}
                                className="flex items-center justify-between gap-4"
                              >
                                <span className="flex items-center gap-2 text-xs text-slate-400">
                                  <span
                                    className={`h-2 w-2 rounded-full ${series.color}`}
                                  />

                                  {series.label}
                                </span>

                                <span className="text-xs font-black text-white">
                                  {formatNumber(
                                    values[
                                      series.key
                                    ],
                                  )}
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      </div>

                      <div
                        className="flex h-56 w-full items-end justify-center gap-1"
                        aria-label={`Données de ${formatMonth(
                          item.month,
                        )} ${item.month.slice(0, 4)}`}
                      >
                        {TREND_SERIES.map(
                          (series) => {
                            const value =
                              values[series.key];

                            const height =
                              value === 0
                                ? 0
                                : Math.max(
                                    8,
                                    (value /
                                      scale.top) *
                                      100,
                                  );

                            return (
                              <div
                                key={
                                  series.key
                                }
                                role="img"
                                aria-label={`${series.label}: ${formatNumber(
                                  value,
                                )}`}
                                title={`${series.label}: ${formatNumber(
                                  value,
                                )}`}
                                className={`w-3 rounded-t-md ${series.color} ${series.hoverColor} transition-all duration-200`}
                                style={{
                                  height: `${height}%`,
                                }}
                              />
                            );
                          },
                        )}
                      </div>

                      <div className="mt-4 text-center">
                        <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
                          {formatMonth(item.month)}
                        </p>

                        <p className="mt-1 text-[10px] text-slate-600">
                          {item.month.slice(0, 4)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="mt-2 pl-14">
            <p className="text-[10px] uppercase tracking-[0.15em] text-slate-700">
              Éléments créés
            </p>
          </div>
        </div>

        <div className="mt-6 border-t border-white/10 pt-5">
          <p className="text-center text-xs text-slate-600">
            Survolez un mois pour afficher le détail des
            quatre indicateurs.
          </p>
        </div>
      </div>
    </div>
  );
}

interface LegendItemProps {
  label: string;
  color: string;
}

function LegendItem({
  label,
  color,
}: LegendItemProps) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`h-2.5 w-2.5 rounded-full ${color}`}
        aria-hidden="true"
      />

      <span className="text-xs font-medium text-slate-400">
        {label}
      </span>
    </div>
  );
}

interface StatusBarItemProps {
  label: string;
  value: number;
  total: number;
}

function StatusBarItem({
  label,
  value,
  total,
}: StatusBarItemProps) {
  const percentage =
    total > 0
      ? (value / total) * 100
      : 0;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-4">
        <span className="text-sm font-medium text-slate-400">
          {label}
        </span>

        <div className="flex items-center gap-3">
          <span className="text-sm font-black text-white">
            {formatNumber(value)}
          </span>

          <span className="w-12 text-right text-xs text-slate-600">
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full bg-[#f5c400] transition-all duration-500"
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

function StatusDistribution({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-6">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
        Répartition
      </p>

      <h3 className="mt-2 text-lg font-black text-white">
        {title}
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        {description}
      </p>

      <div className="mt-6 space-y-5">
        {children}
      </div>
    </div>
  );
}

/* ================================================================
   RECENT BUSINESS ACTIVITY
================================================================ */

const BUSINESS_ACTION_LABELS: Record<
  string,
  string
> = {
  ACTIVITY_CREATED: "Activité créée",
  ACTIVITY_UPDATED: "Activité modifiée",
  ACTIVITY_PUBLISHED: "Activité publiée",
  ACTIVITY_DELETED: "Activité supprimée",

  EVENT_CREATED: "Événement créé",
  EVENT_UPDATED: "Événement modifié",
  EVENT_PUBLISHED: "Événement publié",
  EVENT_CANCELLED: "Événement annulé",
  EVENT_DELETED: "Événement supprimé",

  NEWS_CREATED: "Actualité créée",
  NEWS_UPDATED: "Actualité modifiée",
  NEWS_PUBLISHED: "Actualité publiée",
  NEWS_UNPUBLISHED: "Actualité dépubliée",
  NEWS_DELETED: "Actualité supprimée",

  MEMBER_UPDATED: "Membre modifié",
  MEMBER_DEACTIVATED: "Membre désactivé",
  MEMBER_REACTIVATED: "Membre réactivé",
  MEMBER_ARCHIVED: "Membre archivé",
  MEMBER_DELETED: "Membre supprimé",

  USER_ACTIVATED: "Utilisateur activé",
};

const BUSINESS_RESOURCE_LABELS: Record<
  string,
  string
> = {
  activity: "Activité",
  event: "Événement",
  news: "Actualité",
  member: "Membre",
  user: "Utilisateur",
};

function getBusinessActionLabel(
  action: string,
): string {
  return (
    BUSINESS_ACTION_LABELS[action] ??
    action.replaceAll("_", " ")
  );
}

function getBusinessResourceLabel(
  resourceType: string | null,
): string {
  if (!resourceType) {
    return "Ressource";
  }

  return (
    BUSINESS_RESOURCE_LABELS[
      resourceType.toLowerCase()
    ] ?? resourceType
  );
}

function getBusinessActionSymbol(
  action: string,
): string {
  if (action.includes("DELETED")) {
    return "×";
  }

  if (
    action.includes("PUBLISHED") ||
    action.includes("REACTIVATED") ||
    action.includes("ACTIVATED")
  ) {
    return "✓";
  }

  if (
    action.includes("CANCELLED") ||
    action.includes("DEACTIVATED") ||
    action.includes("ARCHIVED")
  ) {
    return "!";
  }

  if (action.includes("UPDATED")) {
    return "↻";
  }

  return "+";
}

function getBusinessActionTone(
  action: string,
): string {
  if (action.includes("DELETED")) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  if (
    action.includes("PUBLISHED") ||
    action.includes("REACTIVATED") ||
    action.includes("ACTIVATED")
  ) {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }

  if (
    action.includes("CANCELLED") ||
    action.includes("DEACTIVATED") ||
    action.includes("ARCHIVED")
  ) {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  return "border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]";
}

function formatActivityDetails(
  details: string | null,
): string | null {
  if (!details) return null;
  return details.replace(/^SEED:\S+\s*/i, "").trim();
}

function formatActivityTimestamp(
  timestamp: string,
): string {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function BusinessActivityItem({
  activity,
}: {
  activity: RecentBusinessActivity;
}) {
  const actionLabel =
    getBusinessActionLabel(activity.action);

  const resourceLabel =
    getBusinessResourceLabel(
      activity.resource_type,
    );

  const symbol = getBusinessActionSymbol(
    activity.action,
  );

  const tone = getBusinessActionTone(
    activity.action,
  );

  const displayDetails = formatActivityDetails(activity.details);

  return (
    <div className="flex gap-4 rounded-xl border border-white/10 bg-white/[0.02] p-4 transition hover:border-white/15 hover:bg-white/[0.035]">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border text-sm font-black ${tone}`}
        aria-hidden="true"
      >
        {symbol}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <p className="text-sm font-black text-white">
            {actionLabel}
          </p>

          <time
            dateTime={activity.occurred_at}
            className="shrink-0 text-xs text-slate-600"
          >
            {formatActivityTimestamp(
              activity.occurred_at,
            )}
          </time>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {resourceLabel}
          </span>
        </div>

        {displayDetails ? (
          <p className="mt-2 break-words text-sm leading-5 text-slate-400">
            {displayDetails}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function RecentBusinessActivity({
  activities,
  isLoading,
  isError,
}: {
  activities: RecentBusinessActivity[];
  isLoading: boolean;
  isError: boolean;
}) {
  return (
    <section className="mt-10">
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
            Activité opérationnelle
          </p>

          <h2 className="mt-1 text-lg font-black text-white">
            Activité récente
          </h2>

          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
            Dernières actions métier enregistrées sur la
            plateforme KBR.
          </p>
        </div>

        <Link
          to="/admin/activity-logs"
          className="inline-flex w-fit items-center rounded-xl border border-white/10 px-4 py-2.5 text-xs font-bold text-slate-400 transition hover:border-white/20 hover:bg-white/5 hover:text-white"
        >
          Voir tous les journaux →
        </Link>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5 sm:p-6">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map(
              (_, index) => (
                <div
                  key={`activity-skeleton-${index}`}
                  className="h-24 animate-pulse rounded-xl border border-white/10 bg-white/[0.03]"
                />
              ),
            )}
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/[0.05] p-5">
            <p className="text-sm font-bold text-red-300">
              Impossible de charger l'activité récente.
            </p>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Les autres indicateurs du tableau de bord
              restent disponibles.
            </p>
          </div>
        ) : activities.length === 0 ? (
          <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] p-8 text-center">
            <p className="text-sm font-bold text-white">
              Aucune activité métier récente.
            </p>

            <p className="mt-2 text-sm text-slate-600">
              Les nouvelles actions importantes apparaîtront
              ici automatiquement.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <BusinessActivityItem
                key={activity.id}
                activity={activity}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

interface ResultShellProps {
  eyebrow: string;
  title: string;
  children: ReactNode;
}

function ResultShell({
  eyebrow,
  title,
  children,
}: ResultShellProps) {
  return (
    <div className="rounded-2xl border border-[#f5c400]/20 bg-[#f5c400]/[0.04] p-6">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
        {eyebrow}
      </p>

      <h3 className="mt-2 text-lg font-black text-white">
        {title}
      </h3>

      <div className="mt-6">
        {children}
      </div>
    </div>
  );
}

function MetricResult({
  result,
}: {
  result: AnalyticsResult;
}) {
  return (
    <ResultShell
      eyebrow="Résultat vérifié"
      title={result.label}
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-5xl font-black tracking-tight text-white">
            {formatNumber(result.value)}
          </p>

          <p className="mt-2 text-sm text-slate-400">
            Valeur calculée par le moteur analytique KBR.
          </p>
        </div>

        <div className="text-left sm:text-right">
          <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-600">
            Métrique
          </p>

          <p className="mt-1 text-sm font-semibold text-slate-300">
            {result.metric}
          </p>
        </div>
      </div>

      <SourceInformation result={result} />
    </ResultShell>
  );
}

function TrendResult({
  result,
}: {
  result: AnalyticsResult;
}) {
  const months = result.months ?? [];

  const maximum = Math.max(
    ...months.map(([, value]) => value),
    1,
  );

  return (
    <ResultShell
      eyebrow="Tendance vérifiée"
      title={result.label}
    >
      <div className="space-y-4">
        {months.map(([month, value]) => {
          const width =
            value === 0
              ? 0
              : Math.max(
                  4,
                  (value / maximum) * 100,
                );

          return (
            <div key={month}>
              <div className="mb-2 flex items-center justify-between gap-4">
                <span className="text-sm font-medium text-slate-400">
                  {formatMonth(month)} {month.slice(0, 4)}
                </span>

                <span className="text-sm font-black text-white">
                  {formatNumber(value)}
                </span>
              </div>

              <div className="h-2 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-[#f5c400] transition-all"
                  style={{
                    width: `${width}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <SourceInformation result={result} />
    </ResultShell>
  );
}

function ComparisonResult({
  result,
}: {
  result: AnalyticsResult;
}) {
  return (
    <ResultShell
      eyebrow="Comparaison vérifiée"
      title={result.label}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <ComparisonPeriod
          label={result.first_period_label}
          value={result.first_value}
        />

        <ComparisonPeriod
          label={result.second_period_label}
          value={result.second_value}
        />
      </div>

      <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-600">
              Différence
            </p>

            <p className="mt-1 text-2xl font-black text-white">
              {result.difference !== null &&
              result.difference > 0
                ? "+"
                : ""}
              {formatNumber(result.difference)}
            </p>
          </div>

          <div className="sm:text-right">
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-600">
              Variation
            </p>

            <p className="mt-1 text-2xl font-black text-[#f5c400]">
              {formatPercentage(
                result.percentage_change,
              )}
            </p>
          </div>
        </div>
      </div>

      <SourceInformation result={result} />
    </ResultShell>
  );
}

function ComparisonPeriod({
  label,
  value,
}: {
  label: string | null;
  value: number | null;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-5">
      <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-600">
        Période
      </p>

      <p className="mt-2 text-sm font-semibold text-slate-300">
        {label ?? "—"}
      </p>

      <p className="mt-3 text-3xl font-black text-white">
        {formatNumber(value)}
      </p>
    </div>
  );
}

function SourceInformation({
  result,
}: {
  result: AnalyticsResult;
}) {
  return (
    <div className="mt-6 border-t border-white/10 pt-4">
      <div className="flex flex-col gap-2 text-xs text-slate-600 sm:flex-row sm:items-center sm:justify-between">
        <span>
          Source : {result.source}
        </span>

        {result.start_date || result.end_date ? (
          <span>
            {result.start_date ?? "—"} →{" "}
            {result.end_date ?? "—"}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function UnsupportedResult() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-sm font-black text-slate-400">
          ?
        </div>

        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
            Analyse indisponible
          </p>

          <h3 className="mt-2 text-lg font-black text-white">
            Cette statistique n'est pas encore supportée.
          </h3>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Le moteur analytique ne dispose pas encore
            d'une métrique déterministe correspondant à
            cette question. Aucune valeur n'a été inventée.
          </p>
        </div>
      </div>
    </div>
  );
}

function EmptyAnalysisState() {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-8 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-lg font-black text-slate-500">
        AI
      </div>

      <h3 className="mt-4 text-lg font-black text-white">
        Posez une question sur KBR
      </h3>

      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
        Le moteur analytique interrogera les données
        vérifiées de KBR et présentera le résultat sans
        inventer de statistiques.
      </p>
    </div>
  );
}

interface QuickQuestionProps {
  question: string;
  onSelect: (question: string) => void;
  disabled: boolean;
}

function QuickQuestion({
  question,
  onSelect,
  disabled,
}: QuickQuestionProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(question)}
      disabled={disabled}
      className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-sm font-medium text-slate-400 transition hover:border-[#f5c400]/30 hover:bg-[#f5c400]/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
    >
      {question}
    </button>
  );
}

function ArchitectureStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <p className="text-xs font-black tracking-[0.2em] text-[#f5c400]">
        {number}
      </p>

      <h3 className="mt-3 text-base font-black text-white">
        {title}
      </h3>

      <p className="mt-2 text-sm leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
}

export default function AdminAIAnalyticsPage() {
  const {
    data: overview,
    isLoading: overviewLoading,
    isError: overviewError,
  } = useStatisticsOverview();

  const {
    data: trends,
    isLoading: trendsLoading,
    isError: trendsError,
  } = useStatisticsTrends(6);

  const {
    data: recentActivity,
    isLoading: recentActivityLoading,
    isError: recentActivityError,
  } = useRecentBusinessActivity(10);

  const analyticsMutation = useAnalyticsQuery();

  const [query, setQuery] = useState("");

  const [submittedQuery, setSubmittedQuery] =
    useState<string | null>(null);

  const handleSubmit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const normalizedQuery = query.trim();

    if (!normalizedQuery) {
      return;
    }

    setSubmittedQuery(normalizedQuery);

    analyticsMutation.mutate(normalizedQuery);
  };

  const handleQuickQuestion = (
    question: string,
  ) => {
    setQuery(question);
    setSubmittedQuery(question);
    analyticsMutation.mutate(question);
  };

  const result =
    analyticsMutation.data?.result ?? null;

  const hasSubmittedQuery =
    submittedQuery !== null;

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        {/* ============================================================
            HEADER
        ============================================================ */}

        <div className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Data Science / AI
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              AI Analytics
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Analysez les données KBR à travers des
              indicateurs vérifiés, des tendances et des
              requêtes en langage naturel.
            </p>
          </div>

          <Link
            to="/admin"
            className="inline-flex w-fit items-center rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
          >
            ← Tableau de bord
          </Link>
        </div>

        {/* ============================================================
            EXECUTIVE OVERVIEW
        ============================================================ */}

        <section>
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Vue exécutive
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Indicateurs clés
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Vue synthétique de l'activité actuelle de la
              plateforme KBR. Les variations comparent le
              mois en cours au mois précédent.
            </p>
          </div>

          {overviewLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map(
                (_, index) => (
                  <div
                    key={`overview-skeleton-${index}`}
                    className="h-56 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
                  />
                ),
              )}
            </div>
          ) : overviewError || !overview ? (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-6">
              <p className="text-sm font-bold text-red-300">
                Impossible de charger les indicateurs
                analytiques.
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Vérifiez votre session administrateur et
                la disponibilité du serveur.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KpiCard
                label="Membres"
                value={overview.members.total}
                currentMonth={
                  overview.members.created_this_month
                }
                previousMonth={
                  overview.members.created_last_month
                }
                description="Membres enregistrés"
              />

              <KpiCard
                label="Événements"
                value={overview.events.total}
                currentMonth={
                  overview.events.created_this_month
                }
                previousMonth={
                  overview.events.created_last_month
                }
                description="Événements enregistrés"
              />

              <KpiCard
                label="Activités"
                value={overview.activities.total}
                currentMonth={
                  overview.activities.created_this_month
                }
                previousMonth={
                  overview.activities.created_last_month
                }
                description="Activités enregistrées"
              />

              <KpiCard
                label="Actualités"
                value={overview.news.total}
                currentMonth={
                  overview.news.created_this_month
                }
                previousMonth={
                  overview.news.created_last_month
                }
                description="Articles enregistrés"
              />
            </div>
          )}
        </section>

        {/* ============================================================
            STATUS DISTRIBUTION
        ============================================================ */}

        {!overviewLoading &&
        !overviewError &&
        overview ? (
          <section className="mt-10">
            <div className="mb-5">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
                État actuel
              </p>

              <h2 className="mt-1 text-lg font-black text-white">
                Répartition des ressources
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Distribution actuelle des membres et des
                événements selon leur statut.
              </p>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <StatusDistribution
                title="Membres"
                description="État des membres enregistrés dans KBR."
              >
                <StatusBarItem
                  label="Actifs"
                  value={overview.members.active}
                  total={overview.members.total}
                />

                <StatusBarItem
                  label="En attente"
                  value={overview.members.pending}
                  total={overview.members.total}
                />

                <StatusBarItem
                  label="Suspendus"
                  value={overview.members.suspended}
                  total={overview.members.total}
                />

                <StatusBarItem
                  label="Inactifs"
                  value={overview.members.inactive}
                  total={overview.members.total}
                />

                <StatusBarItem
                  label="Archivés"
                  value={overview.members.archived}
                  total={overview.members.total}
                />
              </StatusDistribution>

              <StatusDistribution
                title="Événements"
                description="État des événements actuellement enregistrés."
              >
                <StatusBarItem
                  label="Publiés"
                  value={overview.events.published}
                  total={overview.events.total}
                />

                <StatusBarItem
                  label="Brouillons"
                  value={overview.events.draft}
                  total={overview.events.total}
                />

                <StatusBarItem
                  label="Annulés"
                  value={overview.events.cancelled}
                  total={overview.events.total}
                />

                <StatusBarItem
                  label="À venir"
                  value={overview.events.upcoming}
                  total={overview.events.total}
                />

                <StatusBarItem
                  label="Passés"
                  value={overview.events.past}
                  total={overview.events.total}
                />
              </StatusDistribution>
            </div>
          </section>
        ) : null}

        {/* ============================================================
            RECENT BUSINESS ACTIVITY
        ============================================================ */}

        <RecentBusinessActivity
          activities={
            recentActivity?.activities ?? []
          }
          isLoading={recentActivityLoading}
          isError={recentActivityError}
        />

        {/* ============================================================
            TRENDS
        ============================================================ */}

        <section className="mt-10">
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Data Science
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Évolution mensuelle
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Création de nouveaux éléments dans KBR au fil
              du temps. Le dernier mois correspond au mois
              en cours et peut donc être partiel.
            </p>
          </div>

          {trendsLoading ? (
            <div className="h-80 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]" />
          ) : trendsError || !trends ? (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-6">
              <p className="text-sm font-bold text-red-300">
                Impossible de charger les tendances.
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Les indicateurs clés restent disponibles,
                mais les données historiques ne peuvent pas
                être affichées actuellement.
              </p>
            </div>
          ) : (
            <TrendChart months={trends.months} />
          )}
        </section>

        {/* ============================================================
            AI ANALYST
        ============================================================ */}

        <section className="mt-10">
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              AI Analyst
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Interroger les données KBR
            </h2>

            <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
              Posez une question en langage naturel. Les
              statistiques sont calculées par le moteur
              analytique avant d'être présentées.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-6 sm:p-8">
            <form
              onSubmit={handleSubmit}
              className="flex flex-col gap-3 lg:flex-row"
            >
              <input
                type="text"
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Ex. Combien d'événements avons-nous ?"
                disabled={analyticsMutation.isPending}
                className="min-h-12 flex-1 rounded-xl border border-white/10 bg-black/30 px-4 text-sm text-white outline-none transition placeholder:text-slate-700 focus:border-[#f5c400]/40 focus:ring-1 focus:ring-[#f5c400]/20 disabled:cursor-not-allowed disabled:opacity-60"
              />

              <button
                type="submit"
                disabled={
                  analyticsMutation.isPending ||
                  !query.trim()
                }
                className="min-h-12 rounded-xl bg-[#f5c400] px-6 text-sm font-black text-[#050505] transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {analyticsMutation.isPending
                  ? "Analyse..."
                  : "Analyser"}
              </button>
            </form>

            <div className="mt-6">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-600">
                Questions rapides
              </p>

              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <QuickQuestion
                  question="Combien d'événements KBR compte-t-il ?"
                  onSelect={handleQuickQuestion}
                  disabled={
                    analyticsMutation.isPending
                  }
                />

                <QuickQuestion
                  question="Combien d'événements ont été créés en août 2026 ?"
                  onSelect={handleQuickQuestion}
                  disabled={
                    analyticsMutation.isPending
                  }
                />

                <QuickQuestion
                  question="Comment évolue le nombre de membres ?"
                  onSelect={handleQuickQuestion}
                  disabled={
                    analyticsMutation.isPending
                  }
                />

                <QuickQuestion
                  question="Comparer les événements entre juin et septembre."
                  onSelect={handleQuickQuestion}
                  disabled={
                    analyticsMutation.isPending
                  }
                />
              </div>
            </div>

            {analyticsMutation.isError ? (
              <div className="mt-6 rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-5">
                <p className="text-sm font-bold text-red-300">
                  Impossible d'exécuter cette analyse.
                </p>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Vérifiez que le serveur backend est
                  disponible et que votre session
                  administrateur est toujours valide.
                </p>
              </div>
            ) : null}

            {hasSubmittedQuery &&
            !analyticsMutation.isPending &&
            !analyticsMutation.isError ? (
              <div className="mt-8">
                <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-600">
                      Requête analysée
                    </p>

                    <p className="mt-1 text-sm font-medium text-slate-300">
                      {submittedQuery}
                    </p>
                  </div>
                </div>

                {!analyticsMutation.data?.supported ? (
                  <UnsupportedResult />
                ) : result?.type === "metric" ? (
                  <MetricResult result={result} />
                ) : result?.type === "trend" ? (
                  <TrendResult result={result} />
                ) : result?.type === "comparison" ? (
                  <ComparisonResult result={result} />
                ) : (
                  <UnsupportedResult />
                )}
              </div>
            ) : null}

            {!hasSubmittedQuery &&
            !analyticsMutation.isPending ? (
              <div className="mt-8">
                <EmptyAnalysisState />
              </div>
            ) : null}

            {analyticsMutation.isPending ? (
              <div className="mt-8 rounded-2xl border border-[#f5c400]/20 bg-[#f5c400]/[0.03] p-8">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 animate-pulse rounded-xl bg-[#f5c400]/20" />

                  <div className="flex-1">
                    <div className="h-3 w-32 animate-pulse rounded bg-white/10" />

                    <div className="mt-3 h-4 w-64 animate-pulse rounded bg-white/10" />
                  </div>
                </div>

                <p className="mt-5 text-sm text-slate-500">
                  Analyse des données KBR en cours...
                </p>
              </div>
            ) : null}
          </div>
        </section>

        {/* ============================================================
            ARCHITECTURE
        ============================================================ */}

        <section className="mt-10">
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Architecture
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Pipeline analytique
            </h2>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
              Les réponses analytiques reposent sur des
              données déterministes avant leur présentation
              à l'administrateur.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <ArchitectureStep
              number="01"
              title="Question"
              description="La question est saisie en langage naturel dans l'interface AI Analyst."
            />

            <ArchitectureStep
              number="02"
              title="Intent"
              description="Le système identifie si la demande correspond à une analyse supportée."
            />

            <ArchitectureStep
              number="03"
              title="Analytics Engine"
              description="Le moteur applique les métriques et périodes analytiques disponibles."
            />

            <ArchitectureStep
              number="04"
              title="PostgreSQL"
              description="Les valeurs sont calculées à partir des données persistées de KBR."
            />

            <ArchitectureStep
              number="05"
              title="Résultat vérifié"
              description="Le résultat déterministe est présenté sans inventer de valeur manquante."
            />
          </div>
        </section>
      </div>
    </section>
  );
}