import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import EventForm from "../components/forms/EventForm";

import {
  useEvent,
  useUpdateEvent,
} from "../features/events/events.hooks";

import type {
  EventUpdateRequest,
} from "../features/events/events.types";

export default function AdminEventEditPage() {
  const {
    eventId,
  } = useParams();

  const navigate =
    useNavigate();

  const {
    data: event,
    isLoading,
    isError,
  } = useEvent(eventId);

  const mutation =
    useUpdateEvent();

  if (isLoading) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] text-slate-400">
        Chargement de l'événement...
      </section>
    );
  }

  if (isError || !event) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="text-center">
          <h1 className="text-2xl font-black">
            Événement introuvable
          </h1>

          <Link
            to="/admin/events"
            className="mt-5 inline-block text-sm font-bold text-[#f5c400]"
          >
            ← Retour aux événements
          </Link>
        </div>
      </section>
    );
  }

  const currentEventId =
    event.id;

  function handleSubmit(
    data: EventUpdateRequest,
  ) {
    mutation.mutate(
      {
        eventId: currentEventId,
        data,
      },
      {
        onSuccess: () => {
          navigate(
            "/admin/events",
          );
        },
      },
    );
  }

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-4xl">
        <Link
          to="/admin/events"
          className="text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux événements
        </Link>

        <div className="mb-8 mt-6">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <h1 className="mt-2 text-3xl font-black">
            Modifier l'événement
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Modifiez les informations de :
            <span className="ml-1 font-semibold text-white">
              {event.title}
            </span>
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <EventForm
            mode="edit"
            initialValues={{
              title: event.title,
              description:
                event.description ?? "",
              location:
                event.location ?? "",
              start_at:
                event.start_at,
              end_at:
                event.end_at ?? "",
              cover_image:
                event.cover_image ?? "",
              status:
                event.status,
            }}
            isSubmitting={
              mutation.isPending
            }
            onSubmit={handleSubmit}
            onCancel={() =>
              navigate(
                "/admin/events",
              )
            }
          />
        </div>
      </div>
    </section>
  );
}