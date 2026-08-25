import type {
  EventCreateRequest,
  EventStatus,
  EventUpdateRequest,
} from "../../features/events/events.types";

interface BaseEventFormProps {
  initialValues?: {
    title?: string;
    description?: string | null;
    location?: string | null;
    start_at?: string;
    end_at?: string | null;
    cover_image?: string | null;
    status?: EventStatus;
  };
  submitLabel?: string;
  isSubmitting?: boolean;
  onCancel?: () => void;
}

interface CreateEventFormProps
  extends BaseEventFormProps {
  mode?: "create";
  onSubmit: (
    data: EventCreateRequest,
  ) => void;
}

interface EditEventFormProps
  extends BaseEventFormProps {
  mode: "edit";
  onSubmit: (
    data: EventUpdateRequest,
  ) => void;
}

export type EventFormProps =
  | CreateEventFormProps
  | EditEventFormProps;

export default function EventForm({
  mode = "create",
  initialValues,
  submitLabel = "Enregistrer",
  isSubmitting = false,
  onSubmit,
  onCancel,
}: EventFormProps) {
  const values = {
    title: initialValues?.title ?? "",
    description:
      initialValues?.description ?? "",
    location:
      initialValues?.location ?? "",
    start_at:
      initialValues?.start_at ?? "",
    end_at:
      initialValues?.end_at ?? "",
    cover_image:
      initialValues?.cover_image ?? "",
    status:
      initialValues?.status ?? "draft",
  };

  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const formData = new FormData(
      event.currentTarget,
    );

    const title = String(
      formData.get("title") ?? "",
    ).trim();

    const description = String(
      formData.get("description") ?? "",
    ).trim();

    const location = String(
      formData.get("location") ?? "",
    ).trim();

    const startAt = String(
      formData.get("start_at") ?? "",
    );

    const endAt = String(
      formData.get("end_at") ?? "",
    );

    const coverImage = String(
      formData.get("cover_image") ?? "",
    ).trim();

    const status = String(
      formData.get("status") ?? "draft",
    ) as EventStatus;

    if (!title || !startAt) {
      return;
    }

    const data = {
      title,
      description: description || null,
      location: location || null,
      start_at: startAt,
      end_at: endAt || null,
      cover_image: coverImage || null,
      status,
    };

    if (mode === "edit") {
      onSubmit(data);
      return;
    }

    onSubmit(data);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6"
    >
      <div>
        <label
          htmlFor="title"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Titre
        </label>

        <input
          id="title"
          name="title"
          type="text"
          required
          defaultValue={values.title}
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="Nom de l'événement"
        />
      </div>

      <div>
        <label
          htmlFor="description"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Description
        </label>

        <textarea
          id="description"
          name="description"
          rows={5}
          defaultValue={
            values.description ?? ""
          }
          className="w-full resize-y rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="Description de l'événement"
        />
      </div>

      <div>
        <label
          htmlFor="location"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Lieu
        </label>

        <input
          id="location"
          name="location"
          type="text"
          defaultValue={values.location ?? ""}
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="Bizerte, Tunisie"
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label
            htmlFor="start_at"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Début
          </label>

          <input
            id="start_at"
            name="start_at"
            type="datetime-local"
            required
            defaultValue={
              values.start_at
                ? values.start_at.slice(0, 16)
                : ""
            }
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          />
        </div>

        <div>
          <label
            htmlFor="end_at"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Fin
          </label>

          <input
            id="end_at"
            name="end_at"
            type="datetime-local"
            defaultValue={
              values.end_at
                ? values.end_at.slice(0, 16)
                : ""
            }
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          />
        </div>
      </div>

      <div>
        <label
          htmlFor="cover_image"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Image de couverture
        </label>

        <input
          id="cover_image"
          name="cover_image"
          type="url"
          defaultValue={
            values.cover_image ?? ""
          }
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="https://..."
        />
      </div>

      <div>
        <label
          htmlFor="status"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Statut
        </label>

        <select
          id="status"
          name="status"
          defaultValue={values.status}
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
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

      <div className="flex flex-col-reverse gap-3 sm:flex-row">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-6 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/[0.08] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Annuler
          </button>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting
            ? "Enregistrement..."
            : submitLabel}
        </button>
      </div>
    </form>
  );
}