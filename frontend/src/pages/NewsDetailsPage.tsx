import {
  Link,
  useParams,
} from "react-router-dom";

import {
  useNewsBySlug,
} from "../features/news/news.hooks";


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


export default function NewsDetailsPage() {
  const {
    slug,
  } = useParams();

  const {
    data: article,
    isLoading,
    isError,
  } =
    useNewsBySlug(slug);


  if (isLoading) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505]">
        <p className="text-sm text-slate-400">
          Chargement de l'article...
        </p>
      </section>
    );
  }


  if (
    isError ||
    !article
  ) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-[#050505] px-6">
        <div className="text-center">
          <h1 className="text-3xl font-black text-white">
            Article introuvable
          </h1>

          <p className="mt-3 text-slate-400">
            Cet article n'existe pas ou
            n'est plus disponible.
          </p>

          <Link
            to="/news"
            className="mt-6 inline-block rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            Retour aux actualités
          </Link>
        </div>
      </section>
    );
  }


  return (
    <section className="min-h-[70vh] bg-[#050505]">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <Link
          to="/news"
          className="inline-flex items-center text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux actualités
        </Link>


        <article className="mt-8 overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04]">
          {article.cover_image ? (
            <div className="h-[300px] overflow-hidden md:h-[500px]">
              <img
                src={
                  article.cover_image
                }
                alt={
                  article.title
                }
                className="h-full w-full object-cover"
              />
            </div>
          ) : (
            <div className="flex h-[300px] items-center justify-center bg-gradient-to-br from-[#151515] to-[#050505] md:h-[500px]">
              <span className="text-7xl font-black text-[#f5c400]/20">
                KBR
              </span>
            </div>
          )}


          <div className="p-6 md:p-10 lg:p-14">
            <p className="text-sm font-bold uppercase tracking-[0.15em] text-[#f5c400]">
              {formatDate(
                article.published_at ??
                  article.created_at,
              )}
            </p>

            <h1 className="mt-4 text-4xl font-black leading-tight text-white md:text-5xl lg:text-6xl">
              {
                article.title
              }
            </h1>


            {article.excerpt && (
              <p className="mt-6 max-w-4xl text-lg leading-8 text-slate-400">
                {
                  article.excerpt
                }
              </p>
            )}


            <div className="my-10 h-px bg-white/10" />


            <div className="max-w-4xl">
              <p className="whitespace-pre-line text-base leading-8 text-slate-300 md:text-lg">
                {
                  article.content
                }
              </p>
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}