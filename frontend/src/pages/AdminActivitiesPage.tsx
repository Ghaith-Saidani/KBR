import {
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  useDeleteActivity,
  useManageActivities,
  useUpdateActivity,
} from "../features/activities/activities.hooks";

import type {
  Activity,
  ActivityStatus,
} from "../features/activities/activities.types";


function formatDate(
  value: string | null,
) {
  if (!value) {
    return "—";
  }

  return new Date(
    value,
  ).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  );
}


function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return "—";
  }

  return new Date(
    value,
  ).toLocaleString(
    "fr-FR",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


function statusLabel(
  status: ActivityStatus,
) {
  return status === "published"
    ? "Publié"
    : "Brouillon";
}


function statusClass(
  status: ActivityStatus,
) {
  return status === "published"
    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
    : "border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]";
}


function ActivitySkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <div className="flex flex-col gap-5 lg:flex-row">
        <div className="h-28 w-full rounded-xl bg-white/5 lg:w-48" />

        <div className="flex-1 space-y-3">
          <div className="h-4 w-24 rounded bg-white/5" />
          <div className="h-6 w-2/3 rounded bg-white/5" />
          <div className="h-4 w-1/2 rounded bg-white/5" />
          <div className="h-4 w-full rounded bg-white/5" />
        </div>
      </div>
    </div>
  );
}


