import {
  useMemo,
  useState,
} from "react";

import {
  useAdminActivityLogs,
} from "../features/admin/adminActivity.hooks";

import type {
  ActivityType,
  UserActivity,
} from "../features/admin/adminActivity.types";

const PAGE_SIZE = 20;

const ACTIVITY_TYPE_OPTIONS: Array<{
  value: "" | ActivityType;
  label: string;
}> = [
  {
    value: "",
    label: "Toutes les activités",
  },
  {
    value: "business",
    label: "Actions métier",
  },
  {
    value: "technical",
    label: "Activité technique",
  },
];

const ACTION_OPTIONS = [
  {
    value: "",
    label: "Toutes les actions",
  },
  {
    value: "MEMBER_UPDATED",
    label: "Membre modifié",
  },
  {
    value: "MEMBER_DEACTIVATED",
    label: "Membre désactivé",
  },
  {
    value: "MEMBER_REACTIVATED",
    label: "Membre réactivé",
  },
  {
    value: "MEMBER_ARCHIVED",
    label: "Membre archivé",
  },
  {
    value: "MEMBER_DELETED",
    label: "Membre supprimé",
  },
  {
    value: "EVENT_CREATED",
    label: "Événement créé",
  },
  {
    value: "EVENT_UPDATED",
    label: "Événement modifié",
  },
  {
    value: "EVENT_PUBLISHED",
    label: "Événement publié",
  },
  {
    value: "EVENT_CANCELLED",
    label: "Événement annulé",
  },
  {
    value: "EVENT_DELETED",
    label: "Événement supprimé",
  },
  {
    value: "NEWS_CREATED",
    label: "Article créé",
  },
  {
    value: "NEWS_UPDATED",
    label: "Article modifié",
  },
  {
    value: "NEWS_PUBLISHED",
    label: "Article publié",
  },
  {
    value: "NEWS_UNPUBLISHED",
    label: "Article dépublié",
  },
  {
    value: "NEWS_DELETED",
    label: "Article supprimé",
  },
  {
    value: "ACTIVITY_CREATED",
    label: "Activité créée",
  },
  {
    value: "ACTIVITY_UPDATED",
    label: "Activité modifiée",
  },
  {
    value: "ACTIVITY_PUBLISHED",
    label: "Activité publiée",
  },
  {
    value: "ACTIVITY_DELETED",
    label: "Activité supprimée",
  },
  {
    value: "LOGIN",
    label: "Connexion",
  },
  {
    value: "REGISTER",
    label: "Inscription",
  },
  {
    value: "USER_ACTIVATED",
    label: "Utilisateur activé",
  },
];

const RESOURCE_OPTIONS = [
  {
    value: "",
    label: "Toutes les ressources",
  },
  {
    value: "member",
    label: "Membres",
  },
  {
    value: "event",
    label: "Événements",
  },
  {
    value: "news",
    label: "Actualités",
  },
  {
    value: "activity",
    label: "Activités",
  },
  {
    value: "authentication",
    label: "Authentification",
  },
  {
    value: "http_request",
    label: "Requêtes HTTP",
  },
];

function formatDate(
  value: string,
) {
  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "short",
      timeStyle: "medium",
    },
  ).format(new Date(value));
}

