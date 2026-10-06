import { Link } from "react-router-dom";

import {
  useRecentBusinessActivity,
  useStatisticsOverview,
  useStatisticsTrends,
} from "../features/statistics/statistics.hooks";

import type { RecentBusinessActivity } from "../features/statistics/statistics.types";

function formatNumber(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat("fr-FR").format(value);
}

function formatPercentage(value: number | null): string {
  if (value === null) {
    return "Base 0";
  }

  if (value === 0) {
    return "0 %";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(1)} %`;
}

function calculateChange(
  current: number,
  previous: number,
): number | null {
  if (previous === 0) {
    return current === 0 ? 0 : null;
  }

  return ((current - previous) / previous) * 100;
}

function getChangeClassName(
  current: number,
  previous: number,
): string {
  if (current === previous) {
    return "text-slate-500";
  }

  return current > previous
    ? "text-emerald-400"
    : "text-red-400";
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
  const change = calculateChange(
    currentMonth,
    previousMonth,
  );

  const changeClassName = getChangeClassName(
    currentMonth,
    previousMonth,
  );

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-4xl font-black tracking-tight text-white">
        {formatNumber(value)}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>

      <div className="mt-5 border-t border-white/10 pt-4">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-600">
            Ce mois
          </span>

          <span className="text-sm font-black text-white">
            {formatNumber(currentMonth)}
          </span>
        </div>

        <div className="mt-2 flex items-center justify-between">
          <span className="text-xs text-slate-600">
            Mois précédent
          </span>

          <span className="text-sm font-semibold text-slate-400">
            {formatNumber(previousMonth)}
          </span>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <span
            className={`text-xs font-medium ${changeClassName}`}
          >
            {currentMonth === previousMonth
              ? "Stable"
              : currentMonth > previousMonth
                ? "En hausse"
                : "En baisse"}
          </span>

          <span
            className={`text-xs font-black ${changeClassName}`}
          >
            {formatPercentage(change)}
          </span>
        </div>
      </div>
    </article>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-5">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
        {eyebrow}
      </p>

      <h2 className="mt-1 text-lg font-black text-white">
        {title}
      </h2>

      <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
}

function StatusBar({
  label,
  value,
  total,
}: {
  label: string;
  value: number;
  total: number;
}) {
  const percentage =
    total > 0 ? (value / total) * 100 : 0;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-4">
        <span className="text-sm text-slate-400">
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
          className="h-full rounded-full bg-[#f5c400]"
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

function DistributionCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.025] p-6">
      <h3 className="text-lg font-black text-white">
        {title}
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        {description}
      </p>

      <div className="mt-6 space-y-5">
        {children}
      </div>
    </article>
  );
}

const ACTION_LABELS: Record<string, string> = {
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

function formatAction(action: string): string {
  return (
    ACTION_LABELS[action] ??
    action.replaceAll("_", " ")
  );
}

function formatActivityDetails(
  details: string | null,
): string | null {
  if (!details) {
    return null;
  }

  return details
    .replace(/^SEED:\S+\s*/i, "")
    .trim();
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function RecentActivity({
  activities,
  loading,
  error,
}: {
  activities: RecentBusinessActivity[];
  loading: boolean;
  error: boolean;
}) {
  return (
    <section>
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <SectionHeader
          eyebrow="Opérations"
          title="Activité récente"
          description="Dernières actions métier enregistrées sur la plateforme."
        />

        <Link
          to="/admin/activity-logs"
          className="mb-5 inline-flex w-fit rounded-xl border border-white/10 px-4 py-2.5 text-xs font-bold text-slate-400 transition hover:bg-white/5 hover:text-white"
        >
          Tous les journaux →
        </Link>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <div
                key={index}
                className="h-20 animate-pulse rounded-xl bg-white/[0.04]"
              />
            ))}
          </div>
        ) : error ? (
          <p className="text-sm text-red-300">
            Impossible de charger l'activité récente.
          </p>
        ) : activities.length === 0 ? (
          <p className="text-sm text-slate-500">
            Aucune activité métier récente.
          </p>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => {
              const details = formatActivityDetails(
                activity.details,
              );

              return (
                <div
                  key={activity.id}
                  className="rounded-xl border border-white/10 bg-white/[0.02] p-4"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-black text-white">
                        {formatAction(activity.action)}
                      </span>

                      {activity.resource_type ? (
                        <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-500">
                          {activity.resource_type}
                        </span>
                      ) : null}
                    </div>

                    <time className="text-xs text-slate-600">
                      {formatTimestamp(
                        activity.occurred_at,
                      )}
                    </time>
                  </div>

                  {details ? (
                    <p className="mt-2 text-sm leading-5 text-slate-500">
                      {details}
                    </p>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function TrendChart({
  months,
}: {
  months: {
    month: string;
    members: number;
    events: number;
    activities: number;
    news: number;
  }[];
}) {
  const maximum = Math.max(
    ...months.flatMap((item) => [
      item.members,
      item.events,
      item.activities,
      item.news,
    ]),
    1,
  );

  if (months.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-500">
        Aucune donnée historique disponible.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.025] p-6">
      <div className="mb-6 flex flex-wrap gap-5">
        <span className="text-xs text-slate-400">
          Membres
        </span>
        <span className="text-xs text-slate-400">
          Événements
        </span>
        <span className="text-xs text-slate-400">
          Activités
        </span>
        <span className="text-xs text-slate-400">
          Actualités
        </span>
      </div>

      <div className="flex min-w-[720px] items-end gap-5">
        {months.map((item) => {
          const values = [
            item.members,
            item.events,
            item.activities,
            item.news,
          ];

          return (
            <div
              key={item.month}
              className="flex flex-1 flex-col items-center"
            >
              <div className="flex h-56 w-full items-end justify-center gap-1">
                {values.map((value, index) => (
                  <div
                    key={index}
                    title={formatNumber(value)}
                    className={`w-3 rounded-t-md ${
                      index === 0
                        ? "bg-blue-500"
                        : index === 1
                          ? "bg-[#f5c400]"
                          : index === 2
                            ? "bg-purple-500"
                            : "bg-emerald-500"
                    }`}
                    style={{
                      height: `${
                        value === 0
                          ? 0
                          : Math.max(
                              6,
                              (value / maximum) * 100,
                            )
                      }%`,
                    }}
                  />
                ))}
              </div>

              <p className="mt-3 text-xs font-bold text-slate-400">
                {formatMonth(item.month)}
              </p>

              <p className="mt-1 text-[10px] text-slate-600">
                {item.month.slice(0, 4)}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function AdminStatisticsPage() {
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
    isLoading: activityLoading,
    isError: activityError,
  } = useRecentBusinessActivity(10);

  return (
    <main className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <header className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              Statistiques
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Vue exécutive de l'état et de l'activité
              opérationnelle de KBR.
            </p>
          </div>

          <Link
            to="/admin/ai-analytics"
            className="inline-flex w-fit items-center rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-black text-[#050505] transition hover:bg-[#ffd21a]"
          >
            Ouvrir AI Analyst →
          </Link>
        </header>

        <section>
          <SectionHeader
            eyebrow="Vue exécutive"
            title="Indicateurs clés"
            description="Volumes actuels et évolution par rapport au mois précédent."
          />

          {overviewLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div
                  key={index}
                  className="h-56 animate-pulse rounded-2xl bg-white/[0.04]"
                />
              ))}
            </div>
          ) : overviewError || !overview ? (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-6 text-sm text-red-300">
              Impossible de charger les statistiques.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KpiCard
                label="Membres"
                value={overview.members.total}
                currentMonth={overview.members.created_this_month}
                previousMonth={overview.members.created_last_month}
                description="Membres enregistrés"
              />

              <KpiCard
                label="Événements"
                value={overview.events.total}
                currentMonth={overview.events.created_this_month}
                previousMonth={overview.events.created_last_month}
                description="Événements enregistrés"
              />

              <KpiCard
                label="Activités"
                value={overview.activities.total}
                currentMonth={overview.activities.created_this_month}
                previousMonth={overview.activities.created_last_month}
                description="Activités enregistrées"
              />

              <KpiCard
                label="Actualités"
                value={overview.news.total}
                currentMonth={overview.news.created_this_month}
                previousMonth={overview.news.created_last_month}
                description="Articles enregistrés"
              />
            </div>
          )}
        </section>

        {overview ? (
          <section className="mt-10">
            <SectionHeader
              eyebrow="État actuel"
              title="Répartition opérationnelle"
              description="État des membres, utilisateurs et contenus de la plateforme."
            />

            <div className="grid gap-4 lg:grid-cols-3">
              <DistributionCard
                title="Membres"
                description="Répartition par statut."
              >
                <StatusBar
                  label="Actifs"
                  value={overview.members.active}
                  total={overview.members.total}
                />
                <StatusBar
                  label="En attente"
                  value={overview.members.pending}
                  total={overview.members.total}
                />
                <StatusBar
                  label="Suspendus"
                  value={overview.members.suspended}
                  total={overview.members.total}
                />
                <StatusBar
                  label="Inactifs"
                  value={overview.members.inactive}
                  total={overview.members.total}
                />
                <StatusBar
                  label="Archivés"
                  value={overview.members.archived}
                  total={overview.members.total}
                />
              </DistributionCard>

              <DistributionCard
                title="Utilisateurs"
                description="Répartition par rôle."
              >
                <StatusBar
                  label="Membres"
                  value={overview.users.members}
                  total={overview.users.total}
                />
                <StatusBar
                  label="Staff"
                  value={overview.users.staff}
                  total={overview.users.total}
                />
                <StatusBar
                  label="Administrateurs"
                  value={overview.users.admins}
                  total={overview.users.total}
                />
              </DistributionCard>

              <DistributionCard
                title="Événements"
                description="Répartition par état."
              >
                <StatusBar
                  label="Publiés"
                  value={overview.events.published}
                  total={overview.events.total}
                />
                <StatusBar
                  label="Brouillons"
                  value={overview.events.draft}
                  total={overview.events.total}
                />
                <StatusBar
                  label="Annulés"
                  value={overview.events.cancelled}
                  total={overview.events.total}
                />
                <StatusBar
                  label="À venir"
                  value={overview.events.upcoming}
                  total={overview.events.total}
                />
                <StatusBar
                  label="Passés"
                  value={overview.events.past}
                  total={overview.events.total}
                />
              </DistributionCard>
            </div>
          </section>
        ) : null}

        <section className="mt-10">
          <SectionHeader
            eyebrow="Historique"
            title="Évolution mensuelle"
            description="Nouveaux éléments créés au cours des six derniers mois."
          />

          {trendsLoading ? (
            <div className="h-80 animate-pulse rounded-2xl bg-white/[0.04]" />
          ) : trendsError || !trends ? (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.05] p-6 text-sm text-red-300">
              Impossible de charger les tendances.
            </div>
          ) : (
            <TrendChart months={trends.months} />
          )}
        </section>

        <div className="mt-10">
          <RecentActivity
            activities={recentActivity?.activities ?? []}
            loading={activityLoading}
            error={activityError}
          />
        </div>

        <section className="mt-10 rounded-2xl border border-[#f5c400]/20 bg-[#f5c400]/[0.04] p-6 sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
                Analyse avancée
              </p>

              <h2 className="mt-2 text-xl font-black text-white">
                Besoin d'aller plus loin ?
              </h2>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                Utilisez AI Analyst pour poser des questions
                en langage naturel, comparer des périodes,
                analyser la croissance, les distributions et
                les classements.
              </p>
            </div>

            <Link
              to="/admin/ai-analytics"
              className="inline-flex shrink-0 items-center justify-center rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-black text-[#050505] transition hover:bg-[#ffd21a]"
            >
              Lancer AI Analyst →
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}