import {
  useState,
} from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  useActivateAdminMember,
  useAdminMember,
  useSuspendAdminMember,
  useUpdateAdminMember,
  useUpdateAdminMemberRole,
} from "../features/admin/admin.hooks";

import type {
  AdminMember,
  AdminMemberUpdateRequest,
} from "../features/admin/admin.types";

import type {
  UserRole,
} from "../features/auth/auth.types";

export default function AdminMemberEditPage() {
  const {
    memberId,
  } = useParams();

  const {
    data: member,
    isLoading,
    isError,
  } = useAdminMember(
    memberId,
  );

  if (isLoading) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] text-slate-400">
        Chargement du membre...
      </section>
    );
  }

  if (isError || !member) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="text-center">
          <h1 className="text-2xl font-black">
            Membre introuvable
          </h1>

          <Link
            to="/admin/members"
            className="mt-5 inline-block text-sm font-bold text-[#f5c400]"
          >
            ← Retour aux membres
          </Link>
        </div>
      </section>
    );
  }

  return (
    <AdminMemberEditForm
      member={member}
      memberId={memberId}
    />
  );
}

interface AdminMemberEditFormProps {
  member: AdminMember;
  memberId: string | undefined;
}

function AdminMemberEditForm({
  member,
  memberId,
}: AdminMemberEditFormProps) {
  const navigate =
    useNavigate();

  const updateMutation =
    useUpdateAdminMember();

  const activateMutation =
    useActivateAdminMember();

  const suspendMutation =
    useSuspendAdminMember();

  const roleMutation =
    useUpdateAdminMemberRole();

  const [
    form,
    setForm,
  ] = useState<AdminMemberUpdateRequest>(
    () => ({
      first_name:
        member.first_name,
      last_name:
        member.last_name,
      phone:
        member.phone ?? "",
      profile_image:
        member.profile_image ?? "",
      bio:
        member.bio ?? "",
    }),
  );

  const [
    role,
    setRole,
  ] = useState<UserRole>(
    member.role,
  );

  function updateField(
    field: keyof AdminMemberUpdateRequest,
    value: string,
  ) {
    setForm(
      (current) => ({
        ...current,
        [field]: value,
      }),
    );
  }

  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!memberId) {
      return;
    }

    updateMutation.mutate({
      memberId,
      data: {
        first_name:
          form.first_name?.trim() ||
          null,

        last_name:
          form.last_name?.trim() ||
          null,

        phone:
          form.phone?.trim() ||
          null,

        profile_image:
          form.profile_image?.trim() ||
          null,

        bio:
          form.bio?.trim() ||
          null,
      },
    });
  }

  function handleRoleChange(
    nextRole: UserRole,
  ) {
    if (!memberId) {
      return;
    }

    if (
      nextRole ===
      member.role
    ) {
      setRole(nextRole);
      return;
    }

    const roleLabel =
      nextRole === "admin"
        ? "administrateur"
        : nextRole === "staff"
          ? "staff"
          : "membre";

    const confirmed =
      window.confirm(
        `Changer le rôle de ${member.first_name} ${member.last_name} en ${roleLabel} ?`,
      );

    if (!confirmed) {
      return;
    }

    setRole(nextRole);

    roleMutation.mutate({
      memberId,
      data: {
        role: nextRole,
      },
    });
  }

  function handleStatusAction() {
    if (!memberId) {
      return;
    }

    if (
      member.status ===
      "active"
    ) {
      const confirmed =
        window.confirm(
          `Suspendre le compte de ${member.first_name} ${member.last_name} ?`,
        );

      if (!confirmed) {
        return;
      }

      suspendMutation.mutate(
        memberId,
      );

      return;
    }

    activateMutation.mutate(
      memberId,
    );
  }

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-4xl">
        <Link
          to="/admin/members"
          className="text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux membres
        </Link>

        <div className="mb-8 mt-6">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <h1 className="mt-2 text-3xl font-black">
            Gestion du membre
          </h1>

          <p className="mt-3 text-sm text-slate-400">
            Gérez le profil, le rôle et le statut du compte.
          </p>
        </div>

        <div className="mb-6 rounded-2xl border border-white/10 bg-white/[0.04] p-6">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
            <div className="h-20 w-20 shrink-0 overflow-hidden rounded-full bg-[#0b0b0b]">
              {member.profile_image ? (
                <img
                  src={
                    member.profile_image
                  }
                  alt=""
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-xl font-black text-[#f5c400]">
                  {member.first_name
                    .charAt(0)
                    .toUpperCase()}

                  {member.last_name
                    .charAt(0)
                    .toUpperCase()}
                </div>
              )}
            </div>

            <div>
              <h2 className="text-xl font-black">
                {member.first_name}{" "}
                {member.last_name}
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {member.email}
              </p>

              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-slate-400">
                  {member.status}
                </span>

                <span className="rounded-full border border-[#f5c400]/20 bg-[#f5c400]/10 px-3 py-1 text-xs font-bold text-[#f5c400]">
                  {member.role}
                </span>

                {member.is_email_verified && (
                  <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-300">
                    Email vérifié
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8"
        >
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <label
                htmlFor="first_name"
                className="mb-2 block text-sm font-semibold text-white"
              >
                Prénom
              </label>

              <input
                id="first_name"
                type="text"
                value={
                  form.first_name ??
                  ""
                }
                onChange={(event) =>
                  updateField(
                    "first_name",
                    event.target.value,
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
              />
            </div>

            <div>
              <label
                htmlFor="last_name"
                className="mb-2 block text-sm font-semibold text-white"
              >
                Nom
              </label>

              <input
                id="last_name"
                type="text"
                value={
                  form.last_name ??
                  ""
                }
                onChange={(event) =>
                  updateField(
                    "last_name",
                    event.target.value,
                  )
                }
                className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
              />
            </div>
          </div>

          <div className="mt-6">
            <label
              htmlFor="phone"
              className="mb-2 block text-sm font-semibold text-white"
            >
              Téléphone
            </label>

            <input
              id="phone"
              type="tel"
              value={
                form.phone ??
                ""
              }
              onChange={(event) =>
                updateField(
                  "phone",
                  event.target.value,
                )
              }
              className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
            />
          </div>

          <div className="mt-6">
            <label
              htmlFor="profile_image"
              className="mb-2 block text-sm font-semibold text-white"
            >
              Image de profil
            </label>

            <input
              id="profile_image"
              type="url"
              value={
                form.profile_image ??
                ""
              }
              onChange={(event) =>
                updateField(
                  "profile_image",
                  event.target.value,
                )
              }
              placeholder="https://..."
              className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
            />
          </div>

          <div className="mt-6">
            <label
              htmlFor="bio"
              className="mb-2 block text-sm font-semibold text-white"
            >
              Biographie
            </label>

            <textarea
              id="bio"
              rows={6}
              value={
                form.bio ??
                ""
              }
              onChange={(event) =>
                updateField(
                  "bio",
                  event.target.value,
                )
              }
              className="w-full resize-y rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
            />
          </div>

          <div className="mt-8 border-t border-white/10 pt-8">
            <h2 className="text-lg font-black">
              Permissions et statut
            </h2>

            <div className="mt-5 grid gap-6 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="role"
                  className="mb-2 block text-sm font-semibold text-white"
                >
                  Rôle
                </label>

                <select
                  id="role"
                  value={role}
                  disabled={
                    roleMutation.isPending
                  }
                  onChange={(event) =>
                    handleRoleChange(
                      event.target
                        .value as UserRole,
                    )
                  }
                  className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400] disabled:opacity-50"
                >
                  <option value="member">
                    Membre
                  </option>

                  <option value="staff">
                    Staff
                  </option>

                  <option value="admin">
                    Administrateur
                  </option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-white">
                  Statut du compte
                </label>

                <button
                  type="button"
                  disabled={
                    activateMutation.isPending ||
                    suspendMutation.isPending
                  }
                  onClick={
                    handleStatusAction
                  }
                  className={[
                    "w-full rounded-xl border px-4 py-3 text-sm font-bold transition disabled:opacity-50",

                    member.status ===
                    "active"
                      ? "border-red-500/20 bg-red-500/10 text-red-300 hover:bg-red-500/20"
                      : "border-emerald-500/20 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20",
                  ].join(" ")}
                >
                  {member.status ===
                  "active"
                    ? "Suspendre le compte"
                    : "Activer le compte"}
                </button>
              </div>
            </div>
          </div>

          <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={() =>
                navigate(
                  "/admin/members",
                )
              }
              className="rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-slate-400 transition hover:bg-white/5 hover:text-white"
            >
              Annuler
            </button>

            <button
              type="submit"
              disabled={
                updateMutation.isPending
              }
              className="rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {updateMutation.isPending
                ? "Enregistrement..."
                : "Enregistrer les modifications"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}