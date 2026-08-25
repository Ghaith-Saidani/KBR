import {
  Link,
  useNavigate,
} from "react-router-dom";

import NewsForm from "../components/forms/NewsForm";

import {
  useCreateNews,
} from "../features/news/news.hooks";

import type {
  NewsCreateRequest,
} from "../features/news/news.types";


export default function AdminNewsCreatePage() {
  const navigate =
    useNavigate();

  const mutation =
    useCreateNews();


  function handleSubmit(
    data: NewsCreateRequest,
  ) {
    mutation.mutate(
      data,
      {
        onSuccess: (
          createdNews,
        ) => {
          navigate(
            `/admin/news/${createdNews.id}/edit`,
          );
        },
      },
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
            Créer une actualité
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Publiez une nouvelle actualité
            pour la communauté KBR.
          </p>
        </div>


        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
          <NewsForm
            mode="create"
            submitLabel="Créer l'actualité"
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
                Impossible de créer
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