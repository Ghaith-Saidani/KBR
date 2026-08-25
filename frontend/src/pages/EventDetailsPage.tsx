import { Link, useParams } from "react-router-dom";

import { useEvent } from "../features/events/events.hooks";

function formatDate(value: string) {
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

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

export default function EventDetailsPage() {
  const { eventId } = useParams();

  const {
    data: event,
    isLoading,
    isError,
  } = useEvent(eventId);

  if (isLoading) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505]">
        <p className="text-sm text-slate-400">
          Chargement de l’événement...
        </p>
      </section>
    );
  }

  if (isError || !event) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505] px-6">
        <div className="text-center">
          <h1 className="text-3xl font-black text-white">
            Événement introuvable
          </h1>

          <p className="mt-3 text-slate-400">
            Cet événement n’existe pas ou n’est
            plus disponible.
          </p>

          <Link
            to="/events"
            className="mt-6 inline-block rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            Retour aux événements
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-[70vh] bg-[#050505]">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <Link
          to="/events"
          className="inline-flex items-center text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux événements
        </Link>

        <div className="mt-8 overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04]">
          {event.cover_image ? (
            <div className="h-[300px] overflow-hidden md:h-[450px]">
              <img
                src={event.cover_image}
                alt={event.title}
                className="h-full w-full object-cover"
              />
            </div>
          ) : (
            <div className="flex h-[300px] items-center justify-center bg-gradient-to-br from-[#151515] to-[#050505] md:h-[450px]">
              <span className="text-7xl font-black text-[#f5c400]/20">
                KBR
              </span>
            </div>
          )}

          <div className="p-6 md:p-10">
            <p className="text-sm font-bold uppercase tracking-[0.15em] text-[#f5c400]">
              {formatDate(event.start_at)}
            </p>

            <h1 className="mt-3 text-4xl font-black text-white md:text-5xl">
              {event.title}
            </h1>

            <div className="mt-5 flex flex-wrap gap-4 text-sm text-slate-400">
              <span>
                🕐 {formatTime(event.start_at)}
              </span>

              {event.location && (
                <span>
                  📍 {event.location}
                </span>
              )}
            </div>

            {event.description && (
              <div className="mt-8 max-w-4xl">
                <p className="whitespace-pre-line text-base leading-8 text-slate-300">
                  {event.description}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}