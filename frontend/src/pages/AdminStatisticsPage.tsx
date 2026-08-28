import { Link } from "react-router-dom";

import {
  useStatisticsOverview,
  useStatisticsTrends,
} from "../features/statistics/statistics.hooks";

interface StatCardProps {
  label: string;
  value: number;
  description: string;
}

function StatCard({
  label,
  value,
  description,
}: StatCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition hover:border-white/20 hover:bg-white/[0.055]">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-4xl font-black tracking-tight text-white">
        {value}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>
    </div>
  );
}

interface DistributionRowProps {
  label: string;
  value: number;
  total: number;
}

function DistributionRow({
  label,
  value,
  total,
}: DistributionRowProps) {
  const percentage =
    total > 0
      ? Math.round((value / total) * 100)
      : 0;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-4">
        <span className="text-sm font-semibold text-slate-300">
          {label}
        </span>

        <span className="text-sm font-bold text-white">
          {value}
          <span className="ml-2 text-xs font-medium text-slate-600">
            {percentage}%
          </span>
        </span>
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

interface MiniStatProps {
  label: string;
  value: number;
}

function MiniStat({
  label,
  value,
}: MiniStatProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.025] p-4">
      <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-600">
        {label}
      </p>

      <p className="mt-2 text-2xl font-black text-white">
        {value}
      </p>
    </div>
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
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
        {eyebrow}
      </p>

      <h2 className="mt-1 text-lg font-black text-white">
        {title}
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        {description}
      </p>
    </div>
  );
}

function TrendChart({
  data,
}: {
  data: {
    month: string;
    members: number;
    events: number;
    activities: number;
    news: number;
  }[];
}) {
  const maxValue = Math.max(
    1,
    ...data.flatMap((item) => [
      item.members,
      item.events,
      item.activities,
      item.news,
    ]),
  );

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
      <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
            Évolution
          </p>

          <h2 className="mt-1 text-xl font-black text-white">
            Activité mensuelle
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Nombre de nouveaux éléments créés chaque mois.
          </p>
        </div>

        <div className="flex flex-wrap gap-4 text-xs font-semibold text-slate-400">
          <LegendItem label="Membres" />
          <LegendItem label="Événements" />
          <LegendItem label="Activités" />
          <LegendItem label="Actualités" />
        </div>
      </div>

      <div className="flex h-72 items-end gap-2 overflow-x-auto pb-8">
        {data.map((item) => {
          const total =
            item.members +
            item.events +
            item.activities +
            item.news;

          const height =
            maxValue > 0
              ? Math.max(
                  total > 0 ? 8 : 2,
                  (total / maxValue) * 100,
                )
              : 0;

          return (
            <div
              key={item.month}
              className="flex min-w-[64px] flex-1 flex-col items-center justify-end"
            >
              <div className="mb-3 text-xs font-bold text-slate-500">
                {total}
              </div>

              <div
                className="w-full max-w-12 rounded-t-lg bg-[#f5c400]/80 transition-all duration-500 hover:bg-[#f5c400]"
                style={{
                  height: `${height}%`,
                }}
                title={`${item.month}: ${total} éléments`}
              />

              <div className="mt-3 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                {formatMonth(item.month)}
              </div>
            </div>
          );
        })}
      </div>

      {data.length === 0 && (
        <div className="flex h-64 items-center justify-center text-sm text-slate-600">
          Aucune donnée disponible.
        </div>
      )}
    </div>
  );
}

function LegendItem({
  label,
}: {
  label: string;
}) {
  return (
    <span className="flex items-center gap-2">
      <span className="h-2 w-2 rounded-full bg-[#f5c400]" />
      {label}
    </span>
  );
}

function formatMonth(
  value: string,
): string {
  const [year, month] =
    value.split("-");

  if (!year || !month) {
    return value;
  }

  const date = new Date(
    Number(year),
    Number(month) - 1,
    1,
  );

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      month: "short",
    },
  )
    .format(date)
    .replace(".", "");
}

