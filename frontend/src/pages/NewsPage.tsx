import { useState } from "react";
import { Link } from "react-router-dom";

import { useNews } from "../features/news/news.hooks";


function formatDate(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "long",
      year: "numeric",
    },
  );
}


export default function NewsPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const {
    data,
    isLoading,
    isError,
  } = useNews({
    search:
      search.trim() ||
      undefined,
  });


  return (
    <section className="min-h-[70vh] bg-[#050505] px-6 py-16">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
            KBR
          </p>

          <h1 className="mt-3 text-4xl font-black text-white sm:text-5xl">
            Actualités
          </h1>

          <p className="mt-4 max-w-2xl text-slate-400">
            Retrouvez les dernières
            actualités, annonces et
            informations de la communauté
            KBR.
          </p>
        </div>


        <div className="mb-8 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
          <input
            type="search"
            value={search}
            onChange={(
              event,
            ) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Rechercher une actualité..."
            aria-label="Rechercher une actualité"
            className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />
        </div>


        {isLoading && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({
              length: 6,
            }).map(
              (
                _,
                index,
              ) => (
                <div
                  key={index}
                  className="animate-pulse overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
                >
                  <div className="h-52 bg-white/5" />

                  <div className="space-y-3 p-6">
                    <div className="h-4 w-1/3 rounded bg-white/5" />

                    <div className="h-6 w-3/4 rounded bg-white/5" />

                    <div className="h-4 w-full rounded bg-white/5" />

                    <div className="h-4 w-5/6 rounded bg-white/5" />
                  </div>
                </div>
              ),
            )}
          </div>
        )}


        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-xl font-bold text-white">
              Impossible de charger les
              actualités
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Une erreur est survenue lors
              du chargement des actualités.
            </p>
          </div>
        )}


        {!isLoading &&
          !isError &&
          data?.items.length ===
            0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold text-white">
                Aucune actualité
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucune actualité ne correspond
                à votre recherche.
              </p>
            </div>
          )}


        {!isLoading &&
          !isError &&
          data &&
          data.items.length >
            0 && (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data.items.map(
                (article) => (
                  <Link
                    key={
                      article.id
                    }
                    to={`/news/${article.slug}`}
                    className="group overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:-translate-y-1 hover:border-[#f5c400]/40 hover:bg-white/[0.06]"
                  >
                    <div className="relative h-52 overflow-hidden bg-[#0b0b0b]">
                      {article.cover_image ? (
                        <img
                          src={
                            article.cover_image
                          }
                          alt={
                            article.title
                          }
                          className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center bg-gradient-to-br from-[#151515] to-[#050505]">
                          <span className="text-5xl font-black text-[#f5c400]/20">
                            KBR
                          </span>
                        </div>
                      )}

                      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 to-transparent" />
                    </div>


                    <div className="p-6">
                      <p className="text-xs font-semibold uppercase tracking-wider text-[#f5c400]">
                        {formatDate(
                          article.published_at ??
                            article.created_at,
                        )}
                      </p>

                      <h2 className="mt-2 line-clamp-2 text-xl font-bold text-white">
                        {
                          article.title
                        }
                      </h2>

                      {article.excerpt && (
                        <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-400">
                          {
                            article.excerpt
                          }
                        </p>
                      )}

                      <div className="mt-6 text-sm font-bold text-[#f5c400]">
                        Lire l'article →
                      </div>
                    </div>
                  </Link>
                ),
              )}
            </div>
          )}
      </div>
    </section>
  );
}