function formatAction(
  action: string,
) {
  const labels: Record<string, string> = {
    MEMBER_UPDATED: "Membre modifié",
    MEMBER_DEACTIVATED: "Membre désactivé",
    MEMBER_REACTIVATED: "Membre réactivé",
    MEMBER_ARCHIVED: "Membre archivé",
    MEMBER_DELETED: "Membre supprimé",

    EVENT_CREATED: "Événement créé",
    EVENT_UPDATED: "Événement modifié",
    EVENT_PUBLISHED: "Événement publié",
    EVENT_CANCELLED: "Événement annulé",
    EVENT_DELETED: "Événement supprimé",

    NEWS_CREATED: "Article créé",
    NEWS_UPDATED: "Article modifié",
    NEWS_PUBLISHED: "Article publié",
    NEWS_UNPUBLISHED: "Article dépublié",
    NEWS_DELETED: "Article supprimé",

    ACTIVITY_CREATED: "Activité créée",
    ACTIVITY_UPDATED: "Activité modifiée",
    ACTIVITY_PUBLISHED: "Activité publiée",
    ACTIVITY_DELETED: "Activité supprimée",

    LOGIN: "Connexion",
    REGISTER: "Inscription",
    USER_ACTIVATED: "Utilisateur activé",
  };

  if (labels[action]) {
    return labels[action];
  }

  return action
    .toLowerCase()
    .replaceAll("_", " ");
}

function formatResource(
  resourceType: string | null,
) {
  if (!resourceType) {
    return "—";
  }

  const labels: Record<string, string> = {
    member: "Membre",
    event: "Événement",
    news: "Actualité",
    activity: "Activité",
    authentication: "Authentification",
    http_request: "Requête HTTP",
  };

  return (
    labels[resourceType] ??
    resourceType
  );
}

