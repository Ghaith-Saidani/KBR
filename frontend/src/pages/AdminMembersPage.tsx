import {
  useMemo,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useAdminMembers,
} from "../features/admin/admin.hooks";

import type {
  AdminMemberListParams,
} from "../features/admin/admin.types";

import type {
  UserRole,
  UserStatus,
} from "../features/auth/auth.types";

function roleLabel(
  role: UserRole,
) {
  switch (role) {
    case "admin":
      return "Administrateur";

    case "staff":
      return "Staff";

    default:
      return "Membre";
  }
}

function roleClass(
  role: UserRole,
) {
  switch (role) {
    case "admin":
      return "border-purple-500/20 bg-purple-500/10 text-purple-300";

    case "staff":
      return "border-blue-500/20 bg-blue-500/10 text-blue-300";

    default:
      return "border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]";
  }
}

function statusLabel(
  status: UserStatus,
) {
  switch (status) {
    case "active":
      return "Actif";

    case "suspended":
      return "Suspendu";

    case "pending":
      return "En attente";

    case "archived":
      return "Archivé";

    default:
      return status;
  }
}

function statusClass(
  status: UserStatus,
) {
  switch (status) {
    case "active":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

    case "suspended":
      return "border-red-500/20 bg-red-500/10 text-red-300";

    case "pending":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";

    case "archived":
      return "border-slate-500/20 bg-slate-500/10 text-slate-400";

    default:
      return "border-white/10 bg-white/5 text-slate-400";
  }
}

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

function getInitials(
  firstName: string,
  lastName: string,
) {
  return (
    `${firstName.charAt(0)}${lastName.charAt(0)}`
  ).toUpperCase();
}

