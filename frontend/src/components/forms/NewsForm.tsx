import type {
  NewsCreateRequest,
  NewsStatus,
  NewsUpdateRequest,
} from "../../features/news/news.types";


interface BaseNewsFormProps {
  initialValues?: {
    title?: string;
    slug?: string;
    excerpt?: string | null;
    content?: string;
    cover_image?: string | null;
    status?: NewsStatus;
    published_at?: string | null;
  };

  submitLabel?: string;
  isSubmitting?: boolean;
  onCancel?: () => void;
}


interface CreateNewsFormProps
  extends BaseNewsFormProps {
  mode?: "create";

  onSubmit: (
    data: NewsCreateRequest,
  ) => void;
}


interface EditNewsFormProps
  extends BaseNewsFormProps {
  mode: "edit";

  onSubmit: (
    data: NewsUpdateRequest,
  ) => void;
}


export type NewsFormProps =
  | CreateNewsFormProps
  | EditNewsFormProps;


function toDateTimeLocal(
  value?: string | null,
) {
  if (!value) {
    return "";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "";
  }

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


export default function NewsForm({
  mode = "create",
  initialValues,
  submitLabel = "Enregistrer",
  isSubmitting = false,
  onSubmit,
  onCancel,
}: NewsFormProps) {
  const values = {
    title:
      initialValues?.title ??
      "",

    slug:
      initialValues?.slug ??
      "",

    excerpt:
      initialValues?.excerpt ??
      "",

    content:
      initialValues?.content ??
      "",

    cover_image:
      initialValues?.cover_image ??
      "",

    status:
      initialValues?.status ??
      "draft",

    published_at:
      initialValues?.published_at ??
      null,
  };


  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const formData =
      new FormData(
        event.currentTarget,
      );


    const title =
      String(
        formData.get("title") ??
          "",
      ).trim();

    const slug =
      String(
        formData.get("slug") ??
          "",
      ).trim();

    const excerpt =
      String(
        formData.get("excerpt") ??
          "",
      ).trim();

    const content =
      String(
        formData.get("content") ??
          "",
      ).trim();

    const coverImage =
      String(
        formData.get(
          "cover_image",
        ) ?? "",
      ).trim();

    const status =
      String(
        formData.get(
          "status",
        ) ?? "draft",
      ) as NewsStatus;

    const publishedAt =
      String(
        formData.get(
          "published_at",
        ) ?? "",
      );


    if (
      !title ||
      !slug ||
      !content
    ) {
      return;
    }


    const data = {
      title,
      slug,
      excerpt:
        excerpt || null,
      content,
      cover_image:
        coverImage || null,
      status,
      published_at:
        publishedAt
          ? new Date(
              publishedAt,
            ).toISOString()
          : null,
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
          maxLength={200}
          defaultValue={
            values.title
          }
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="Titre de l'article"
        />
      </div>


      <div>
        <label
          htmlFor="slug"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Slug
        </label>

        <input
          id="slug"
          name="slug"
          type="text"
          required
          maxLength={220}
          defaultValue={
            values.slug
          }
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="mon-nouvel-article"
        />

        <p className="mt-2 text-xs text-slate-600">
          Utilisé dans l'URL de
          l'article.
        </p>
      </div>


      <div>
        <label
          htmlFor="excerpt"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Résumé
        </label>

        <textarea
          id="excerpt"
          name="excerpt"
          rows={3}
          maxLength={500}
          defaultValue={
            values.excerpt
          }
          className="w-full resize-y rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="Court résumé de l'article..."
        />
      </div>


      <div>
        <label
          htmlFor="content"
          className="mb-2 block text-sm font-semibold text-white"
        >
          Contenu
        </label>

        <textarea
          id="content"
          name="content"
          rows={14}
          required
          defaultValue={
            values.content
          }
          className="w-full resize-y rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-4 text-sm leading-7 text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="Rédigez le contenu complet de l'article..."
        />

        <p className="mt-2 text-xs text-slate-600">
          Le contenu est actuellement
          enregistré en texte simple.
        </p>
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
            values.cover_image
          }
          className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          placeholder="https://..."
        />
      </div>


      <div className="grid gap-6 md:grid-cols-2">
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
            defaultValue={
              values.status
            }
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="draft">
              Brouillon
            </option>

            <option value="published">
              Publié
            </option>
          </select>
        </div>


        <div>
          <label
            htmlFor="published_at"
            className="mb-2 block text-sm font-semibold text-white"
          >
            Date de publication
          </label>

          <input
            id="published_at"
            name="published_at"
            type="datetime-local"
            defaultValue={toDateTimeLocal(
              values.published_at,
            )}
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          />
        </div>
      </div>


      <div className="flex flex-col-reverse gap-3 sm:flex-row">
        {onCancel && (
          <button
            type="button"
            onClick={
              onCancel
            }
            disabled={
              isSubmitting
            }
            className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-6 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/[0.08] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Annuler
          </button>
        )}

        <button
          type="submit"
          disabled={
            isSubmitting
          }
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