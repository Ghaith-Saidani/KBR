import {
  Link,
  useParams,
} from "react-router-dom";

import {
  useActivityBySlug,
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

export default function ActivityDetailsPage() {
  const {
    slug,
  } = useParams();

  const {
    data: activity,
    isLoading,
    isError,
  } =
    useActivityBySlug(slug);

  if (isLoading) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505]">
        <p className="text-sm text-slate-400">
          Chargement de l'activité...
        </p>
      </section>
    );
  }

  if (isError || !activity) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505] px-6">
        <div className="text-center">
          <h1 className="text-3xl font-black text-white">
            Activité introuvable
          </h1>

          <p className="mt-3 text-slate-400">
            Cette activité n'existe pas ou
            n'est plus disponible.
          </p>

          <Link
            to="/activities"
            className="mt-6 inline-block rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            Retour aux activités
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-[70vh] bg-[#050505]">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <Link
          to="/activities"
          className="inline-flex items-center text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux activités
        </Link>

        {activity.cover_image && (
          <div className="mt-8 overflow-hidden rounded-2xl border border-white/10">
            <img
              src={activity.cover_image}
              alt={activity.title}
              className="max-h-[520px] w-full object-cover"
            />
          </div>
        )}

        <div className="mt-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
            Activité KBR
          </p>

          <h1 className="mt-3 text-4xl font-black tracking-tight text-white sm:text-5xl">
            {activity.title}
          </h1>

          {(activity.start_at ||
            activity.location) && (
            <div className="mt-5 flex flex-wrap gap-3 text-sm text-slate-400">
              {activity.start_at && (
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2">
                  {formatDate(
                    activity.start_at,
                  )}

                  {" · "}

                  {formatTime(
                    activity.start_at,
                  )}
                </span>
              )}

              {activity.end_at && (
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2">
                  Jusqu'à{" "}
                  {formatDate(
                    activity.end_at,
                  )}{" "}
                  à{" "}
                  {formatTime(
                    activity.end_at,
                  )}
                </span>
              )}

              {activity.location && (
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2">
                  {activity.location}
                </span>
              )}
            </div>
          )}

          {activity.excerpt && (
            <p className="mt-8 text-lg leading-8 text-slate-400">
              {activity.excerpt}
            </p>
          )}

          <div className="mt-8 border-t border-white/10 pt-8">
            <p className="whitespace-pre-line text-base leading-8 text-slate-300">
              {activity.description}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}