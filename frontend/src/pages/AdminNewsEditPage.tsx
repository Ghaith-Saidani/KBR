import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import NewsForm from "../components/forms/NewsForm";

import {
  useNewsById,
  useUpdateNews,
} from "../features/news/news.hooks";

import type {
  NewsUpdateRequest,
} from "../features/news/news.types";


export default function AdminNewsEditPage() {
  const {
    newsId,
  } = useParams();

  const navigate =
    useNavigate();

  const {
    data: article,
    isLoading,
    isError,
  } =
    useNewsById(newsId);

  const mutation =
    useUpdateNews();


  function handleSubmit(
    data: NewsUpdateRequest,
  ) {
    if (!newsId) {
      return;
    }

    mutation.mutate(
      {
        newsId,
        data,
      },
      {
        onSuccess: () => {
          navigate(
            "/admin/news",
          );
        },
      },
    );
  }


  if (isLoading) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505]">
        <p className="text-sm text-slate-400">
          Chargement de l'actualité...
        </p>
      </section>
    );
  }


  if (
    isError ||
    !article
  ) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6">
        <div className="text-center">
          <h1 className="text-3xl font-black text-white">
            Actualité introuvable
          </h1>

          <p className="mt-3 text-slate-400">
            Cette actualité n'existe pas
            ou n'est plus disponible.
          </p>

          <Link
            to="/admin/news"
            className="mt-6 inline-block rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            Retour aux actualités
          </Link>
        </div>
      </section>
    );
  }


  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-4xl">
        <Link
          to="/admin/news"
          className="text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux actualités
        </Link>


        <div className="mb-8 mt-6">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <h1 className="mt-2 text-3xl font-black">
            Modifier l'actualité
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Modifiez le contenu et les
            paramètres de publication.
          </p>
        </div>


        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <NewsForm
            mode="edit"
            initialValues={{
              title:
                article.title,

              slug:
                article.slug,

              excerpt:
                article.excerpt,

              content:
                article.content,

              cover_image:
                article.cover_image,

              status:
                article.status,

              published_at:
                article.published_at,
            }}
            submitLabel="Enregistrer les modifications"
            isSubmitting={
              mutation.isPending
            }
            onSubmit={
              handleSubmit
            }
            onCancel={() =>
              navigate(
                "/admin/news",
              )
            }
          />


          {mutation.isError && (
            <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
              <p className="text-sm font-semibold text-red-200">
                Impossible de modifier
                l'actualité.
              </p>

              <p className="mt-1 text-sm text-red-200/70">
                Le slug est peut-être
                déjà utilisé ou une erreur
                est survenue.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}