function getActionStyle(
  action: string,
) {
  const normalized = action.toUpperCase();

  if (
    normalized.includes("DELETE") ||
    normalized.includes("DEACTIVATED") ||
    normalized.includes("CANCELLED") ||
    normalized.includes("UNPUBLISHED") ||
    normalized.includes("FAIL")
  ) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  if (
    normalized.includes("CREATE") ||
    normalized.includes("REGISTER") ||
    normalized.includes("LOGIN") ||
    normalized.includes("REACTIVATED")
  ) {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }

  if (
    normalized.includes("PUBLISH") ||
    normalized.includes("ARCHIVED")
  ) {
    return "border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]";
  }

  if (
    normalized.includes("UPDATE") ||
    normalized.includes("EDIT")
  ) {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  return "border-white/10 bg-white/[0.05] text-slate-300";
}

function getActionDot(
  action: string,
) {
  const normalized = action.toUpperCase();

  if (
    normalized.includes("DELETE") ||
    normalized.includes("DEACTIVATED") ||
    normalized.includes("CANCELLED") ||
    normalized.includes("UNPUBLISHED")
  ) {
    return "bg-red-400";
  }

  if (
    normalized.includes("CREATE") ||
    normalized.includes("REGISTER") ||
    normalized.includes("LOGIN") ||
    normalized.includes("REACTIVATED")
  ) {
    return "bg-emerald-400";
  }

  if (
    normalized.includes("PUBLISH") ||
    normalized.includes("ARCHIVED")
  ) {
    return "bg-[#f5c400]";
  }

  if (
    normalized.includes("UPDATE") ||
    normalized.includes("EDIT")
  ) {
    return "bg-blue-400";
  }

  return "bg-slate-400";
}

function formatMetadataValue(
  value: unknown,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (
    typeof value === "object"
  ) {
    return JSON.stringify(
      value,
      null,
      2,
    );
  }

  return String(value);
}

function getMetadataEntries(
  activity: UserActivity,
) {
  if (
    !activity.activity_metadata
  ) {
    return [];
  }

  return Object.entries(
    activity.activity_metadata,
  );
}

function ActivityDetails({
  activity,
}: {
  activity: UserActivity;
}) {
  const metadataEntries =
    getMetadataEntries(activity);

  return (
    <div className="border-t border-white/10 bg-black/20 px-6 py-6">
      <div className="grid gap-6 lg:grid-cols-3">

        {/* General information */}
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-600">
            Informations
          </p>

          <div className="mt-4 space-y-3">
            <div>
              <p className="text-xs text-slate-600">
                Action
              </p>

              <p className="mt-1 text-sm font-bold text-white">
                {formatAction(
                  activity.action,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Ressource
              </p>

              <p className="mt-1 text-sm text-slate-300">
                {formatResource(
                  activity.resource_type,
                )}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Identifiant de ressource
              </p>

              <p className="mt-1 break-all font-mono text-xs text-slate-400">
                {activity.resource_id ??
                  "—"}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Date
              </p>

              <p className="mt-1 text-sm text-slate-300">
                {formatDate(
                  activity.occurred_at,
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Technical information */}
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-600">
            Informations techniques
          </p>

          <div className="mt-4 space-y-3">
            <div>
              <p className="text-xs text-slate-600">
                Méthode
              </p>

              <p className="mt-1 font-mono text-xs text-slate-300">
                {activity.method ??
                  "—"}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Endpoint
              </p>

              <p className="mt-1 break-all font-mono text-xs text-slate-400">
                {activity.endpoint ??
                  "—"}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Adresse IP
              </p>

              <p className="mt-1 font-mono text-xs text-slate-400">
                {activity.ip_address ??
                  "—"}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Utilisateur
              </p>

              <p className="mt-1 break-all font-mono text-xs text-slate-400">
                {activity.user_id ??
                  "Système"}
              </p>
            </div>
          </div>
        </div>

        {/* Business details */}
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-600">
            Détails métier
          </p>

          {activity.details && (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm leading-6 text-slate-300">
                {activity.details}
              </p>
            </div>
          )}

          {metadataEntries.length >
            0 && (
            <div className="mt-4 space-y-3">
              {metadataEntries.map(
                ([key, value]) => (
                  <div
                    key={key}
                    className="rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3"
                  >
                    <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-600">
                      {key.replaceAll(
                        "_",
                        " ",
                      )}
                    </p>

                    <p className="mt-1 whitespace-pre-wrap break-words font-mono text-xs text-slate-300">
                      {formatMetadataValue(
                        value,
                      )}
                    </p>
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </div>

      {activity.user_agent && (
        <div className="mt-6 border-t border-white/5 pt-5">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-600">
            User agent
          </p>

          <p className="mt-2 break-all font-mono text-xs leading-5 text-slate-600">
            {activity.user_agent}
          </p>
        </div>
      )}
    </div>
  );
}

function ActivityLogsSkeleton() {
  return (
    <main className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-4 w-32 rounded bg-white/10" />

        <div className="mt-3 h-10 w-72 rounded bg-white/10" />

        <div className="mt-3 h-5 w-full max-w-2xl rounded bg-white/10" />

        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.04] p-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            {Array.from({
              length: 5,
            }).map((_, index) => (
              <div
                key={`filter-skeleton-${index}`}
                className="h-20 rounded-xl bg-white/5"
              />
            ))}
          </div>
        </div>

        <div className="mt-6 h-96 rounded-2xl border border-white/10 bg-white/[0.04]" />
      </div>
    </main>
  );
}

export default function AdminActivityLogsPage() {
  const [page, setPage] =
    useState(1);

  const [
    activityType,
    setActivityType,
  ] = useState<"" | ActivityType>(
    "",
  );

  const [action, setAction] =
    useState("");

  const [method, setMethod] =
    useState("");

  const [
    resourceType,
    setResourceType,
  ] = useState("");

  const [
    sortOrder,
    setSortOrder,
  ] = useState<
    "asc" | "desc"
  >("desc");

  const [
    expandedActivityId,
    setExpandedActivityId,
  ] = useState<string | null>(
    null,
  );

  const filters = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      activity_type:
        activityType || undefined,
      action:
        action || undefined,
      method:
        method || undefined,
      resource_type:
        resourceType || undefined,
      sort_order: sortOrder,
    }),
    [
      page,
      activityType,
      action,
      method,
      resourceType,
      sortOrder,
    ],
  );

  const {
    data,
    isLoading,
    isError,
    error,
  } = useAdminActivityLogs(
    filters,
  );

  const resetFilters = () => {
    setActivityType("");
    setAction("");
    setMethod("");
    setResourceType("");
    setSortOrder("desc");
    setPage(1);
    setExpandedActivityId(null);
  };

  const handleActivityTypeChange = (
    value: "" | ActivityType,
  ) => {
    setActivityType(value);
    setAction("");
    setPage(1);
    setExpandedActivityId(null);
  };

  const handleActionChange = (
    value: string,
  ) => {
    setAction(value);
    setPage(1);
    setExpandedActivityId(null);
  };

  const handleResourceChange = (
    value: string,
  ) => {
    setResourceType(value);
    setPage(1);
    setExpandedActivityId(null);
  };

  const handleMethodChange = (
    value: string,
  ) => {
    setMethod(value);
    setPage(1);
    setExpandedActivityId(null);
  };

  const handleSortChange = (
    value: "asc" | "desc",
  ) => {
    setSortOrder(value);
    setPage(1);
    setExpandedActivityId(null);
  };

  if (isLoading) {
    return <ActivityLogsSkeleton />;
  }

  return (
    <main className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">

        {/* Header */}
        <div className="mb-10">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <div className="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-black tracking-tight sm:text-4xl">
                Activity Logs
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
                Consultez les actions métier et
                les activités techniques
                enregistrées sur KBR.
              </p>
            </div>

            {data && (
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-600">
                    Total
                  </p>

                  <p className="mt-1 text-xl font-black text-white">
                    {data.total}
                  </p>
                </div>

                <div className="rounded-xl border border-[#f5c400]/20 bg-[#f5c400]/5 px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#f5c400]/60">
                    Page
                  </p>

                  <p className="mt-1 text-xl font-black text-[#f5c400]">
                    {page}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <section className="mb-6 rounded-2xl border border-white/10 bg-white/[0.04] p-6">
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Filtres
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Rechercher dans les activités
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Filtrez les journaux par type,
              action, ressource, méthode HTTP ou
              ordre chronologique.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-5">

            {/* Activity type */}
            <div>
              <label
                htmlFor="activity-type"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Type
              </label>

              <select
                id="activity-type"
                value={activityType}
                onChange={(event) =>
                  handleActivityTypeChange(
                    event.target.value as
                      | ""
                      | ActivityType,
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              >
                {ACTIVITY_TYPE_OPTIONS.map(
                  (option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ),
                )}
              </select>
            </div>

            {/* Action */}
            <div>
              <label
                htmlFor="activity-action"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Action
              </label>

              <select
                id="activity-action"
                value={action}
                onChange={(event) =>
                  handleActionChange(
                    event.target.value,
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              >
                {ACTION_OPTIONS.map(
                  (option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ),
                )}
              </select>
            </div>

            {/* Resource */}
            <div>
              <label
                htmlFor="activity-resource"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Ressource
              </label>

              <select
                id="activity-resource"
                value={resourceType}
                onChange={(event) =>
                  handleResourceChange(
                    event.target.value,
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              >
                {RESOURCE_OPTIONS.map(
                  (option) => (
                    <option
                      key={option.value}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ),
                )}
              </select>
            </div>

            {/* Method */}
            <div>
              <label
                htmlFor="activity-method"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Méthode
              </label>

              <select
                id="activity-method"
                value={method}
                onChange={(event) =>
                  handleMethodChange(
                    event.target.value,
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              >
                <option value="">
                  Toutes les méthodes
                </option>

                <option value="GET">
                  GET
                </option>

                <option value="POST">
                  POST
                </option>

                <option value="PATCH">
                  PATCH
                </option>

                <option value="PUT">
                  PUT
                </option>

                <option value="DELETE">
                  DELETE
                </option>
              </select>
            </div>

            {/* Sort */}
            <div>
              <label
                htmlFor="activity-sort"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Tri
              </label>

              <select
                id="activity-sort"
                value={sortOrder}
                onChange={(event) =>
                  handleSortChange(
                    event.target.value as
                      | "asc"
                      | "desc",
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              >
                <option value="desc">
                  Plus récent
                </option>

                <option value="asc">
                  Plus ancien
                </option>
              </select>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-3 border-t border-white/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-600">
              {data
                ? `${data.total} activité${
                    data.total > 1
                      ? "s"
                      : ""
                  } enregistrée${
                    data.total > 1
                      ? "s"
                      : ""
                  }`
                : "Aucune donnée"}
            </p>

            <button
              type="button"
              onClick={resetFilters}
              className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:border-[#f5c400]/30 hover:bg-[#f5c400]/10 hover:text-white"
            >
              Réinitialiser les filtres
            </button>
          </div>
        </section>

        {/* Error */}
        {isError ? (
          <section className="rounded-2xl border border-red-500/20 bg-red-500/[0.06] p-8">
            <div className="mx-auto max-w-lg text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/10 text-xl font-black text-red-300">
                !
              </div>

              <h2 className="mt-4 text-xl font-black text-white">
                Impossible de charger les activités
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                Une erreur est survenue lors de
                la récupération des journaux
                d'activité.
              </p>

              {error instanceof Error && (
                <p className="mt-3 rounded-xl border border-white/10 bg-black/20 px-4 py-3 font-mono text-xs text-slate-500">
                  {error.message}
                </p>
              )}
            </div>
          </section>
        ) : !data ||
          data.items.length === 0 ? (
          /* Empty state */
          <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-12">
            <div className="mx-auto max-w-lg text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-xl text-slate-500">
                —
              </div>

              <h2 className="mt-4 text-xl font-black text-white">
                Aucune activité trouvée
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Aucun journal d'activité ne
                correspond aux filtres actuels.
              </p>
            </div>
          </section>
        ) : (
          <>
            {/* Activity table */}
            <section className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]">

              <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
                    Journal système
                  </p>

                  <h2 className="mt-1 text-lg font-black text-white">
                    Activités récentes
                  </h2>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-3 py-1.5 text-xs font-bold ${
                      activityType === "business"
                        ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                        : activityType === "technical"
                          ? "border border-blue-500/20 bg-blue-500/10 text-blue-300"
                          : "border border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]"
                    }`}
                  >
                    {activityType === "business"
                      ? "Audit métier"
                      : activityType === "technical"
                        ? "Activité technique"
                        : "Toutes les activités"}
                  </span>

                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-bold text-slate-400">
                    {data.total} total
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-white/10 bg-white/[0.02] text-left">
                      <th className="w-12 px-4 py-4" />

                      <th className="whitespace-nowrap px-4 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Date
                      </th>

                      <th className="whitespace-nowrap px-4 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Action
                      </th>

                      <th className="whitespace-nowrap px-4 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Ressource
                      </th>

                      <th className="whitespace-nowrap px-4 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Méthode
                      </th>

                      <th className="whitespace-nowrap px-4 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Endpoint
                      </th>

                      <th className="whitespace-nowrap px-4 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Utilisateur
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {data.items.map(
                      (activity) => {
                        const isExpanded =
                          expandedActivityId ===
                          activity.id;

                        return (
                          <>
                            <tr
                              key={activity.id}
                              className={`border-b border-white/5 transition ${
                                isExpanded
                                  ? "bg-white/[0.04]"
                                  : "hover:bg-white/[0.025]"
                              }`}
                            >
                              <td className="px-4 py-5">
                                <button
                                  type="button"
                                  aria-label={
                                    isExpanded
                                      ? "Masquer les détails"
                                      : "Afficher les détails"
                                  }
                                  onClick={() =>
                                    setExpandedActivityId(
                                      isExpanded
                                        ? null
                                        : activity.id,
                                    )
                                  }
                                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-sm text-slate-400 transition hover:border-[#f5c400]/30 hover:bg-[#f5c400]/10 hover:text-[#f5c400]"
                                >
                                  {isExpanded
                                    ? "−"
                                    : "+"}
                                </button>
                              </td>

                              <td className="whitespace-nowrap px-4 py-5 text-sm text-slate-400">
                                {formatDate(
                                  activity.occurred_at,
                                )}
                              </td>

                              <td className="px-4 py-5">
                                <div className="flex items-center gap-2">
                                  <span
                                    className={`h-1.5 w-1.5 shrink-0 rounded-full ${getActionDot(
                                      activity.action,
                                    )}`}
                                  />

                                  <span
                                    className={`inline-flex rounded-lg border px-2.5 py-1 text-xs font-bold ${getActionStyle(
                                      activity.action,
                                    )}`}
                                  >
                                    {formatAction(
                                      activity.action,
                                    )}
                                  </span>
                                </div>

                                {activity.details && (
                                  <p className="mt-2 max-w-xs truncate text-xs text-slate-600">
                                    {
                                      activity.details
                                    }
                                  </p>
                                )}
                              </td>

                              <td className="px-4 py-5">
                                <p className="text-sm font-bold text-slate-300">
                                  {formatResource(
                                    activity.resource_type,
                                  )}
                                </p>

                                {activity.resource_id && (
                                  <p className="mt-1 max-w-[180px] truncate font-mono text-[10px] text-slate-700">
                                    {
                                      activity.resource_id
                                    }
                                  </p>
                                )}
                              </td>

                              <td className="px-4 py-5">
                                {activity.method ? (
                                  <span className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 font-mono text-xs font-bold text-slate-300">
                                    {
                                      activity.method
                                    }
                                  </span>
                                ) : (
                                  <span className="text-slate-700">
                                    —
                                  </span>
                                )}
                              </td>

                              <td className="px-4 py-5 font-mono text-xs text-slate-400">
                                {activity.endpoint ?? (
                                  <span className="text-slate-700">
                                    —
                                  </span>
                                )}
                              </td>

                              <td className="px-4 py-5">
                                {activity.user_id ? (
                                  <span
                                    title={
                                      activity.user_id
                                    }
                                    className="font-mono text-xs text-slate-400"
                                  >
                                    {activity.user_id.slice(
                                      0,
                                      8,
                                    )}
                                    ...
                                  </span>
                                ) : (
                                  <span className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-xs font-bold text-slate-500">
                                    Système
                                  </span>
                                )}
                              </td>
                            </tr>

                            {isExpanded && (
                              <tr
                                key={`${activity.id}-details`}
                                className="border-b border-white/5"
                              >
                                <td
                                  colSpan={7}
                                  className="p-0"
                                >
                                  <ActivityDetails
                                    activity={
                                      activity
                                    }
                                  />
                                </td>
                              </tr>
                            )}
                          </>
                        );
                      },
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex flex-col gap-4 border-t border-white/10 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-slate-400">
                    Page{" "}
                    <span className="font-bold text-white">
                      {page}
                    </span>{" "}
                    sur{" "}
                    <span className="font-bold text-white">
                      {data.pages || 1}
                    </span>
                  </p>

                  <p className="mt-1 text-xs text-slate-600">
                    {data.total} activité
                    {data.total > 1
                      ? "s"
                      : ""}{" "}
                    au total
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => {
                      setPage(
                        (value) =>
                          Math.max(
                            1,
                            value - 1,
                          ),
                      );
                      setExpandedActivityId(
                        null,
                      );
                    }}
                    className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:border-white/20 hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    ← Précédent
                  </button>

                  <div className="flex h-10 min-w-10 items-center justify-center rounded-xl border border-[#f5c400]/20 bg-[#f5c400]/10 px-3 text-sm font-black text-[#f5c400]">
                    {page}
                  </div>

                  <button
                    type="button"
                    disabled={
                      page >= data.pages
                    }
                    onClick={() => {
                      setPage(
                        (value) =>
                          value + 1,
                      );
                      setExpandedActivityId(
                        null,
                      );
                    }}
                    className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:border-white/20 hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    Suivant →
                  </button>
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}