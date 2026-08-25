import { useState } from "react";
import { Link } from "react-router-dom";

import { useEvents } from "../features/events/events.hooks";

function formatEventDate(value: string) {
  return new Date(value).toLocaleDateString(
    "fr-FR",
    {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    },
  );
}

function formatEventTime(value: string) {
  return new Date(value).toLocaleTimeString(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

export default function EventsPage() {
  const [search, setSearch] = useState("");

  const [filter, setFilter] = useState<
    "upcoming" | "past"
  >("upcoming");

  const {
    data,
    isLoading,
    isError,
  } = useEvents({
    search:
      search.trim() || undefined,
    upcoming:
      filter === "upcoming",
  });

  return (
    <section className="min-h-[70vh] bg-[#050505] px-6 py-16">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
            KBR
          </p>

          <h1 className="mt-3 text-4xl font-black text-white sm:text-5xl">
            Événements
          </h1>

          <p className="mt-4 max-w-2xl text-slate-400">
            Découvrez les prochains événements,
            rencontres et activités de la
            communauté KBR.
          </p>
        </div>

        <div className="mb-8 flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 md:flex-row">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Rechercher un événement..."
            aria-label="Rechercher un événement"
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <div className="flex rounded-xl border border-white/10 bg-[#0b0b0b] p-1">
            <button
              type="button"
              onClick={() =>
                setFilter("upcoming")
              }
              className={[
                "rounded-lg px-4 py-2 text-sm font-semibold transition",
                filter === "upcoming"
                  ? "bg-[#f5c400] text-black"
                  : "text-slate-400 hover:text-white",
              ].join(" ")}
            >
              À venir
            </button>

            <button
              type="button"
              onClick={() =>
                setFilter("past")
              }
              className={[
                "rounded-lg px-4 py-2 text-sm font-semibold transition",
                filter === "past"
                  ? "bg-[#f5c400] text-black"
                  : "text-slate-400 hover:text-white",
              ].join(" ")}
            >
              Passés
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({
              length: 6,
            }).map((_, index) => (
              <div
                key={index}
                className="animate-pulse overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
              >
                <div className="h-52 bg-white/5" />

                <div className="space-y-3 p-6">
                  <div className="h-5 w-3/4 rounded bg-white/5" />
                  <div className="h-4 w-1/2 rounded bg-white/5" />
                  <div className="h-4 w-full rounded bg-white/5" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-xl font-bold text-white">
              Impossible de charger les événements
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Une erreur est survenue lors du
              chargement des événements.
            </p>
          </div>
        )}

        {!isLoading &&
          !isError &&
          data?.items.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold text-white">
                Aucun événement trouvé
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucun événement ne correspond à
                votre recherche.
              </p>
            </div>
          )}

        {!isLoading &&
          !isError &&
          data &&
          data.items.length > 0 && (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data.items.map((event) => (
                <Link
                  key={event.id}
                  to={`/events/${event.id}`}
                  className="group overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:-translate-y-1 hover:border-[#f5c400]/40 hover:bg-white/[0.06]"
                >
                  <div className="relative h-52 overflow-hidden bg-[#0b0b0b]">
                    {event.cover_image ? (
                      <img
                        src={event.cover_image}
                        alt={event.title}
                        className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center bg-gradient-to-br from-[#151515] to-[#050505]">
                        <span className="text-5xl font-black text-[#f5c400]/20">
                          KBR
                        </span>
                      </div>
                    )}

                    <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 to-transparent" />
                  </div>

                  <div className="p-6">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#f5c400]">
                      {formatEventDate(
                        event.start_at,
                      )}
                    </p>

                    <h2 className="mt-2 line-clamp-2 text-xl font-bold text-white">
                      {event.title}
                    </h2>

                    <p className="mt-2 text-sm font-medium text-slate-500">
                      {formatEventTime(
                        event.start_at,
                      )}
                      {event.location
                        ? ` · ${event.location}`
                        : ""}
                    </p>

                    {event.description && (
                      <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-400">
                        {event.description}
                      </p>
                    )}

                    <div className="mt-6 text-sm font-bold text-[#f5c400]">
                      Voir l’événement →
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
      </div>
    </section>
  );
}