export default function AdminMembersPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const [
    role,
    setRole,
  ] = useState<
    "all" | UserRole
  >("all");

  const [
    status,
    setStatus,
  ] = useState<
    "all" | UserStatus
  >("all");

  const [
    page,
    setPage,
  ] = useState(1);

  const limit = 20;

  const params = useMemo(
    (): AdminMemberListParams => ({
      skip:
        (page - 1) * limit,

      limit,

      search:
        search.trim() || undefined,

      role:
        role === "all"
          ? undefined
          : role,

      status:
        status === "all"
          ? undefined
          : status,
    }),
    [
      page,
      search,
      role,
      status,
    ],
  );

  const {
    data,
    isLoading,
    isError,
    isFetching,
  } = useAdminMembers(
    params,
  );

  const members =
    data?.items ?? [];

  const total =
    data?.total ?? 0;

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        total / limit,
      ),
    );

  function handleSearchChange(
    value: string,
  ) {
    setSearch(value);
    setPage(1);
  }

  function handleRoleChange(
    value: string,
  ) {
    setRole(
      value as
        | "all"
        | UserRole,
    );

    setPage(1);
  }

  function handleStatusChange(
    value: string,
  ) {
    setStatus(
      value as
        | "all"
        | UserStatus,
    );

    setPage(1);
  }

  function goToPreviousPage() {
    setPage(
      (current) =>
        Math.max(
          1,
          current - 1,
        ),
    );
  }

  function goToNextPage() {
    setPage(
      (current) =>
        Math.min(
          totalPages,
          current + 1,
        ),
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
              Gestion des membres
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Consultez les membres KBR,
              recherchez un profil et
              gérez les comptes et leurs
              permissions.
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm">
            <span className="text-slate-500">
              Total
            </span>

            <span className="ml-2 font-black text-white">
              {total}
            </span>
          </div>
        </div>

        <div className="mb-6 grid gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 lg:grid-cols-[1fr_auto_auto]">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              handleSearchChange(
                event.target.value,
              )
            }
            placeholder="Rechercher par nom ou email..."
            className="min-w-0 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <select
            value={role}
            onChange={(event) =>
              handleRoleChange(
                event.target.value,
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Tous les rôles
            </option>

            <option value="member">
              Membres
            </option>

            <option value="staff">
              Staff
            </option>

            <option value="admin">
              Administrateurs
            </option>
          </select>

          <select
            value={status}
            onChange={(event) =>
              handleStatusChange(
                event.target.value,
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Tous les statuts
            </option>

            <option value="pending">
              En attente
            </option>

            <option value="active">
              Actifs
            </option>

            <option value="suspended">
              Suspendus
            </option>
          </select>
        </div>

        {isLoading && (
          <div className="space-y-3">
            {Array.from({
              length: 6,
            }).map(
              (_, index) => (
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
              membres
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Vérifiez votre session et
              vos permissions
              administrateur, puis
              réessayez.
            </p>
          </div>
        )}

        {!isLoading &&
          !isError &&
          members.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <h2 className="text-xl font-bold">
                Aucun membre
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucun membre ne
                correspond aux filtres
                sélectionnés.
              </p>
            </div>
          )}

        {!isLoading &&
          !isError &&
          members.length > 0 && (
            <div className="space-y-3">
              {members.map(
                (member) => (
                  <article
                    key={
                      member.member_id
                    }
                    className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] transition hover:border-white/15"
                  >
                    <div className="flex flex-col gap-5 p-5 lg:flex-row lg:items-center">
                      <div className="h-16 w-16 shrink-0 overflow-hidden rounded-full bg-[#0b0b0b]">
                        {member.profile_image ? (
                          <img
                            src={
                              member.profile_image
                            }
                            alt=""
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center text-lg font-black text-[#f5c400]">
                            {getInitials(
                              member.first_name,
                              member.last_name,
                            )}
                          </div>
                        )}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-lg font-bold text-white">
                            {
                              member.first_name
                            }{" "}
                            {
                              member.last_name
                            }
                          </h2>

                          <span
                            className={[
                              "rounded-full border px-2.5 py-1 text-xs font-bold",
                              roleClass(
                                member.role,
                              ),
                            ].join(
                              " ",
                            )}
                          >
                            {roleLabel(
                              member.role,
                            )}
                          </span>

                          <span
                            className={[
                              "rounded-full border px-2.5 py-1 text-xs font-bold",
                              statusClass(
                                member.status,
                              ),
                            ].join(
                              " ",
                            )}
                          >
                            {statusLabel(
                              member.status,
                            )}
                          </span>
                        </div>

                        <p className="mt-1 truncate text-sm text-slate-400">
                          {
                            member.email
                          }
                        </p>

                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
                          <span>
                            Inscrit le{" "}
                            {formatDate(
                              member.created_at,
                            )}
                          </span>

                          {member.phone && (
                            <span>
                              {
                                member.phone
                              }
                            </span>
                          )}

                          {member.is_email_verified && (
                            <span className="text-emerald-400/70">
                              Email vérifié
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex shrink-0 flex-wrap gap-2">
                        <Link
                          to={`/admin/members/${member.member_id}/edit`}
                          className="rounded-lg border border-white/10 px-4 py-2.5 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                        >
                          Gérer
                        </Link>
                      </div>
                    </div>
                  </article>
                ),
              )}
            </div>
          )}

        {!isLoading &&
          !isError &&
          totalPages > 1 && (
            <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-slate-500">
                Page{" "}
                <span className="font-bold text-white">
                  {page}
                </span>{" "}
                sur{" "}
                <span className="font-bold text-white">
                  {totalPages}
                </span>

                {isFetching && (
                  <span className="ml-2 text-[#f5c400]">
                    Chargement...
                  </span>
                )}
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={
                    page === 1 ||
                    isFetching
                  }
                  onClick={
                    goToPreviousPage
                  }
                  className="rounded-lg border border-white/10 px-4 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  ← Précédent
                </button>

                <button
                  type="button"
                  disabled={
                    page ===
                      totalPages ||
                    isFetching
                  }
                  onClick={
                    goToNextPage
                  }
                  className="rounded-lg border border-white/10 px-4 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Suivant →
                </button>
              </div>
            </div>
          )}

        {data && (
          <div className="mt-5 text-xs text-slate-600">
            {members.length} membre
            {members.length !== 1
              ? "s"
              : ""}{" "}
            affiché
            {members.length !== 1
              ? "s"
              : ""}{" "}
            sur {total}
          </div>
        )}
      </div>
    </section>
  );
}