import { Link } from "react-router-dom";

import { useEvents } from "../../features/events/events.hooks";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(
    "fr-FR",
    {
      weekday: "short",
      day: "numeric",
      month: "long",
      year: "numeric",
    },
  );
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

export default function EventsPreview() {
  const {
    data,
    isLoading,
    isError,
  } = useEvents({
    upcoming: true,
    limit: 3,
  });

  const events = data?.items ?? [];

  return (
    <section className="bg-[#0B0B0B] py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F5C400]">
              Compétitions
            </p>

            <h2 className="mt-3 text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
              Prochains événements
            </h2>
          </div>

          <Link
            to="/events"
            className="font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
          >
            Voir tous les événements →
          </Link>
        </div>

        {isLoading && (
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="overflow-hidden rounded-2xl border border-white/10 bg-[#050505]"
              >
                <div className="h-48 animate-pulse bg-white/5" />

                <div className="space-y-4 p-6">
                  <div className="h-3 w-24 animate-pulse rounded bg-white/10" />

                  <div className="h-6 w-4/5 animate-pulse rounded bg-white/10" />

                  <div className="h-4 w-3/5 animate-pulse rounded bg-white/10" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="mt-12 rounded-2xl border border-red-500/20 bg-red-500/5 px-6 py-12 text-center">
            <p className="text-lg font-bold text-white">
              Impossible de charger les événements.
            </p>

            <p className="mx-auto mt-3 max-w-xl text-sm text-white/45">
              Les prochains événements KBR seront affichés ici
              dès qu'ils seront disponibles.
            </p>
          </div>
        )}

        {!isLoading && !isError && events.length === 0 && (
          <div className="mt-12 rounded-2xl border border-dashed border-white/15 bg-[#050505] px-6 py-16 text-center">
            <p className="text-lg font-bold text-white">
              Aucun événement à venir.
            </p>

            <p className="mx-auto mt-3 max-w-xl text-white/50">
              Les prochains événements KBR apparaîtront ici
              lorsqu'ils seront publiés.
            </p>
          </div>
        )}

        {!isLoading && !isError && events.length > 0 && (
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {events.map((event) => (
              <article
                key={event.id}
                className="group overflow-hidden rounded-2xl border border-white/10 bg-[#050505] transition hover:-translate-y-1 hover:border-[#F5C400]/30"
              >
                {event.cover_image ? (
                  <div className="h-48 overflow-hidden">
                    <img
                      src={event.cover_image}
                      alt={event.title}
                      className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                    />
                  </div>
                ) : (
                  <div className="flex h-48 items-center justify-center bg-gradient-to-br from-[#161616] to-[#090909]">
                    <span className="text-4xl font-black text-[#F5C400]/20">
                      KBR
                    </span>
                  </div>
                )}

                <div className="p-6">
                  <div className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#F5C400]">
                    <span>{formatDate(event.start_at)}</span>

                    <span className="text-white/20">
                      •
                    </span>

                    <span>
                      {formatTime(event.start_at)}
                    </span>
                  </div>

                  <h3 className="mt-3 line-clamp-2 text-xl font-black text-white transition group-hover:text-[#F5C400]">
                    {event.title}
                  </h3>

                  {event.location && (
                    <p className="mt-3 line-clamp-1 text-sm text-white/45">
                      📍 {event.location}
                    </p>
                  )}

                  {event.description && (
                    <p className="mt-3 line-clamp-2 text-sm leading-6 text-white/45">
                      {event.description}
                    </p>
                  )}

                  <Link
                    to={`/events/${event.id}`}
                    className="mt-5 inline-flex text-sm font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
                  >
                    Voir l'événement →
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}