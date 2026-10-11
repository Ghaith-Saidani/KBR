import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import {
  useMLRiskHealth,
  useMLRiskIncidents,
  useMLRiskObservations,
  useMLRiskSummary,
} from "../features/mlRisk/mlRisk.hooks";

import type {
  MLRiskIncident,
  MLRiskObservation,
  RiskLevel,
} from "../features/mlRisk/mlRisk.types";

const RISK_STYLES: Record<RiskLevel, string> = {
  high: "border-red-500/25 bg-red-500/10 text-red-300",
  medium: "border-amber-500/25 bg-amber-500/10 text-amber-300",
  low: "border-blue-500/25 bg-blue-500/10 text-blue-300",
  minimal: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
};

const RISK_LABELS: Record<RiskLevel, string> = {
  high: "Élevé",
  medium: "Moyen",
  low: "Faible",
  minimal: "Minimal",
};

const DISTRIBUTION_ORDER: RiskLevel[] = [
  "high",
  "medium",
  "low",
  "minimal",
];

function number(value: number | undefined | null): string {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(value);
}

function percent(value: number | undefined): string {
  if (value === undefined || !Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(1)} %`;
}

function formatDate(value?: string): string {
  if (!value) return "Date inconnue";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function riskStyle(level?: string): string {
  return level && level in RISK_STYLES
    ? RISK_STYLES[level as RiskLevel]
    : "border-white/10 bg-white/5 text-slate-300";
}

function Panel({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.025] p-5 sm:p-6">
      {eyebrow ? (
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#f5c400]">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="mt-1 text-lg font-black text-white">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-3 text-3xl font-black tracking-tight text-white">{value}</p>
      <p className="mt-2 text-xs text-slate-500">{hint}</p>
    </div>
  );
}

function RiskBadge({ level }: { level?: string }) {
  const label =
    level && level in RISK_LABELS
      ? RISK_LABELS[level as RiskLevel]
      : level ?? "Inconnu";

  return (
    <span className={`inline-flex rounded-lg border px-2.5 py-1 text-xs font-bold ${riskStyle(level)}`}>
      {label}
    </span>
  );
}

function DistributionRow({
  level,
  value,
  total,
}: {
  level: RiskLevel;
  value: number;
  total: number;
}) {
  const width = total > 0 ? Math.min(100, (value / total) * 100) : 0;
  const barClass: Record<RiskLevel, string> = {
    high: "bg-red-400",
    medium: "bg-amber-400",
    low: "bg-blue-400",
    minimal: "bg-emerald-400",
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="text-slate-300">{RISK_LABELS[level]}</span>
        <span className="font-bold tabular-nums text-white">{number(value)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full ${barClass[level]}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function ObservationCard({ item }: { item: MLRiskObservation }) {
  const reasons = Array.isArray(item.risk_reasons)
    ? item.risk_reasons.filter((reason): reason is string => typeof reason === "string")
    : [];
  const endpoint =
    (typeof item.endpoint_normalized === "string" && item.endpoint_normalized) ||
    (typeof item.endpoint === "string" && item.endpoint) ||
    "Endpoint inconnu";
  const action = typeof item.action === "string" ? item.action : endpoint;

  return (
    <article className="rounded-xl border border-white/10 bg-black/20 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="break-all text-sm font-bold text-white">{action}</p>
          <p className="mt-1 text-xs text-slate-500">{formatDate(item.occurred_at)}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <RiskBadge level={item.risk_level} />
          <span className="text-sm font-black tabular-nums text-white">
            {number(item.risk_score)}
          </span>
        </div>
      </div>
      {typeof item.status_code === "number" ? (
        <p className="mt-3 text-xs text-slate-500">HTTP {item.status_code}</p>
      ) : null}
      {reasons.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {reasons.map((reason) => (
            <span
              key={reason}
              className="rounded-md border border-white/10 bg-white/[0.035] px-2 py-1 text-[11px] text-slate-400"
            >
              {reason}
            </span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function IncidentCard({ item }: { item: MLRiskIncident }) {
  return (
    <article className="rounded-xl border border-white/10 bg-black/20 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="break-all text-sm font-bold text-white">{item.reason || item.incident_type}</p>
          <p className="mt-1 text-xs text-slate-500">{item.incident_id}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <RiskBadge level={item.risk_level} />
          <span className="text-sm font-black tabular-nums text-white">
            {number(item.risk_score)}
          </span>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-3">
        <div>
          <p className="text-slate-600">Événements</p>
          <p className="mt-1 font-bold text-slate-300">{number(item.event_count)}</p>
        </div>
        <div>
          <p className="text-slate-600">Début</p>
          <p className="mt-1 text-slate-300">{formatDate(item.start_time)}</p>
        </div>
        <div>
          <p className="text-slate-600">Endpoint</p>
          <p className="mt-1 break-all text-slate-300">{item.endpoint ?? "—"}</p>
        </div>
      </div>
    </article>
  );
}

function LoadingState() {
  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-4 w-32 rounded bg-white/10" />
        <div className="mt-4 h-10 w-72 rounded bg-white/10" />
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index} className="h-32 rounded-2xl border border-white/10 bg-white/[0.04]" />
          ))}
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="h-80 rounded-2xl border border-white/10 bg-white/[0.04]" />
          <div className="h-80 rounded-2xl border border-white/10 bg-white/[0.04]" />
        </div>
      </div>
    </section>
  );
}

export default function AdminMLRiskPage() {
  const summary = useMLRiskSummary();
  const observations = useMLRiskObservations(15);
  const incidents = useMLRiskIncidents(10);
  const health = useMLRiskHealth();

  if (summary.isLoading) return <LoadingState />;

  if (summary.isError || !summary.data) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 py-10 text-white">
        <div className="max-w-lg rounded-2xl border border-red-500/20 bg-red-500/5 p-7 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-red-300">
            ML Risk Monitoring
          </p>
          <h1 className="mt-3 text-2xl font-black">Rapport ML indisponible</h1>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Vérifiez que le pipeline de scoring a généré le rapport et que l'API peut lire le fichier.
          </p>
          <p className="mt-3 break-all text-xs text-slate-600">
            {health.data?.message ?? "Rapport non disponible ou requête refusée."}
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={() => {
                void summary.refetch();
                void health.refetch();
              }}
              className="rounded-xl bg-[#f5c400] px-4 py-2.5 text-sm font-bold text-black hover:bg-[#ffd21a]"
            >
              Réessayer
            </button>
            <Link
              to="/admin"
              className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 hover:bg-white/5"
            >
              Retour au dashboard
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const data = summary.data;
  const distribution = data.risk_distribution;
  const total = data.total_rows;
  const incidentDistribution = data.temporal_detection.incident_distribution ?? {};
  const incidentRiskDistribution = data.temporal_detection.incident_risk_distribution ?? {};

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration · Machine Learning
            </p>
            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              ML Risk Monitoring
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
              Détection comportementale par Isolation Forest, scoring explicable et regroupement temporel des incidents.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                void summary.refetch();
                void observations.refetch();
                void incidents.refetch();
                void health.refetch();
              }}
              className="rounded-xl border border-white/10 px-4 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              Actualiser
            </button>
            <Link
              to="/admin"
              className="rounded-xl bg-[#f5c400] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
            >
              Retour au dashboard
            </Link>
          </div>
        </header>

        <div className={`mb-6 flex flex-col gap-2 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between ${
          health.data?.available
            ? "border-emerald-500/20 bg-emerald-500/5"
            : "border-amber-500/20 bg-amber-500/5"
        }`}>
          <div>
            <p className="text-sm font-bold text-white">
              {health.data?.available ? "Rapport disponible" : "État du rapport inconnu"}
            </p>
            <p className="mt-1 text-xs text-slate-400">
              {health.data?.message ?? "Vérification de disponibilité…"}
            </p>
          </div>
          <span className="text-xs text-slate-500">
            Actualisation automatique chaque minute
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Événements scorés" value={number(data.total_rows)} hint={`${number(data.http_rows)} requêtes HTTP · ${number(data.business_rows)} événements métier`} />
          <MetricCard label="Incidents temporels" value={number(data.temporal_detection.incident_count)} hint="Bursts détectés dans les fenêtres temporelles" />
          <MetricCard label="Risque moyen" value={percent(data.overall.mean_risk_score)} hint="Score moyen de 0 à 1" />
          <MetricCard label="Incidents à risque élevé" value={number(incidentRiskDistribution.high ?? 0)} hint="Score d'incident ≥ 0,75" />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Panel title="Distribution du risque" eyebrow="Tous les événements">
            <div className="space-y-5">
              {DISTRIBUTION_ORDER.map((level) => (
                <DistributionRow
                  key={level}
                  level={level}
                  value={distribution[level] ?? 0}
                  total={total}
                />
              ))}
            </div>
            <p className="mt-5 text-xs leading-5 text-slate-500">
              Les niveaux d'événement et les niveaux d'incident sont calculés séparément.
            </p>
          </Panel>

          <Panel title="HTTP vs métier" eyebrow="Comparaison des populations">
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                { label: "Requêtes HTTP", section: data.http },
                { label: "Événements métier", section: data.business },
              ].map(({ label, section }) => (
                <div key={label} className="rounded-xl border border-white/10 bg-black/20 p-4">
                  <p className="text-sm font-bold text-white">{label}</p>
                  <p className="mt-3 text-2xl font-black text-white">{number(section.rows)}</p>
                  <p className="mt-1 text-xs text-slate-500">Événements analysés</p>
                  <div className="mt-4 space-y-3 border-t border-white/10 pt-4">
                    <div className="flex justify-between gap-3 text-xs">
                      <span className="text-slate-500">Score moyen</span>
                      <span className="font-bold text-white">{percent(section.mean_risk_score)}</span>
                    </div>
                    {DISTRIBUTION_ORDER.map((level) => {
                      const key = `${level}_risk_count` as const;
                      return (
                        <div key={level} className="flex justify-between gap-3 text-xs">
                          <span className="text-slate-500">{RISK_LABELS[level]}</span>
                          <span className="font-bold text-slate-300">{number(section[key])}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Types d'incidents</p>
              <div className="mt-3 space-y-2">
                {Object.entries(incidentDistribution).length === 0 ? (
                  <p className="text-sm text-slate-500">Aucun incident répertorié.</p>
                ) : Object.entries(incidentDistribution).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between gap-3 text-sm">
                    <span className="break-all text-slate-400">{type.replaceAll("_", " ")}</span>
                    <span className="font-bold text-white">{number(count)}</span>
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <Panel title="Incidents prioritaires" eyebrow="Agrégation temporelle">
            {incidents.isError ? (
              <p className="text-sm text-red-300">Impossible de charger les incidents.</p>
            ) : incidents.isLoading ? (
              <p className="text-sm text-slate-500">Chargement des incidents…</p>
            ) : incidents.data?.items.length ? (
              <div className="space-y-3">
                {incidents.data.items.map((item) => (
                  <IncidentCard key={item.incident_id} item={item} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Aucun incident disponible.</p>
            )}
          </Panel>

          <Panel title="Observations les plus risquées" eyebrow="Scoring par événement">
            {observations.isError ? (
              <p className="text-sm text-red-300">Impossible de charger les observations.</p>
            ) : observations.isLoading ? (
              <p className="text-sm text-slate-500">Chargement des observations…</p>
            ) : observations.data?.items.length ? (
              <div className="space-y-3">
                {observations.data.items.map((item, index) => (
                  <ObservationCard key={item.id ?? `${item.occurred_at}-${index}`} item={item} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Aucune observation disponible.</p>
            )}
          </Panel>
        </div>

        <p className="mt-6 text-xs leading-5 text-slate-600">
          Les scores sont des signaux d'aide à l'analyse et ne constituent pas, à eux seuls, une preuve d'incident de sécurité. Le rapport est calculé par le pipeline batch et relu par l'API.
        </p>
      </div>
    </section>
  );
}
