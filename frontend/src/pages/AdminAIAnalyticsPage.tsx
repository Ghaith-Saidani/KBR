import {
  useMemo,
  useState,
} from "react";
import type { FormEvent } from "react";

import { Link } from "react-router-dom";

import {
  useStatisticsOverview,
  useStatisticsTrends,
} from "../features/statistics/statistics.hooks";

import { useAnalyticsQuery } from "../features/analytics/analytics.hooks";

import type { AnalyticsResult } from "../features/analytics/analytics.types";

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

interface KpiCardProps {
  label: string;
  value: number;
  description: string;
}

function KpiCard({
  label,
  value,
  description,
}: KpiCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition hover:border-white/20 hover:bg-white/[0.055]">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-4xl font-black tracking-tight text-white">
        {formatNumber(value)}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>
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
      <div className="min-w-[680px] rounded-2xl border border-white/10 bg-white/[0.02] p-6">
        <div className="flex h-72 items-end gap-5">
          {months.map((item) => {
            const values = [
              {
                key: "members",
                value: item.members,
              },
              {
                key: "events",
                value: item.events,
              },
              {
                key: "activities",
                value: item.activities,
              },
              {
                key: "news",
                value: item.news,
              },
            ];

            return (
              <div
                key={item.month}
                className="flex min-w-[76px] flex-1 flex-col items-center justify-end gap-3"
              >
                <div className="flex h-56 w-full items-end justify-center gap-1">
                  {values.map((entry) => {
                    const height =
                      entry.value === 0
                        ? 0
                        : Math.max(
                            8,
                            (entry.value / maximum) * 100,
                          );

                    return (
                      <div
                        key={entry.key}
                        title={`${entry.key}: ${entry.value}`}
                        className="w-3 rounded-t-md bg-[#f5c400]/80 transition hover:bg-[#f5c400]"
                        style={{
                          height: `${height}%`,
                        }}
                      />
                    );
                  })}
                </div>

                <div className="text-center">
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

        <div className="mt-6 flex flex-wrap justify-center gap-5 border-t border-white/10 pt-5">
          <LegendItem
            label="Membres"
            value="members"
          />

          <LegendItem
            label="Événements"
            value="events"
          />

          <LegendItem
            label="Activités"
            value="activities"
          />

          <LegendItem
            label="Actualités"
            value="news"
          />
        </div>
      </div>
    </div>
  );
}

interface LegendItemProps {
  label: string;
  value: string;
}

function LegendItem({
  label,
  value,
}: LegendItemProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="h-2.5 w-2.5 rounded-full bg-[#f5c400]" />

      <span className="text-xs font-medium text-slate-500">
        {label}
      </span>

      <span className="text-[10px] uppercase tracking-wider text-slate-700">
        {value}
      </span>
    </div>
  );
}

interface ResultShellProps {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
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
        {/* Header */}
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

        {/* Overview */}
        <section>
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Vue analytique
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Indicateurs clés
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Données actuelles provenant de la plateforme
              KBR.
            </p>
          </div>

          {overviewLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map(
                (_, index) => (
                  <div
                    key={`overview-skeleton-${index}`}
                    className="h-40 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
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
                description="Membres enregistrés"
              />

              <KpiCard
                label="Événements"
                value={overview.events.total}
                description="Événements enregistrés"
              />

              <KpiCard
                label="Activités"
                value={overview.activities.total}
                description="Activités enregistrées"
              />

              <KpiCard
                label="Actualités"
                value={overview.news.total}
                description="Articles enregistrés"
              />
            </div>
          )}
        </section>

        {/* Trends */}
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
              du temps.
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

        {/* AI Analyst */}
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

            {/* Quick questions */}
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

            {/* Query error */}
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

            {/* Analysis result */}
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

            {/* Initial state */}
            {!hasSubmittedQuery &&
            !analyticsMutation.isPending ? (
              <div className="mt-8">
                <EmptyAnalysisState />
              </div>
            ) : null}

            {/* Loading */}
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

        {/* Architecture */}
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