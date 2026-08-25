import { Link } from "react-router-dom";

import { useNews } from "../../features/news/news.hooks";

function formatDate(value: string | null) {
  if (!value) {
    return null;
  }

  return new Date(value).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "long",
      year: "numeric",
    },
  );
}

export default function NewsPreview() {
  const {
    data,
    isLoading,
    isError,
  } = useNews({
    limit: 3,
  });

  const news = data?.items ?? [];

  return (
    <section className="bg-[#050505] py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F5C400]">
              Actualités
            </p>

            <h2 className="mt-3 text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
              La vie de KBR
            </h2>
          </div>

          <Link
            to="/news"
            className="font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
          >
            Toutes les actualités →
          </Link>
        </div>

        {isLoading && (
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="overflow-hidden rounded-2xl border border-white/10 bg-[#0B0B0B]"
              >
                <div className="h-48 animate-pulse bg-white/5" />

                <div className="space-y-4 p-7">
                  <div className="h-3 w-24 animate-pulse rounded bg-white/10" />

                  <div className="h-6 w-4/5 animate-pulse rounded bg-white/10" />

                  <div className="h-4 w-full animate-pulse rounded bg-white/10" />

                  <div className="h-4 w-3/5 animate-pulse rounded bg-white/10" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="mt-12 rounded-2xl border border-red-500/20 bg-red-500/5 px-6 py-12 text-center">
            <p className="text-lg font-bold text-white">
              Impossible de charger les actualités.
            </p>

            <p className="mx-auto mt-3 max-w-xl text-sm text-white/45">
              Les dernières publications KBR seront affichées ici
              dès qu'elles seront disponibles.
            </p>
          </div>
        )}

        {!isLoading && !isError && news.length === 0 && (
          <div className="mt-12 rounded-2xl border border-dashed border-white/15 bg-[#0B0B0B] px-6 py-16 text-center">
            <p className="text-lg font-bold text-white">
              Les actualités KBR arrivent bientôt.
            </p>

            <p className="mx-auto mt-3 max-w-xl text-white/50">
              Les publications officielles du club apparaîtront
              ici dès leur mise en ligne.
            </p>
          </div>
        )}

        {!isLoading && !isError && news.length > 0 && (
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {news.map((article) => (
              <article
                key={article.id}
                className="group overflow-hidden rounded-2xl border border-white/10 bg-[#0B0B0B] transition hover:-translate-y-1 hover:border-[#F5C400]/30"
              >
                {article.cover_image ? (
                  <div className="h-48 overflow-hidden">
                    <img
                      src={article.cover_image}
                      alt={article.title}
                      className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                    />
                  </div>
                ) : (
                  <div className="flex h-48 items-center justify-center bg-gradient-to-br from-[#161616] to-[#090909]">
                    <div className="h-2 w-12 rounded-full bg-[#F5C400]" />
                  </div>
                )}

                <div className="p-7">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white/35">
                    <span>
                      KBR News
                    </span>

                    {formatDate(
                      article.published_at,
                    ) && (
                      <>
                        <span className="text-white/20">
                          •
                        </span>

                        <span>
                          {formatDate(
                            article.published_at,
                          )}
                        </span>
                      </>
                    )}
                  </div>

                  <h3 className="mt-3 line-clamp-2 text-xl font-black text-white transition group-hover:text-[#F5C400]">
                    {article.title}
                  </h3>

                  {article.excerpt && (
                    <p className="mt-3 line-clamp-3 text-sm leading-6 text-white/45">
                      {article.excerpt}
                    </p>
                  )}

                  <Link
                    to={`/news/${article.slug}`}
                    className="mt-5 inline-flex text-sm font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
                  >
                    Lire l'article →
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}