function StatisticsSkeleton() {
  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-4 w-28 rounded bg-white/10" />

        <div className="mt-3 h-10 w-80 rounded bg-white/10" />

        <div className="mt-3 h-5 w-full max-w-2xl rounded bg-white/10" />

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({
            length: 4,
          }).map((_, index) => (
            <div
              key={`stat-${index}`}
              className="h-40 rounded-2xl border border-white/10 bg-white/[0.04]"
            />
          ))}
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          {Array.from({
            length: 2,
          }).map((_, index) => (
            <div
              key={`distribution-${index}`}
              className="h-80 rounded-2xl border border-white/10 bg-white/[0.04]"
            />
          ))}
        </div>

        <div className="mt-10 h-96 rounded-2xl border border-white/10 bg-white/[0.04]" />

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {Array.from({
            length: 3,
          }).map((_, index) => (
            <div
              key={`content-${index}`}
              className="h-64 rounded-2xl border border-white/10 bg-white/[0.04]"
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function StatisticsError() {
  return (
    <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
      <div className="max-w-md text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/10 text-2xl font-black text-red-300">
          !
        </div>

        <h1 className="mt-5 text-2xl font-black">
          Impossible de charger les statistiques
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          Votre session administrateur est peut-être
          expirée ou le serveur est momentanément
          indisponible.
        </p>

        <Link
          to="/admin"
          className="mt-6 inline-flex rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/5"
        >
          Retour au tableau de bord
        </Link>
      </div>
    </section>
  );
}

export default function AdminStatisticsPage() {
  const overviewQuery =
    useStatisticsOverview();

  const trendsQuery =
    useStatisticsTrends(6);

  if (
    overviewQuery.isLoading ||
    trendsQuery.isLoading
  ) {
    return <StatisticsSkeleton />;
  }

  if (
    overviewQuery.isError ||
    trendsQuery.isError ||
    !overviewQuery.data ||
    !trendsQuery.data
  ) {
    return <StatisticsError />;
  }

  const {
    members,
    users,
    events,
    activities,
    news,
  } = overviewQuery.data;

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              Statistiques
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Analyse globale des membres, comptes et
              contenus de la plateforme KBR.
            </p>
          </div>

          <Link
            to="/admin"
            className="inline-flex w-fit rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
          >
            ← Tableau de bord
          </Link>
        </div>

        {/* Main KPIs */}
        <section>
          <SectionHeader
            eyebrow="Vue globale"
            title="Indicateurs principaux"
            description="État actuel des principales ressources de KBR."
          />

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Membres"
              value={members.total}
              description="Membres enregistrés"
            />

            <StatCard
              label="Événements"
              value={events.total}
              description="Événements créés"
            />

            <StatCard
              label="Activités"
              value={activities.total}
              description="Activités créées"
            />

            <StatCard
              label="Actualités"
              value={news.total}
              description="Articles créés"
            />
          </div>
        </section>

        {/* Members / Users */}
        <section className="mt-10 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
            <SectionHeader
              eyebrow="Membres"
              title="Répartition des membres"
              description="État des comptes membres KBR."
            />

            <div className="space-y-5">
              <DistributionRow
                label="Actifs"
                value={members.active}
                total={members.total}
              />

              <DistributionRow
                label="En attente"
                value={members.pending}
                total={members.total}
              />

              <DistributionRow
                label="Suspendus"
                value={members.suspended}
                total={members.total}
              />

              <DistributionRow
                label="Inactifs"
                value={members.inactive}
                total={members.total}
              />

              <DistributionRow
                label="Archivés"
                value={members.archived}
                total={members.total}
              />
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
            <SectionHeader
              eyebrow="Utilisateurs"
              title="Répartition des rôles"
              description="Répartition des comptes selon leur niveau d'accès."
            />

            <div className="space-y-5">
              <DistributionRow
                label="Membres"
                value={users.members}
                total={users.total}
              />

              <DistributionRow
                label="Staff"
                value={users.staff}
                total={users.total}
              />

              <DistributionRow
                label="Administrateurs"
                value={users.admins}
                total={users.total}
              />
            </div>

            <div className="mt-8 grid grid-cols-2 gap-3">
              <MiniStat
                label="Total"
                value={users.total}
              />

              <MiniStat
                label="Administrateurs"
                value={users.admins}
              />
            </div>
          </div>
        </section>

        {/* Trends */}
        <section className="mt-10">
          <TrendChart
            data={
              trendsQuery.data.months
            }
          />
        </section>

        {/* Events */}
        <section className="mt-10">
          <SectionHeader
            eyebrow="Événements"
            title="Statistiques des événements"
            description="État et calendrier des événements KBR."
          />

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
            <MiniStat
              label="Total"
              value={events.total}
            />

            <MiniStat
              label="Publiés"
              value={events.published}
            />

            <MiniStat
              label="Brouillons"
              value={events.draft}
            />

            <MiniStat
              label="Annulés"
              value={events.cancelled}
            />

            <MiniStat
              label="À venir"
              value={events.upcoming}
            />

            <MiniStat
              label="Passés"
              value={events.past}
            />
          </div>
        </section>

        {/* Activities */}
        <section className="mt-10">
          <SectionHeader
            eyebrow="Activités"
            title="Statistiques des activités"
            description="État et calendrier des activités et projets."
          />

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <MiniStat
              label="Total"
              value={activities.total}
            />

            <MiniStat
              label="Publiées"
              value={activities.published}
            />

            <MiniStat
              label="Brouillons"
              value={activities.draft}
            />

            <MiniStat
              label="À venir"
              value={activities.upcoming}
            />

            <MiniStat
              label="Passées"
              value={activities.past}
            />
          </div>
        </section>

        {/* News */}
        <section className="mt-10">
          <SectionHeader
            eyebrow="Actualités"
            title="Statistiques des actualités"
            description="État des articles du site officiel."
          />

          <div className="grid gap-4 sm:grid-cols-3">
            <MiniStat
              label="Total"
              value={news.total}
            />

            <MiniStat
              label="Publiées"
              value={news.published}
            />

            <MiniStat
              label="Brouillons"
              value={news.draft}
            />
          </div>
        </section>

        {/* Footer actions */}
        <section className="mt-10">
          <div className="rounded-2xl border border-[#f5c400]/20 bg-[#f5c400]/[0.04] p-6 sm:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
                  Administration
                </p>

                <h2 className="mt-2 text-xl font-black text-white">
                  Continuer la gestion
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                  Utilisez les outils d'administration pour
                  gérer les membres et les contenus de KBR.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link
                  to="/admin/members"
                  className="rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-[#050505] transition hover:bg-[#ffd21a]"
                >
                  Membres
                </Link>

                <Link
                  to="/admin/events"
                  className="rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/5"
                >
                  Événements
                </Link>

                <Link
                  to="/admin/news"
                  className="rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/5"
                >
                  Actualités
                </Link>
              </div>
            </div>
          </div>
        </section>
      </div>
    </section>
  );
}