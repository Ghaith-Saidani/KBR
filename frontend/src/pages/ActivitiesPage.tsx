import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useActivities,
} from "../features/activities/activities.hooks";

function formatDate(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleDateString(
    "fr-FR",
    {
      weekday: "long",
      day: "numeric",
      month: "long",
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

export default function ActivitiesPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const {
    data,
    isLoading,
    isError,
  } = useActivities({
    search:
      search.trim() ||
      undefined,
  });

  return (
    <section className="min-h-[70vh] bg-[#050505] px-6 py-16">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
            KBR
          </p>

          <h1 className="mt-3 text-4xl font-black text-white sm:text-5xl">
            Activités
          </h1>

          <p className="mt-4 max-w-2xl text-slate-400">
            Découvrez les projets,
            initiatives et activités
            portés par la communauté KBR.
          </p>
        </div>

        <div className="mb-8 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Rechercher une activité..."
            aria-label="Rechercher une activité"
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />
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
                  <div className="h-4 w-1/3 rounded bg-white/5" />
                  <div className="h-6 w-3/4 rounded bg-white/5" />
                  <div className="h-4 w-full rounded bg-white/5" />
                  <div className="h-4 w-5/6 rounded bg-white/5" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-xl font-bold text-white">
              Impossible de charger les activités
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Une erreur est survenue lors
              du chargement des activités.
            </p>
          </div>
        )}

        {!isLoading &&
          !isError &&
          data?.items.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold text-white">
                Aucune activité trouvée
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucune activité ne correspond
                à votre recherche.
              </p>
            </div>
          )}

        {!isLoading &&
          !isError &&
          data &&
          data.items.length > 0 && (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data.items.map(
                (activity) => (
                  <Link
                    key={activity.id}
                    to={`/activities/${activity.slug}`}
                    className="group overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:-translate-y-1 hover:border-[#f5c400]/40 hover:bg-white/[0.06]"
                  >
                    <div className="relative h-52 overflow-hidden bg-[#0b0b0b]">
                      {activity.cover_image ? (
                        <img
                          src={
                            activity.cover_image
                          }
                          alt={
                            activity.title
                          }
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
                      {activity.start_at && (
                        <div className="text-xs font-semibold uppercase tracking-wider text-[#f5c400]">
                          {formatDate(
                            activity.start_at,
                          )}
                        </div>
                      )}

                      <h2 className="mt-2 line-clamp-2 text-xl font-bold text-white">
                        {activity.title}
                      </h2>

                      {(activity.start_at ||
                        activity.location) && (
                        <p className="mt-2 text-sm font-medium text-slate-500">
                          {activity.start_at &&
                            formatTime(
                              activity.start_at,
                            )}

                          {activity.location &&
                            ` · ${activity.location}`}
                        </p>
                      )}

                      {activity.excerpt && (
                        <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-400">
                          {
                            activity.excerpt
                          }
                        </p>
                      )}

                      <div className="mt-6 text-sm font-bold text-[#f5c400]">
                        Découvrir l'activité →
                      </div>
                    </div>
                  </Link>
                ),
              )}
            </div>
          )}
      </div>
    </section>
  );
}