import {
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import type {
  Activity,
  ActivityStatus,
} from "../../features/activities/activities.types";

interface ActivityFormProps {
  activity?: Activity;
  submitLabel: string;
  isSubmitting: boolean;
  onSubmit: (data: {
    title: string;
    slug: string;
    excerpt: string | null;
    description: string;
    cover_image: string | null;
    status: ActivityStatus;
    start_at: string | null;
    end_at: string | null;
    location: string | null;
  }) => void;
}

function slugify(
  value: string,
) {
  return value
    .normalize("NFD")
    .replace(
      /[\u0300-\u036f]/g,
      "",
    )
    .toLowerCase()
    .trim()
    .replace(
      /[^a-z0-9]+/g,
      "-",
    )
    .replace(
      /^-+|-+$/g,
      "",
    );
}

function toLocalDateTime(
  value: string | null,
) {
  if (!value) {
    return "";
  }

  const date =
    new Date(value);

  const offset =
    date.getTimezoneOffset();

  const localDate =
    new Date(
      date.getTime() -
        offset * 60 * 1000,
    );

  return localDate
    .toISOString()
    .slice(0, 16);
}

export default function ActivityForm({
  activity,
  submitLabel,
  isSubmitting,
  onSubmit,
}: ActivityFormProps) {
  const [
    title,
    setTitle,
  ] = useState(
    activity?.title ?? "",
  );

  const [
    slug,
    setSlug,
  ] = useState(
    activity?.slug ?? "",
  );

  const [
    slugTouched,
    setSlugTouched,
  ] = useState(
    Boolean(activity),
  );

  const [
    excerpt,
    setExcerpt,
  ] = useState(
    activity?.excerpt ?? "",
  );

  const [
    description,
    setDescription,
  ] = useState(
    activity?.description ?? "",
  );

  const [
    coverImage,
    setCoverImage,
  ] = useState(
    activity?.cover_image ?? "",
  );

  const [
    status,
    setStatus,
  ] = useState<ActivityStatus>(
    activity?.status ??
      "draft",
  );

  const [
    startAt,
    setStartAt,
  ] = useState(
    toLocalDateTime(
      activity?.start_at ??
        null,
    ),
  );

  const [
    endAt,
    setEndAt,
  ] = useState(
    toLocalDateTime(
      activity?.end_at ??
        null,
    ),
  );

  const [
    location,
    setLocation,
  ] = useState(
    activity?.location ?? "",
  );

  function handleTitleChange(
    value: string,
  ) {
    setTitle(value);

    if (!slugTouched) {
      setSlug(
        slugify(value),
      );
    }
  }

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    onSubmit({
      title: title.trim(),
      slug:
        slug.trim() ||
        slugify(title),
      excerpt:
        excerpt.trim() ||
        null,
      description:
        description.trim(),
      cover_image:
        coverImage.trim() ||
        null,
      status,
      start_at: startAt
        ? new Date(
            startAt,
          ).toISOString()
        : null,
      end_at: endAt
        ? new Date(
            endAt,
          ).toISOString()
        : null,
      location:
        location.trim() ||
        null,
    });
  }

  const inputClass =
    "w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]";

  const labelClass =
    "mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-slate-500";

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6"
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <label
            htmlFor="activity-title"
            className={labelClass}
          >
            Titre
          </label>

          <input
            id="activity-title"
            value={title}
            onChange={(event) =>
              handleTitleChange(
                event.target.value,
              )
            }
            placeholder="Titre de l'activité"
            required
            maxLength={200}
            className={inputClass}
          />
        </div>

        <div>
          <label
            htmlFor="activity-slug"
            className={labelClass}
          >
            Slug
          </label>

          <input
            id="activity-slug"
            value={slug}
            onChange={(event) => {
              setSlugTouched(true);

              setSlug(
                slugify(
                  event.target.value,
                ),
              );
            }}
            placeholder="mon-activite"
            required
            maxLength={220}
            className={inputClass}
          />

          <p className="mt-2 text-xs text-slate-600">
            URL : /activities/
            {slug || "..."}
          </p>
        </div>
      </div>

      <div>
        <label
          htmlFor="activity-excerpt"
          className={labelClass}
        >
          Résumé
        </label>

        <textarea
          id="activity-excerpt"
          value={excerpt}
          onChange={(event) =>
            setExcerpt(
              event.target.value,
            )
          }
          placeholder="Courte présentation de l'activité..."
          maxLength={500}
          rows={3}
          className={`${inputClass} resize-y`}
        />
      </div>

      <div>
        <label
          htmlFor="activity-description"
          className={labelClass}
        >
          Description
        </label>

        <textarea
          id="activity-description"
          value={description}
          onChange={(event) =>
            setDescription(
              event.target.value,
            )
          }
          placeholder="Description complète de l'activité..."
          required
          rows={10}
          className={`${inputClass} resize-y`}
        />
      </div>

      <div>
        <label
          htmlFor="activity-cover"
          className={labelClass}
        >
          Image de couverture
        </label>

        <input
          id="activity-cover"
          type="url"
          value={coverImage}
          onChange={(event) =>
            setCoverImage(
              event.target.value,
            )
          }
          placeholder="https://..."
          className={inputClass}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label
            htmlFor="activity-start"
            className={labelClass}
          >
            Date de début
          </label>

          <input
            id="activity-start"
            type="datetime-local"
            value={startAt}
            onChange={(event) =>
              setStartAt(
                event.target.value,
              )
            }
            className={inputClass}
          />
        </div>

        <div>
          <label
            htmlFor="activity-end"
            className={labelClass}
          >
            Date de fin
          </label>

          <input
            id="activity-end"
            type="datetime-local"
            value={endAt}
            onChange={(event) =>
              setEndAt(
                event.target.value,
              )
            }
            className={inputClass}
          />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label
            htmlFor="activity-location"
            className={labelClass}
          >
            Lieu
          </label>

          <input
            id="activity-location"
            value={location}
            onChange={(event) =>
              setLocation(
                event.target.value,
              )
            }
            placeholder="Bizerte, Tunisie"
            maxLength={255}
            className={inputClass}
          />
        </div>

        <div>
          <label
            htmlFor="activity-status"
            className={labelClass}
          >
            Statut
          </label>

          <select
            id="activity-status"
            value={status}
            onChange={(event) =>
              setStatus(
                event.target.value as ActivityStatus,
              )
            }
            className={inputClass}
          >
            <option value="draft">
              Brouillon
            </option>

            <option value="published">
              Publié
            </option>
          </select>
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 border-t border-white/10 pt-6 sm:flex-row sm:justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-black text-black transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting
            ? "Enregistrement..."
            : submitLabel}
        </button>
      </div>
    </form>
  );
}