export default function AdminActivitiesPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<
    "all" | ActivityStatus
  >("all");

  const [
    deletingId,
    setDeletingId,
  ] = useState<string | null>(
    null,
  );

  const params = useMemo(
    () => ({
      search:
        search.trim() ||
        undefined,
      skip: 0,
      limit: 100,
    }),
    [search],
  );

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useManageActivities(
    params,
  );

  const updateMutation =
    useUpdateActivity();

  const deleteMutation =
    useDeleteActivity();

  const activities =
    (data?.items ?? []).filter(
      (activity) =>
        statusFilter === "all" ||
        activity.status ===
          statusFilter,
    );


  function handleToggleStatus(
    activity: Activity,
  ) {
    const nextStatus: ActivityStatus =
      activity.status === "published"
        ? "draft"
        : "published";

    updateMutation.mutate({
      activityId: activity.id,
      data: {
        status: nextStatus,
      },
    });
  }


  function handleDelete(
    activity: Activity,
  ) {
    const confirmed =
      window.confirm(
        `Supprimer définitivement l'activité "${activity.title}" ?`,
      );

    if (!confirmed) {
      return;
    }

    setDeletingId(
      activity.id,
    );

    deleteMutation.mutate(
      activity.id,
      {
        onSettled: () => {
          setDeletingId(null);
        },
      },
    );
  }


  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">

        <div className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              Activités
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Créez, modifiez et gérez les
              activités et projets de KBR.
            </p>
          </div>

          <Link
            to="/admin/activities/create"
            className="inline-flex items-center justify-center rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-black text-black transition hover:bg-[#ffd21a]"
          >
            + Nouvelle activité
          </Link>
        </div>


        <div className="mb-6 grid gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 lg:grid-cols-[1fr_auto]">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Rechercher une activité..."
            className="min-w-0 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value as
                  | "all"
                  | ActivityStatus,
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Tous les statuts
            </option>

            <option value="published">
              Publiés
            </option>

            <option value="draft">
              Brouillons
            </option>
          </select>
        </div>


        {isLoading && (
          <div className="space-y-3">
            {Array.from({
              length: 5,
            }).map((_, index) => (
              <ActivitySkeleton
                key={index}
              />
            ))}
          </div>
        )}


        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-xl font-bold text-white">
              Impossible de charger les activités
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Vérifiez votre session
              administrateur et réessayez.
            </p>

            <button
              type="button"
              onClick={() =>
                refetch()
              }
              className="mt-5 rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-black text-black transition hover:bg-[#ffd21a]"
            >
              Réessayer
            </button>
          </div>
        )}


        {!isLoading &&
          !isError &&
          activities.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-2xl">
                ◆
              </div>

              <h2 className="mt-5 text-xl font-bold">
                Aucune activité
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucune activité ne correspond
                aux filtres sélectionnés.
              </p>
            </div>
          )}


        {!isLoading &&
          !isError &&
          activities.length > 0 && (
            <div className="space-y-3">
              {activities.map(
                (activity) => (
                  <article
                    key={activity.id}
                    className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:border-white/20"
                  >
                    <div className="flex flex-col gap-5 p-5 lg:flex-row">

                      <div className="h-48 shrink-0 overflow-hidden rounded-xl bg-[#0b0b0b] lg:h-28 lg:w-48">
                        {activity.cover_image ? (
                          <img
                            src={
                              activity.cover_image
                            }
                            alt={
                              activity.title
                            }
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center bg-gradient-to-br from-[#151515] to-[#050505]">
                            <span className="text-3xl font-black text-[#f5c400]/20">
                              KBR
                            </span>
                          </div>
                        )}
                      </div>


                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={[
                              "rounded-full border px-2.5 py-1 text-xs font-bold",
                              statusClass(
                                activity.status,
                              ),
                            ].join(" ")}
                          >
                            {statusLabel(
                              activity.status,
                            )}
                          </span>

                          <span className="text-xs text-slate-600">
                            Créée le{" "}
                            {formatDate(
                              activity.created_at,
                            )}
                          </span>
                        </div>

                        <h2 className="mt-3 truncate text-xl font-bold text-white">
                          {activity.title}
                        </h2>

                        {activity.excerpt && (
                          <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
                            {
                              activity.excerpt
                            }
                          </p>
                        )}

                        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
                          {activity.start_at && (
                            <span>
                              Début :{" "}
                              {formatDateTime(
                                activity.start_at,
                              )}
                            </span>
                          )}

                          {activity.location && (
                            <span>
                              Lieu :{" "}
                              {
                                activity.location
                              }
                            </span>
                          )}
                        </div>
                      </div>


                      <div className="flex shrink-0 flex-wrap items-center gap-2 lg:w-56 lg:justify-end">

                        {activity.status ===
                          "published" && (
                          <Link
                            to={`/activities/${activity.slug}`}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                          >
                            Voir
                          </Link>
                        )}

                        <Link
                          to={`/admin/activities/${activity.id}/edit`}
                          className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                        >
                          Modifier
                        </Link>

                        <button
                          type="button"
                          disabled={
                            updateMutation.isPending
                          }
                          onClick={() =>
                            handleToggleStatus(
                              activity,
                            )
                          }
                          className="rounded-lg border border-[#f5c400]/20 bg-[#f5c400]/10 px-3 py-2 text-xs font-bold text-[#f5c400] transition hover:bg-[#f5c400]/20 disabled:opacity-50"
                        >
                          {activity.status ===
                          "published"
                            ? "Dépublier"
                            : "Publier"}
                        </button>

                        <button
                          type="button"
                          disabled={
                            deletingId ===
                            activity.id
                          }
                          onClick={() =>
                            handleDelete(
                              activity,
                            )
                          }
                          className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-400 transition hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50"
                        >
                          {deletingId ===
                          activity.id
                            ? "Suppression..."
                            : "Supprimer"}
                        </button>

                      </div>
                    </div>
                  </article>
                ),
              )}
            </div>
          )}


        {data && (
          <div className="mt-5 flex flex-wrap justify-between gap-3 text-xs text-slate-600">
            <span>
              {activities.length} activité
              {activities.length !== 1
                ? "s"
                : ""}{" "}
              affichée
              {activities.length !== 1
                ? "s"
                : ""}{" "}
              sur {data.total}
            </span>

            <span>
              Limite : {data.limit}
            </span>
          </div>
        )}

      </div>
    </section>
  );
}