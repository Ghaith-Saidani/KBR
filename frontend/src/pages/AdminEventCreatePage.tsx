import {
  Link,
  useNavigate,
} from "react-router-dom";

import EventForm from "../components/forms/EventForm";

import {
  useCreateEvent,
} from "../features/events/events.hooks";

import type {
  EventCreateRequest,
} from "../features/events/events.types";

export default function AdminEventCreatePage() {
  const navigate =
    useNavigate();

  const mutation =
    useCreateEvent();

  function handleSubmit(
    data: EventCreateRequest,
  ) {
    mutation.mutate(
      data,
      {
        onSuccess: (
          createdEvent,
        ) => {
          navigate(
            `/admin/events/${createdEvent.id}/edit`,
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
            Créer un événement
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Ajoutez un nouvel événement à
            la communauté KBR.
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <EventForm
            mode="create"
            submitLabel="Créer l'événement"
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

          {mutation.isError && (
            <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
              <p className="text-sm font-semibold text-red-200">
                Impossible de créer
                l'événement.
              </p>

              <p className="mt-1 text-sm text-red-200/70">
                Une erreur est survenue.
                Vérifiez les informations
                puis réessayez.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}