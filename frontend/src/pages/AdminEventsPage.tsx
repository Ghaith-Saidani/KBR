import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  useDeleteEvent,
  useManageEvents,
  useUpdateEvent,
} from "../features/events/events.hooks";

import type {
  EventStatus,
} from "../features/events/events.types";

function formatDate(
  value: string,
) {
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

function formatTime(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleTimeString(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function statusLabel(
  status: EventStatus,
) {
  switch (status) {
    case "published":
      return "Publié";

    case "cancelled":
      return "Annulé";

    default:
      return "Brouillon";
  }
}

function statusClass(
  status: EventStatus,
) {
  switch (status) {
    case "published":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

    case "cancelled":
      return "border-red-500/20 bg-red-500/10 text-red-300";

    default:
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }
}

export default function AdminEventsPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const [
    filter,
    setFilter,
  ] = useState<
    "all" | "upcoming" | "past"
  >("all");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<
    "all" | EventStatus
  >("all");

  const [
    deletingId,
    setDeletingId,
  ] = useState<
    string | null
  >(null);

  const params = useMemo(
    () => ({
      search:
        search.trim() || undefined,

      upcoming:
        filter === "all"
          ? undefined
          : filter === "upcoming",
    }),
    [search, filter],
  );

  const {
    data,
    isLoading,
    isError,
  } = useManageEvents(params);

  const updateMutation =
    useUpdateEvent();

  const deleteMutation =
    useDeleteEvent();

  const events =
    data?.items.filter(
      (event) =>
        statusFilter === "all" ||
        event.status ===
          statusFilter,
    ) ?? [];

  function handleStatusChange(
    eventId: string,
    status: EventStatus,
  ) {
    updateMutation.mutate({
      eventId,
      data: {
        status,
      },
    });
  }

  function handleDelete(
    eventId: string,
    title: string,
  ) {
    const confirmed =
      window.confirm(
        `Supprimer définitivement « ${title} » ?`,
      );

    if (!confirmed) {
      return;
    }

    setDeletingId(eventId);

    deleteMutation.mutate(
      eventId,
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
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black sm:text-4xl">
              Gestion des événements
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Créez, modifiez, publiez et
              gérez les événements KBR.
            </p>
          </div>

          <Link
            to="/admin/events/new"
            className="inline-flex items-center justify-center rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            + Nouvel événement
          </Link>
        </div>

        <div className="mb-6 grid gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 lg:grid-cols-[1fr_auto_auto]">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Rechercher..."
            className="min-w-0 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <select
            value={filter}
            onChange={(event) =>
              setFilter(
                event.target.value as
                  | "all"
                  | "upcoming"
                  | "past",
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Toutes les dates
            </option>

            <option value="upcoming">
              À venir
            </option>

            <option value="past">
              Passés
            </option>
          </select>

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value as
                  | "all"
                  | EventStatus,
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Tous les statuts
            </option>

            <option value="draft">
              Brouillons
            </option>

            <option value="published">
              Publiés
            </option>

            <option value="cancelled">
              Annulés
            </option>
          </select>
        </div>

        {isLoading && (
          <div className="space-y-3">
            {Array.from({
              length: 5,
            }).map((_, index) => (
              <div
                key={index}
                className="h-24 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
              />
            ))}
          </div>
        )}

        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-lg font-bold text-white">
              Impossible de charger les
              événements
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Vérifiez votre session et
              réessayez.
            </p>
          </div>
        )}

        {!isLoading &&
          !isError &&
          events.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold">
                Aucun événement
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucun événement ne
                correspond aux filtres
                sélectionnés.
              </p>
            </div>
          )}

        {!isLoading &&
          !isError &&
          events.length > 0 && (
            <div className="space-y-3">
              {events.map((event) => (
                <article
                  key={event.id}
                  className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
                >
                  <div className="flex flex-col gap-5 p-5 lg:flex-row lg:items-center">
                    <div className="h-20 w-full shrink-0 overflow-hidden rounded-xl bg-[#0b0b0b] lg:w-28">
                      {event.cover_image ? (
                        <img
                          src={
                            event.cover_image
                          }
                          alt=""
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center">
                          <span className="font-black text-[#f5c400]/20">
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
                              event.status,
                            ),
                          ].join(" ")}
                        >
                          {statusLabel(
                            event.status,
                          )}
                        </span>

                        <span className="text-xs text-slate-500">
                          {formatDate(
                            event.start_at,
                          )}{" "}
                          ·{" "}
                          {formatTime(
                            event.start_at,
                          )}
                        </span>
                      </div>

                      <h2 className="mt-2 truncate text-lg font-bold text-white">
                        {event.title}
                      </h2>

                      <p className="mt-1 truncate text-sm text-slate-500">
                        {event.location ||
                          "Lieu non défini"}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {event.status !==
                        "published" && (
                        <button
                          type="button"
                          disabled={
                            updateMutation.isPending
                          }
                          onClick={() =>
                            handleStatusChange(
                              event.id,
                              "published",
                            )
                          }
                          className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs font-bold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                        >
                          Publier
                        </button>
                      )}

                      {event.status ===
                        "published" && (
                        <button
                          type="button"
                          disabled={
                            updateMutation.isPending
                          }
                          onClick={() =>
                            handleStatusChange(
                              event.id,
                              "draft",
                            )
                          }
                          className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs font-bold text-amber-300 transition hover:bg-amber-500/20 disabled:opacity-50"
                        >
                          Brouillon
                        </button>
                      )}

                      {event.status !==
                        "cancelled" && (
                        <button
                          type="button"
                          disabled={
                            updateMutation.isPending
                          }
                          onClick={() =>
                            handleStatusChange(
                              event.id,
                              "cancelled",
                            )
                          }
                          className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs font-bold text-red-300 transition hover:bg-red-500/20 disabled:opacity-50"
                        >
                          Annuler
                        </button>
                      )}

                      <Link
                        to={`/admin/events/${event.id}/edit`}
                        className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                      >
                        Modifier
                      </Link>

                      <button
                        type="button"
                        disabled={
                          deletingId ===
                          event.id
                        }
                        onClick={() =>
                          handleDelete(
                            event.id,
                            event.title,
                          )
                        }
                        className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-400 transition hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50"
                      >
                        {deletingId ===
                        event.id
                          ? "Suppression..."
                          : "Supprimer"}
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

        {data && (
          <div className="mt-5 text-xs text-slate-600">
            {events.length} événement
            {events.length !== 1
              ? "s"
              : ""}{" "}
            affiché
            {events.length !== 1
              ? "s"
              : ""}{" "}
            sur {data.total}
          </div>
        )}
      </div>
    </section>
  );
}