import { useState } from "react";

import {
  useCreateEvent,
  useDeleteEvent,
  useManageEvents,
  useUpdateEvent,
} from "../features/events/events.hooks";

import type {
  Event,
  EventCreateRequest,
  EventStatus,
  EventUpdateRequest,
} from "../features/events/events.types";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "short",
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

function statusLabel(
  status: EventStatus,
) {
  switch (status) {
    case "published":
      return "Publié";

    case "draft":
      return "Brouillon";

    case "cancelled":
      return "Annulé";

    default:
      return status;
  }
}

function statusClass(
  status: EventStatus,
) {
  switch (status) {
    case "published":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-400";

    case "draft":
      return "border-yellow-500/20 bg-yellow-500/10 text-yellow-400";

    case "cancelled":
      return "border-red-500/20 bg-red-500/10 text-red-400";

    default:
      return "border-white/10 bg-white/5 text-slate-400";
  }
}

const emptyForm: EventCreateRequest = {
  title: "",
  description: "",
  location: "",
  start_at: "",
  end_at: "",
  cover_image: "",
  status: "draft",
};

export default function EventManagementPage() {
  const [search, setSearch] = useState("");

  const [statusFilter, setStatusFilter] =
    useState<"all" | EventStatus>("all");

  const [isCreateOpen, setIsCreateOpen] =
    useState(false);

  const [editingEvent, setEditingEvent] =
    useState<Event | null>(null);

  const [deleteTarget, setDeleteTarget] =
    useState<Event | null>(null);

  const [form, setForm] =
    useState<EventCreateRequest>(
      emptyForm,
    );

  const eventsQuery = useManageEvents({
    search:
      search.trim() || undefined,
  });

  const createMutation =
    useCreateEvent();

  const updateMutation =
    useUpdateEvent();

  const deleteMutation =
    useDeleteEvent();

  const events =
    eventsQuery.data?.items ?? [];

  const filteredEvents =
    statusFilter === "all"
      ? events
      : events.filter(
          (event) =>
            event.status === statusFilter,
        );

  function openCreate() {
    setForm(emptyForm);
    setEditingEvent(null);
    setIsCreateOpen(true);
  }

  function openEdit(event: Event) {
    setEditingEvent(event);

    setForm({
      title: event.title,
      description:
        event.description ?? "",
      location:
        event.location ?? "",
      start_at: event.start_at.slice(
        0,
        16,
      ),
      end_at: event.end_at
        ? event.end_at.slice(0, 16)
        : "",
      cover_image:
        event.cover_image ?? "",
      status: event.status,
    });

    setIsCreateOpen(true);
  }

  function closeForm() {
    setIsCreateOpen(false);
    setEditingEvent(null);
    setForm(emptyForm);
  }

  function updateField(
    field: keyof EventCreateRequest,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSubmit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    if (!form.title.trim()) {
      return;
    }

    if (!form.start_at) {
      return;
    }

    if (editingEvent) {
      const data: EventUpdateRequest = {
        title: form.title.trim(),
        description:
          form.description?.trim() || null,
        location:
          form.location?.trim() || null,
        start_at: new Date(
          form.start_at,
        ).toISOString(),
        end_at: form.end_at
          ? new Date(
              form.end_at,
            ).toISOString()
          : null,
        cover_image:
          form.cover_image?.trim() || null,
        status:
          form.status,
      };

      await updateMutation.mutateAsync({
        eventId: editingEvent.id,
        data,
      });
    } else {
      await createMutation.mutateAsync({
        title: form.title.trim(),
        description:
          form.description?.trim() || null,
        location:
          form.location?.trim() || null,
        start_at: new Date(
          form.start_at,
        ).toISOString(),
        end_at: form.end_at
          ? new Date(
              form.end_at,
            ).toISOString()
          : null,
        cover_image:
          form.cover_image?.trim() || null,
        status:
          form.status,
      });
    }

    closeForm();
  }

  async function handleDelete() {
    if (!deleteTarget) {
      return;
    }

    await deleteMutation.mutateAsync(
      deleteTarget.id,
    );

    setDeleteTarget(null);
  }

  const isSaving =
    createMutation.isPending ||
    updateMutation.isPending;

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
              KBR Administration
            </p>

            <h1 className="mt-2 text-4xl font-black text-white">
              Gestion des événements
            </h1>

            <p className="mt-3 max-w-2xl text-slate-400">
              Créez, modifiez, publiez ou
              supprimez les événements KBR.
            </p>
          </div>

          <button
            type="button"
            onClick={openCreate}
            className="rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            + Nouvel événement
          </button>
        </div>

        <div className="mb-6 flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 md:flex-row">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Rechercher un événement..."
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target
                  .value as
                  | "all"
                  | EventStatus,
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

            <option value="cancelled">
              Annulés
            </option>
          </select>
        </div>

        {eventsQuery.isLoading && (
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-8 text-center text-slate-400">
            Chargement des événements...
          </div>
        )}

        {eventsQuery.isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="font-bold text-white">
              Impossible de charger les événements
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Vérifiez que votre compte possède
              les permissions staff ou admin.
            </p>
          </div>
        )}

        {!eventsQuery.isLoading &&
          !eventsQuery.isError &&
          filteredEvents.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold text-white">
                Aucun événement
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucun événement ne correspond
                aux filtres actuels.
              </p>
            </div>
          )}

        {!eventsQuery.isLoading &&
          !eventsQuery.isError &&
          filteredEvents.length > 0 && (
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px]">
                  <thead>
                    <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-slate-500">
                      <th className="px-6 py-4">
                        Événement
                      </th>

                      <th className="px-6 py-4">
                        Date
                      </th>

                      <th className="px-6 py-4">
                        Lieu
                      </th>

                      <th className="px-6 py-4">
                        Statut
                      </th>

                      <th className="px-6 py-4 text-right">
                        Actions
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredEvents.map(
                      (event) => (
                        <tr
                          key={event.id}
                          className="border-b border-white/5 last:border-0 hover:bg-white/[0.03]"
                        >
                          <td className="px-6 py-5">
                            <div className="flex items-center gap-4">
                              <div className="h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-[#0b0b0b]">
                                {event.cover_image ? (
                                  <img
                                    src={
                                      event.cover_image
                                    }
                                    alt=""
                                    className="h-full w-full object-cover"
                                  />
                                ) : (
                                  <div className="flex h-full items-center justify-center text-xs font-black text-[#f5c400]/30">
                                    KBR
                                  </div>
                                )}
                              </div>

                              <div>
                                <p className="font-bold text-white">
                                  {event.title}
                                </p>

                                <p className="mt-1 max-w-md truncate text-sm text-slate-500">
                                  {event.description ||
                                    "Aucune description"}
                                </p>
                              </div>
                            </div>
                          </td>

                          <td className="px-6 py-5">
                            <p className="text-sm font-semibold text-white">
                              {formatDate(
                                event.start_at,
                              )}
                            </p>

                            <p className="mt-1 text-xs text-slate-500">
                              {formatTime(
                                event.start_at,
                              )}
                            </p>
                          </td>

                          <td className="px-6 py-5 text-sm text-slate-400">
                            {event.location ||
                              "—"}
                          </td>

                          <td className="px-6 py-5">
                            <span
                              className={[
                                "inline-flex rounded-full border px-3 py-1 text-xs font-semibold",
                                statusClass(
                                  event.status,
                                ),
                              ].join(" ")}
                            >
                              {statusLabel(
                                event.status,
                              )}
                            </span>
                          </td>

                          <td className="px-6 py-5">
                            <div className="flex justify-end gap-2">
                              <button
                                type="button"
                                onClick={() =>
                                  openEdit(event)
                                }
                                className="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:border-[#f5c400]/40 hover:text-[#f5c400]"
                              >
                                Modifier
                              </button>

                              <button
                                type="button"
                                onClick={() =>
                                  setDeleteTarget(
                                    event,
                                  )
                                }
                                className="rounded-lg border border-red-500/20 px-3 py-2 text-xs font-semibold text-red-400 transition hover:bg-red-500/10"
                              >
                                Supprimer
                              </button>
                            </div>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
      </div>

      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4 py-8 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/10 bg-[#0b0b0b] shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
              <div>
                <h2 className="text-xl font-bold text-white">
                  {editingEvent
                    ? "Modifier l'événement"
                    : "Créer un événement"}
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Renseignez les informations
                  principales.
                </p>
              </div>

              <button
                type="button"
                onClick={closeForm}
                className="text-2xl text-slate-500 hover:text-white"
              >
                ×
              </button>
            </div>

            <form
              onSubmit={handleSubmit}
              className="space-y-5 p-6"
            >
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-300">
                  Titre
                </label>

                <input
                  required
                  value={form.title}
                  onChange={(event) =>
                    updateField(
                      "title",
                      event.target.value,
                    )
                  }
                  className="w-full rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-300">
                  Description
                </label>

                <textarea
                  rows={5}
                  value={
                    form.description ??
                    ""
                  }
                  onChange={(event) =>
                    updateField(
                      "description",
                      event.target.value,
                    )
                  }
                  className="w-full resize-none rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                />
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Date et heure de début
                  </label>

                  <input
                    required
                    type="datetime-local"
                    value={form.start_at}
                    onChange={(event) =>
                      updateField(
                        "start_at",
                        event.target.value,
                      )
                    }
                    className="w-full rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Date et heure de fin
                  </label>

                  <input
                    type="datetime-local"
                    value={
                      form.end_at ?? ""
                    }
                    onChange={(event) =>
                      updateField(
                        "end_at",
                        event.target.value,
                      )
                    }
                    className="w-full rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                  />
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Lieu
                  </label>

                  <input
                    value={
                      form.location ??
                      ""
                    }
                    onChange={(event) =>
                      updateField(
                        "location",
                        event.target.value,
                      )
                    }
                    className="w-full rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-300">
                    Statut
                  </label>

                  <select
                    value={
                      form.status ??
                      "draft"
                    }
                    onChange={(event) =>
                      updateField(
                        "status",
                        event.target.value,
                      )
                    }
                    className="w-full rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                  >
                    <option value="draft">
                      Brouillon
                    </option>

                    <option value="published">
                      Publié
                    </option>

                    <option value="cancelled">
                      Annulé
                    </option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-300">
                  URL de l'image
                </label>

                <input
                  type="url"
                  value={
                    form.cover_image ??
                    ""
                  }
                  onChange={(event) =>
                    updateField(
                      "cover_image",
                      event.target.value,
                    )
                  }
                  placeholder="https://..."
                  className="w-full rounded-xl border border-white/10 bg-[#050505] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
                />
              </div>

              <div className="flex justify-end gap-3 border-t border-white/10 pt-5">
                <button
                  type="button"
                  onClick={closeForm}
                  className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-slate-400 hover:text-white"
                >
                  Annuler
                </button>

                <button
                  type="submit"
                  disabled={isSaving}
                  className="rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSaving
                    ? "Enregistrement..."
                    : editingEvent
                      ? "Enregistrer"
                      : "Créer l'événement"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#0b0b0b] p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-white">
              Supprimer l'événement ?
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Vous êtes sur le point de supprimer
              définitivement :
            </p>

            <p className="mt-2 font-semibold text-white">
              {deleteTarget.title}
            </p>

            <p className="mt-3 text-xs text-red-400">
              Cette action est irréversible.
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() =>
                  setDeleteTarget(null)
                }
                className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-slate-400 hover:text-white"
              >
                Annuler
              </button>

              <button
                type="button"
                onClick={handleDelete}
                disabled={
                  deleteMutation.isPending
                }
                className="rounded-xl bg-red-500 px-5 py-3 text-sm font-bold text-white transition hover:bg-red-400 disabled:opacity-50"
              >
                {deleteMutation.isPending
                  ? "Suppression..."
                  : "Supprimer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}