import {
  useState,
} from "react";

import {
  Link,
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
  AdminMemberUpdateRequest,
} from "../features/admin/admin.types";

import type {
  UserRole,
} from "../features/auth/auth.types";

import {
  useAuthStore,
} from "../stores/authStore";


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
  status: string,
) {
  switch (status) {
    case "active":
      return "Actif";

    case "pending":
      return "En attente";

    case "suspended":
      return "Suspendu";

    case "archived":
      return "Archivé";

    default:
      return status;
  }
}


function statusClass(
  status: string,
) {
  switch (status) {
    case "active":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

    case "pending":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";

    case "suspended":
      return "border-red-500/20 bg-red-500/10 text-red-300";

    case "archived":
      return "border-slate-500/20 bg-slate-500/10 text-slate-400";

    default:
      return "border-white/10 bg-white/5 text-slate-400";
  }
}


function getInitials(
  firstName: string,
  lastName: string,
) {
  return (
    `${firstName.charAt(0)}${lastName.charAt(0)}`
  ).toUpperCase();
}


function formatDate(
  value: string | null,
) {
  if (!value) {
    return "—";
  }

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


interface AdminMemberEditFormProps {
  member: NonNullable<
    ReturnType<typeof useAdminMember>["data"]
  >;
  memberId: string;
  currentUserId?: string;
}


function AdminMemberEditForm({
  member,
  memberId,
  currentUserId,
}: AdminMemberEditFormProps) {
  const updateMutation =
    useUpdateAdminMember();

  const activateMutation =
    useActivateAdminMember();

  const suspendMutation =
    useSuspendAdminMember();

  const roleMutation =
    useUpdateAdminMemberRole();

  const [
    firstName,
    setFirstName,
  ] = useState(
    member.first_name,
  );

  const [
    lastName,
    setLastName,
  ] = useState(
    member.last_name,
  );

  const [
    phone,
    setPhone,
  ] = useState(
    member.phone ?? "",
  );

  const [
    profileImage,
    setProfileImage,
  ] = useState(
    member.profile_image ?? "",
  );

  const [
    bio,
    setBio,
  ] = useState(
    member.bio ?? "",
  );

  const [
    role,
    setRole,
  ] = useState<UserRole>(
    member.role,
  );

  const [
    formMessage,
    setFormMessage,
  ] = useState<
    string | null
  >(null);

  const [
    formError,
    setFormError,
  ] = useState<
    string | null
  >(null);

  const isSaving =
    updateMutation.isPending;

  const isChangingStatus =
    activateMutation.isPending ||
    suspendMutation.isPending;

  const isChangingRole =
    roleMutation.isPending;

  const isMutating =
    isSaving ||
    isChangingStatus ||
    isChangingRole;

  const isCurrentUser =
    Boolean(
      currentUserId &&
      member.user_id === currentUserId,
    );

  function clearMessages() {
    setFormMessage(null);
    setFormError(null);
  }

  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    clearMessages();

    const data: AdminMemberUpdateRequest = {
      first_name:
        firstName.trim() || null,

      last_name:
        lastName.trim() || null,

      phone:
        phone.trim() || null,

      profile_image:
        profileImage.trim() || null,

      bio:
        bio.trim() || null,
    };

    updateMutation.mutate(
      {
        memberId,
        data,
      },
      {
        onSuccess: () => {
          setFormMessage(
            "Les informations du membre ont été enregistrées.",
          );
        },

        onError: () => {
          setFormError(
            "Impossible d'enregistrer les modifications.",
          );
        },
      },
    );
  }

  function handleActivate() {
    clearMessages();

    activateMutation.mutate(
      memberId,
      {
        onSuccess: () => {
          setFormMessage(
            "Le compte a été activé.",
          );
        },

        onError: () => {
          setFormError(
            "Impossible d'activer ce compte.",
          );
        },
      },
    );
  }

  function handleSuspend() {
    if (isCurrentUser) {
      setFormError(
        "Vous ne pouvez pas suspendre votre propre compte administrateur.",
      );

      return;
    }

    const confirmed =
      window.confirm(
        "Voulez-vous vraiment suspendre ce compte ? Le membre ne pourra plus se connecter.",
      );

    if (!confirmed) {
      return;
    }

    clearMessages();

    suspendMutation.mutate(
      memberId,
      {
        onSuccess: () => {
          setFormMessage(
            "Le compte a été suspendu.",
          );
        },

        onError: () => {
          setFormError(
            "Impossible de suspendre ce compte.",
          );
        },
      },
    );
  }

  function handleRoleChange(
    value: string,
  ) {
    const nextRole =
      value as UserRole;

    if (
      nextRole === member.role
    ) {
      setRole(nextRole);
      return;
    }

    if (
      isCurrentUser &&
      nextRole !== "admin"
    ) {
      setFormError(
        "Vous ne pouvez pas retirer votre propre rôle administrateur.",
      );

      setRole("admin");

      return;
    }

    const confirmed =
      window.confirm(
        `Voulez-vous modifier le rôle de ce membre en « ${roleLabel(nextRole)} » ?`,
      );

    if (!confirmed) {
      setRole(member.role);
      return;
    }

    clearMessages();

    setRole(nextRole);

    roleMutation.mutate(
      {
        memberId,
        data: {
          role: nextRole,
        },
      },
      {
        onSuccess: () => {
          setFormMessage(
            "Le rôle du membre a été modifié.",
          );
        },

        onError: () => {
          setRole(member.role);

          setFormError(
            "Impossible de modifier le rôle du membre.",
          );
        },
      },
    );
  }

  return (
    <>
      {(formMessage ||
        formError) && (
        <div
          className={[
            "mb-6 rounded-xl border px-4 py-3 text-sm",
            formError
              ? "border-red-500/20 bg-red-500/10 text-red-200"
              : "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
          ].join(" ")}
        >
          {formError ??
            formMessage}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 sm:p-8"
        >
          <div className="mb-7">
            <h2 className="text-xl font-black">
              Informations du membre
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Modifiez les informations
              publiques et personnelles
              associées au profil.
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label
                htmlFor="firstName"
                className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500"
              >
                Prénom
              </label>

              <input
                id="firstName"
                type="text"
                value={firstName}
                onChange={(event) =>
                  setFirstName(
                    event.target.value,
                  )
                }
                maxLength={100}
                disabled={isSaving}
                className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-700 focus:border-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <div>
              <label
                htmlFor="lastName"
                className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500"
              >
                Nom
              </label>

              <input
                id="lastName"
                type="text"
                value={lastName}
                onChange={(event) =>
                  setLastName(
                    event.target.value,
                  )
                }
                maxLength={100}
                disabled={isSaving}
                className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-700 focus:border-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
          </div>

          <div className="mt-5">
            <label
              htmlFor="email"
              className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500"
            >
              Adresse email
            </label>

            <input
              id="email"
              type="email"
              value={member.email}
              disabled
              className="w-full cursor-not-allowed rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 text-sm text-slate-500 outline-none"
            />

            <p className="mt-2 text-xs text-slate-700">
              L'adresse email ne peut pas
              être modifiée depuis cet écran.
            </p>
          </div>

          <div className="mt-5">
            <label
              htmlFor="phone"
              className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500"
            >
              Téléphone
            </label>

            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(event) =>
                setPhone(
                  event.target.value,
                )
              }
              maxLength={30}
              disabled={isSaving}
              placeholder="Numéro de téléphone"
              className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-700 focus:border-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          <div className="mt-5">
            <label
              htmlFor="profileImage"
              className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500"
            >
              Image de profil
            </label>

            <input
              id="profileImage"
              type="url"
              value={profileImage}
              onChange={(event) =>
                setProfileImage(
                  event.target.value,
                )
              }
              maxLength={500}
              disabled={isSaving}
              placeholder="https://..."
              className="w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-700 focus:border-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          <div className="mt-5">
            <label
              htmlFor="bio"
              className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500"
            >
              Biographie
            </label>

            <textarea
              id="bio"
              value={bio}
              onChange={(event) =>
                setBio(
                  event.target.value,
                )
              }
              maxLength={2000}
              rows={6}
              disabled={isSaving}
              placeholder="Présentation du membre..."
              className="w-full resize-y rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm leading-6 text-white outline-none transition placeholder:text-slate-700 focus:border-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
            />

            <div className="mt-2 text-right text-xs text-slate-700">
              {bio.length}/2000
            </div>
          </div>

          <div className="mt-8 flex flex-col-reverse gap-3 border-t border-white/10 pt-6 sm:flex-row sm:justify-end">
            <Link
              to="/admin/members"
              className="rounded-xl border border-white/10 px-5 py-3 text-center text-sm font-bold text-slate-400 transition hover:bg-white/5 hover:text-white"
            >
              Annuler
            </Link>

            <button
              type="submit"
              disabled={isMutating}
              className="rounded-xl bg-[#f5c400] px-6 py-3 text-sm font-black text-black transition hover:bg-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSaving
                ? "Enregistrement..."
                : "Enregistrer les modifications"}
            </button>
          </div>
        </form>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <h2 className="text-lg font-black">
              Compte
            </h2>

            <div className="mt-5 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-600">
                  Rôle
                </p>

                <select
                  value={role}
                  onChange={(event) =>
                    handleRoleChange(
                      event.target.value,
                    )
                  }
                  disabled={
                    isChangingRole ||
                    isCurrentUser
                  }
                  className="mt-2 w-full rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm font-semibold text-white outline-none focus:border-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
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

                {isCurrentUser && (
                  <p className="mt-2 text-xs leading-5 text-amber-400/70">
                    Votre propre rôle
                    administrateur ne peut
                    pas être retiré ici.
                  </p>
                )}
              </div>

              <div>
                <p className="text-xs uppercase tracking-wider text-slate-600">
                  Statut du compte
                </p>

                <div className="mt-2">
                  <span
                    className={[
                      "inline-flex rounded-full border px-3 py-1.5 text-xs font-bold",
                      statusClass(
                        member.status,
                      ),
                    ].join(" ")}
                  >
                    {statusLabel(
                      member.status,
                    )}
                  </span>
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-wider text-slate-600">
                  Email
                </p>

                <p
                  className={[
                    "mt-2 text-sm font-semibold",
                    member.is_email_verified
                      ? "text-emerald-400"
                      : "text-amber-400",
                  ].join(" ")}
                >
                  {member.is_email_verified
                    ? "Email vérifié"
                    : "Email non vérifié"}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <h2 className="text-lg font-black">
              Gestion du compte
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Les actions ci-dessous
              modifient immédiatement
              l'accès du membre.
            </p>

            <div className="mt-5 space-y-3">
              {member.status !==
                "active" && (
                <button
                  type="button"
                  onClick={
                    handleActivate
                  }
                  disabled={
                    isMutating
                  }
                  className="w-full rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm font-bold text-emerald-300 transition hover:bg-emerald-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {activateMutation.isPending
                    ? "Activation..."
                    : "Activer le compte"}
                </button>
              )}

              {member.status !==
                "suspended" && (
                <button
                  type="button"
                  onClick={
                    handleSuspend
                  }
                  disabled={
                    isMutating ||
                    isCurrentUser
                  }
                  className="w-full rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-bold text-red-300 transition hover:bg-red-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {suspendMutation.isPending
                    ? "Suspension..."
                    : "Suspendre le compte"}
                </button>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <h2 className="text-lg font-black">
              Informations système
            </h2>

            <dl className="mt-5 space-y-4">
              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-600">
                  ID utilisateur
                </dt>

                <dd className="mt-1 break-all font-mono text-xs text-slate-400">
                  {member.user_id}
                </dd>
              </div>

              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-600">
                  ID membre
                </dt>

                <dd className="mt-1 break-all font-mono text-xs text-slate-400">
                  {member.member_id}
                </dd>
              </div>

              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-600">
                  Inscription
                </dt>

                <dd className="mt-1 text-sm text-slate-400">
                  {formatDate(
                    member.created_at,
                  )}
                </dd>
              </div>

              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-600">
                  Dernière modification
                </dt>

                <dd className="mt-1 text-sm text-slate-400">
                  {formatDate(
                    member.updated_at,
                  )}
                </dd>
              </div>

              <div>
                <dt className="text-xs uppercase tracking-wider text-slate-600">
                  Date d'adhésion
                </dt>

                <dd className="mt-1 text-sm text-slate-400">
                  {formatDate(
                    member.joined_at,
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </aside>
      </div>
    </>
  );
}


export default function AdminMemberEditPage() {
  const {
    memberId,
  } = useParams<{
    memberId: string;
  }>();

  const currentUser =
    useAuthStore(
      (state) => state.user,
    );

  const {
    data: member,
    isLoading,
    isError,
    refetch,
  } = useAdminMember(
    memberId,
  );

  if (!memberId) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="text-center">
          <h1 className="text-2xl font-black">
            Membre introuvable
          </h1>

          <Link
            to="/admin/members"
            className="mt-5 inline-flex rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-black text-black"
          >
            Retour aux membres
          </Link>
        </div>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] text-slate-400">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-[#f5c400]" />

          <p className="mt-4 text-sm">
            Chargement du membre...
          </p>
        </div>
      </section>
    );
  }

  if (
    isError ||
    !member
  ) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="max-w-md text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10 text-2xl">
            !
          </div>

          <h1 className="mt-5 text-2xl font-black">
            Membre introuvable
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            Impossible de charger les
            informations de ce membre.
          </p>

          <div className="mt-6 flex justify-center gap-3">
            <button
              type="button"
              onClick={() =>
                refetch()
              }
              className="rounded-lg border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              Réessayer
            </button>

            <Link
              to="/admin/members"
              className="rounded-lg bg-[#f5c400] px-4 py-2.5 text-sm font-black text-black transition hover:bg-[#ffd21a]"
            >
              Retour aux membres
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl">
        <Link
          to="/admin/members"
          className="inline-flex items-center text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
        >
          ← Retour aux membres
        </Link>

        <div className="mb-8 mt-6">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <div className="mt-3 flex flex-col gap-5 sm:flex-row sm:items-center">
            <div className="h-20 w-20 shrink-0 overflow-hidden rounded-full border border-white/10 bg-[#0b0b0b]">
              {member.profile_image ? (
                <img
                  src={member.profile_image}
                  alt={`${member.first_name} ${member.last_name}`}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-xl font-black text-[#f5c400]">
                  {getInitials(
                    member.first_name,
                    member.last_name,
                  )}
                </div>
              )}
            </div>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-3xl font-black">
                  {member.first_name}{" "}
                  {member.last_name}
                </h1>

                <span
                  className={[
                    "rounded-full border px-3 py-1 text-xs font-bold",
                    roleClass(
                      member.role,
                    ),
                  ].join(" ")}
                >
                  {roleLabel(
                    member.role,
                  )}
                </span>

                <span
                  className={[
                    "rounded-full border px-3 py-1 text-xs font-bold",
                    statusClass(
                      member.status,
                    ),
                  ].join(" ")}
                >
                  {statusLabel(
                    member.status,
                  )}
                </span>
              </div>

              <p className="mt-2 text-sm text-slate-500">
                {member.email}
              </p>
            </div>
          </div>
        </div>

        <AdminMemberEditForm
          key={member.member_id}
          member={member}
          memberId={memberId}
          currentUserId={
            currentUser?.id
          }
        />
      </div>
    </section>
  );
}