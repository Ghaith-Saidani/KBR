import {
  useMemo,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useDeleteNews,
  useManageNews,
  useUpdateNews,
} from "../features/news/news.hooks";

import type {
  NewsStatus,
} from "../features/news/news.types";


function formatDate(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  );
}


function statusLabel(
  status: NewsStatus,
) {
  return status ===
    "published"
    ? "Publié"
    : "Brouillon";
}


function statusClass(
  status: NewsStatus,
) {
  return status ===
    "published"
    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
    : "border-amber-500/20 bg-amber-500/10 text-amber-300";
}


export default function AdminNewsPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<
    "all" | NewsStatus
  >("all");

  const [
    deletingId,
    setDeletingId,
  ] = useState<
    string | null
  >(null);


  const params = useMemo(
    () => ({
      search:
        search.trim() ||
        undefined,
    }),
    [search],
  );


  const {
    data,
    isLoading,
    isError,
  } =
    useManageNews(params);


  const updateMutation =
    useUpdateNews();

  const deleteMutation =
    useDeleteNews();


  const articles =
    data?.items.filter(
      (article) =>
        statusFilter ===
          "all" ||
        article.status ===
          statusFilter,
    ) ?? [];


  function handleStatusChange(
    newsId: string,
    status: NewsStatus,
  ) {
    updateMutation.mutate({
      newsId,
      data: {
        status,
      },
    });
  }


  function handleDelete(
    newsId: string,
    title: string,
  ) {
    const confirmed =
      window.confirm(
        `Supprimer définitivement « ${title} » ?`,
      );

    if (!confirmed) {
      return;
    }

    setDeletingId(newsId);

    deleteMutation.mutate(
      newsId,
      {
        onSettled: () => {
          setDeletingId(null);
        },
      },
    );
  }


  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black sm:text-4xl">
              Gestion des actualités
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Créez, modifiez, publiez et
              gérez les actualités KBR.
            </p>
          </div>


          <Link
            to="/admin/news/new"
            className="inline-flex items-center justify-center rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
          >
            + Nouvelle actualité
          </Link>
        </div>


        <div className="mb-6 grid gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 lg:grid-cols-[1fr_auto]">
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
            placeholder="Rechercher..."
            className="min-w-0 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />


          <select
            value={
              statusFilter
            }
            onChange={(
              event,
            ) =>
              setStatusFilter(
                event.target
                  .value as
                  | "all"
                  | NewsStatus,
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Tous les statuts
            </option>

            <option value="draft">
              Brouillons
            </option>

            <option value="published">
              Publiés
            </option>
          </select>
        </div>


        {isLoading && (
          <div className="space-y-3">
            {Array.from({
              length: 5,
            }).map(
              (
                _,
                index,
              ) => (
                <div
                  key={index}
                  className="h-28 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
                />
              ),
            )}
          </div>
        )}


        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-lg font-bold text-white">
              Impossible de charger les
              actualités
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Vérifiez votre session et
              réessayez.
            </p>
          </div>
        )}


        {!isLoading &&
          !isError &&
          articles.length ===
            0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold">
                Aucune actualité
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucune actualité ne
                correspond aux filtres
                sélectionnés.
              </p>
            </div>
          )}


        {!isLoading &&
          !isError &&
          articles.length >
            0 && (
            <div className="space-y-3">
              {articles.map(
                (article) => (
                  <article
                    key={
                      article.id
                    }
                    className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
                  >
                    <div className="flex flex-col gap-5 p-5 lg:flex-row lg:items-center">
                      <div className="h-20 w-full shrink-0 overflow-hidden rounded-xl bg-[#0b0b0b] lg:w-28">
                        {article.cover_image ? (
                          <img
                            src={
                              article.cover_image
                            }
                            alt=""
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center">
                            <span className="font-black text-[#f5c400]/20">
                              KBR
                            </span>
                          </div>
                        )}
                      </div>


                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={[
                              "rounded-full border px-2.5 py-1 text-xs font-bold",
                              statusClass(
                                article.status,
                              ),
                            ].join(
                              " ",
                            )}
                          >
                            {statusLabel(
                              article.status,
                            )}
                          </span>

                          <span className="text-xs text-slate-500">
                            {formatDate(
                              article.published_at ??
                                article.created_at,
                            )}
                          </span>
                        </div>


                        <h2 className="mt-2 truncate text-lg font-bold text-white">
                          {
                            article.title
                          }
                        </h2>


                        <p className="mt-1 truncate text-sm text-slate-500">
                          /news/
                          {
                            article.slug
                          }
                        </p>
                      </div>


                      <div className="flex flex-wrap gap-2">
                        {article.status !==
                          "published" && (
                          <button
                            type="button"
                            disabled={
                              updateMutation.isPending
                            }
                            onClick={() =>
                              handleStatusChange(
                                article.id,
                                "published",
                              )
                            }
                            className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs font-bold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                          >
                            Publier
                          </button>
                        )}


                        {article.status ===
                          "published" && (
                          <button
                            type="button"
                            disabled={
                              updateMutation.isPending
                            }
                            onClick={() =>
                              handleStatusChange(
                                article.id,
                                "draft",
                              )
                            }
                            className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs font-bold text-amber-300 transition hover:bg-amber-500/20 disabled:opacity-50"
                          >
                            Brouillon
                          </button>
                        )}


                        <Link
                          to={`/admin/news/${article.id}/edit`}
                          className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                        >
                          Modifier
                        </Link>


                        <button
                          type="button"
                          disabled={
                            deletingId ===
                            article.id
                          }
                          onClick={() =>
                            handleDelete(
                              article.id,
                              article.title,
                            )
                          }
                          className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-400 transition hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50"
                        >
                          {deletingId ===
                          article.id
                            ? "Suppression..."
                            : "Supprimer"}
                        </button>
                      </div>
                    </div>
                  </article>
                ),
              )}
            </div>
          )}


        {data && (
          <div className="mt-5 text-xs text-slate-600">
            {articles.length}{" "}
            actualité
            {articles.length !==
            1
              ? "s"
              : ""}{" "}
            affichée
            {articles.length !==
            1
              ? "s"
              : ""}{" "}
            sur {data.total}
          </div>
        )}
      </div>
    </section>
  );
}