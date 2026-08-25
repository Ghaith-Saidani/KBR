import { Link } from "react-router-dom";

import { useAdminDashboard } from "../features/admin/admin.hooks";

function StatCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-4xl font-black text-white">
        {value}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>
    </div>
  );
}

export default function AdminDashboardPage() {
  const {
    data,
    isLoading,
    isError,
  } = useAdminDashboard();

  if (isLoading) {
    return (
      <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
        <div className="mx-auto max-w-7xl">
          <div className="animate-pulse">
            <div className="h-4 w-32 rounded bg-white/10" />

            <div className="mt-3 h-10 w-72 rounded bg-white/10" />

            <div className="mt-3 h-5 w-96 max-w-full rounded bg-white/10" />
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({
              length: 4,
            }).map((_, index) => (
              <div
                key={index}
                className="h-40 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
              />
            ))}
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({
              length: 4,
            }).map((_, index) => (
              <div
                key={index}
                className="h-40 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]"
              />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="max-w-md text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/10 text-2xl">
            !
          </div>

          <h1 className="mt-5 text-2xl font-black">
            Impossible de charger le tableau de bord
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            Vérifiez votre session administrateur et
            réessayez.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black sm:text-4xl">
              Tableau de bord
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Vue d'ensemble de l'activité et des
              comptes KBR.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              to="/admin/members"
              className="rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              Gérer les membres
            </Link>

            <Link
              to="/admin/events"
              className="rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-black transition hover:bg-[#ffd21a]"
            >
              Gérer les événements
            </Link>
          </div>
        </div>

        <div>
          <div className="mb-4">
            <h2 className="text-lg font-black">
              Membres
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              État actuel des membres KBR.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total"
              value={data.members.total}
              description="Membres enregistrés"
            />

            <StatCard
              label="Actifs"
              value={data.members.active}
              description="Comptes actifs"
            />

            <StatCard
              label="En attente"
              value={data.members.pending}
              description="Comptes à activer"
            />

            <StatCard
              label="Suspendus"
              value={data.members.suspended}
              description="Comptes suspendus"
            />
          </div>
        </div>

        <div className="mt-10">
          <div className="mb-4">
            <h2 className="text-lg font-black">
              Utilisateurs
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Répartition des comptes par rôle.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total"
              value={data.users.total}
              description="Utilisateurs enregistrés"
            />

            <StatCard
              label="Membres"
              value={data.users.members}
              description="Rôle membre"
            />

            <StatCard
              label="Staff"
              value={data.users.staff}
              description="Rôle staff"
            />

            <StatCard
              label="Administrateurs"
              value={data.users.admins}
              description="Rôle administrateur"
            />
          </div>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
              Membres
            </p>

            <h2 className="mt-2 text-xl font-black">
              Gestion des membres
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              Recherchez les membres, modifiez leurs
              informations, gérez leurs rôles et
              contrôlez l'état de leurs comptes.
            </p>

            <Link
              to="/admin/members"
              className="mt-5 inline-flex rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              Ouvrir la gestion →
            </Link>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
              Événements
            </p>

            <h2 className="mt-2 text-xl font-black">
              Gestion des événements
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              Créez, modifiez, publiez, annulez ou
              supprimez les événements KBR.
            </p>

            <Link
              to="/admin/events"
              className="mt-5 inline-flex rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
            >
              Ouvrir la gestion →
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}