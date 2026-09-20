import {
  useMemo,
  useState,
} from "react";

import {
  useAdminActivityLogs,
} from "../features/admin/adminActivity.hooks";

const PAGE_SIZE = 20;

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
  return action
    .toLowerCase()
    .replaceAll("_", " ");
}

function getActionStyle(
  action: string,
) {
  const normalized = action.toUpperCase();

  if (
    normalized.includes("DELETE") ||
    normalized.includes("REMOVE") ||
    normalized.includes("FAIL")
  ) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  if (
    normalized.includes("CREATE") ||
    normalized.includes("REGISTER") ||
    normalized.includes("LOGIN")
  ) {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }

  if (
    normalized.includes("UPDATE") ||
    normalized.includes("EDIT")
  ) {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  return "border-white/10 bg-white/[0.05] text-slate-300";
}

function ActivityLogsSkeleton() {
  return (
    <main className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-4 w-32 rounded bg-white/10" />

        <div className="mt-3 h-10 w-72 rounded bg-white/10" />

        <div className="mt-3 h-5 w-full max-w-2xl rounded bg-white/10" />

        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.04] p-6">
          <div className="grid gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map(
              (_, index) => (
                <div
                  key={`filter-skeleton-${index}`}
                  className="h-20 rounded-xl bg-white/5"
                />
              ),
            )}
          </div>
        </div>

        <div className="mt-6 h-96 rounded-2xl border border-white/10 bg-white/[0.04]" />
      </div>
    </main>
  );
}

export default function AdminActivityLogsPage() {
  const [
    page,
    setPage,
  ] = useState(1);

  const [
    action,
    setAction,
  ] = useState("");

  const [
    method,
    setMethod,
  ] = useState("");

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

  const filters = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
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
    setAction("");
    setMethod("");
    setResourceType("");
    setSortOrder("desc");
    setPage(1);
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

          <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
            Activity Logs
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Consultez et analysez les activités
            des utilisateurs et les actions
            administratives effectuées sur KBR.
          </p>
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
              Filtrez les événements par action,
              ressource ou méthode HTTP.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">

            {/* Action */}
            <div>
              <label
                htmlFor="activity-action"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Action
              </label>

              <input
                id="activity-action"
                value={action}
                onChange={(event) => {
                  setAction(
                    event.target.value,
                  );
                  setPage(1);
                }}
                placeholder="LOGIN"
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              />
            </div>

            {/* Resource */}
            <div>
              <label
                htmlFor="activity-resource"
                className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-400"
              >
                Ressource
              </label>

              <input
                id="activity-resource"
                value={resourceType}
                onChange={(event) => {
                  setResourceType(
                    event.target.value,
                  );
                  setPage(1);
                }}
                placeholder="member"
                className="w-full rounded-xl border border-white/10 bg-[#090909] px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none transition focus:border-[#f5c400]/50 focus:ring-1 focus:ring-[#f5c400]/20"
              />
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
                onChange={(event) => {
                  setMethod(
                    event.target.value,
                  );
                  setPage(1);
                }}
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
                onChange={(event) => {
                  setSortOrder(
                    event.target.value as
                      | "asc"
                      | "desc",
                  );

                  setPage(1);
                }}
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

          <div className="mt-5 flex items-center justify-between border-t border-white/10 pt-5">
            <p className="text-xs text-slate-600">
              {data
                ? `${data.total} activité${data.total > 1 ? "s" : ""} enregistrée${data.total > 1 ? "s" : ""}`
                : "Aucune donnée"}
            </p>

            <button
              type="button"
              onClick={resetFilters}
              className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:border-[#f5c400]/30 hover:bg-[#f5c400]/10 hover:text-white"
            >
              Réinitialiser
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

              <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
                    Journal système
                  </p>

                  <h2 className="mt-1 text-lg font-black text-white">
                    Activités récentes
                  </h2>
                </div>

                <div className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-bold text-slate-400">
                  {data.total} total
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-white/10 bg-white/[0.02] text-left">
                      <th className="whitespace-nowrap px-6 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Date
                      </th>

                      <th className="whitespace-nowrap px-6 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Action
                      </th>

                      <th className="whitespace-nowrap px-6 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Ressource
                      </th>

                      <th className="whitespace-nowrap px-6 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Méthode
                      </th>

                      <th className="whitespace-nowrap px-6 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Endpoint
                      </th>

                      <th className="whitespace-nowrap px-6 py-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
                        Utilisateur
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {data.items.map(
                      (activity) => (
                        <tr
                          key={activity.id}
                          className="border-b border-white/5 transition last:border-b-0 hover:bg-white/[0.025]"
                        >
                          <td className="whitespace-nowrap px-6 py-5 text-sm text-slate-400">
                            {formatDate(
                              activity.occurred_at,
                            )}
                          </td>

                          <td className="px-6 py-5">
                            <span
                              className={`inline-flex rounded-lg border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${getActionStyle(
                                activity.action,
                              )}`}
                            >
                              {formatAction(
                                activity.action,
                              )}
                            </span>

                            {activity.details && (
                              <p className="mt-2 max-w-xs truncate text-xs text-slate-600">
                                {
                                  activity.details
                                }
                              </p>
                            )}
                          </td>

                          <td className="px-6 py-5 text-sm text-slate-300">
                            {activity.resource_type ?? (
                              <span className="text-slate-700">
                                —
                              </span>
                            )}
                          </td>

                          <td className="px-6 py-5">
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

                          <td className="px-6 py-5 font-mono text-xs text-slate-400">
                            {activity.endpoint ?? (
                              <span className="text-slate-700">
                                —
                              </span>
                            )}
                          </td>

                          <td className="px-6 py-5">
                            {activity.user_id ? (
                              <span className="font-mono text-xs text-slate-400">
                                {activity.user_id.slice(
                                  0,
                                  8,
                                )}
                                ...
                              </span>
                            ) : (
                              <span className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-xs font-bold text-slate-500">
                                System
                              </span>
                            )}
                          </td>
                        </tr>
                      ),
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
                    onClick={() =>
                      setPage(
                        (value) =>
                          Math.max(
                            1,
                            value - 1,
                          ),
                      )
                    }
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
                    onClick={() =>
                      setPage(
                        (value) =>
                          value + 1,
                      )
                    }
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