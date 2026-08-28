import { Link } from "react-router-dom";

import { useAdminDashboard } from "../features/admin/admin.hooks";

interface StatCardProps {
  label: string;
  value: number;
  description: string;
}

function StatCard({
  label,
  value,
  description,
}: StatCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition hover:border-white/20 hover:bg-white/[0.055]">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-4xl font-black tracking-tight text-white">
        {value}
      </p>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>
    </div>
  );
}

interface ManagementCardProps {
  eyebrow: string;
  title: string;
  description: string;
  href: string;
  action: string;
}

function ManagementCard({
  eyebrow,
  title,
  description,
  href,
  action,
}: ManagementCardProps) {
  return (
    <div className="group rounded-2xl border border-white/10 bg-white/[0.04] p-6 transition hover:border-[#f5c400]/30 hover:bg-white/[0.055]">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
        {eyebrow}
      </p>

      <h3 className="mt-2 text-xl font-black text-white">
        {title}
      </h3>

      <p className="mt-3 text-sm leading-6 text-slate-500">
        {description}
      </p>

      <Link
        to={href}
        className="mt-5 inline-flex items-center rounded-xl border border-white/10 px-4 py-2.5 text-sm font-bold text-slate-300 transition hover:border-[#f5c400]/30 hover:bg-[#f5c400]/10 hover:text-white"
      >
        {action}
        <span className="ml-2 transition-transform group-hover:translate-x-1">
          →
        </span>
      </Link>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl animate-pulse">
        <div className="h-4 w-32 rounded bg-white/10" />

        <div className="mt-3 h-10 w-72 rounded bg-white/10" />

        <div className="mt-3 h-5 w-full max-w-xl rounded bg-white/10" />

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={`member-skeleton-${index}`}
              className="h-40 rounded-2xl border border-white/10 bg-white/[0.04]"
            />
          ))}
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={`user-skeleton-${index}`}
              className="h-40 rounded-2xl border border-white/10 bg-white/[0.04]"
            />
          ))}
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={`management-skeleton-${index}`}
              className="h-48 rounded-2xl border border-white/10 bg-white/[0.04]"
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function DashboardError() {
  return (
    <section className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
      <div className="max-w-md text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/10 text-2xl font-black text-red-300">
          !
        </div>

        <h1 className="mt-5 text-2xl font-black">
          Impossible de charger le tableau de bord
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          Votre session administrateur est peut-être
          expirée ou le serveur est momentanément
          indisponible.
        </p>

        <Link
          to="/"
          className="mt-6 inline-flex rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/5"
        >
          Retour à l'accueil
        </Link>
      </div>
    </section>
  );
}

export default function AdminDashboardPage() {
  const {
    data,
    isLoading,
    isError,
  } = useAdminDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (isError || !data) {
    return <DashboardError />;
  }

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              Tableau de bord
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              Vue d'ensemble des comptes, membres et
              activités de KBR.
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
              className="rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-[#050505] transition hover:bg-[#ffd21a]"
            >
              Créer un événement
            </Link>
          </div>
        </div>

        {/* Members */}
        <section>
          <div className="mb-4">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Membres
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              État des membres
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Vue actuelle des comptes membres KBR.
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
        </section>

        {/* Users */}
        <section className="mt-10">
          <div className="mb-4">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Utilisateurs
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Répartition des comptes
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Répartition des utilisateurs selon leur rôle.
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
        </section>

        {/* Management */}
        <section className="mt-10">
          <div className="mb-5">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Gestion
            </p>

            <h2 className="mt-1 text-lg font-black text-white">
              Administration KBR
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Accédez rapidement aux différentes sections
              d'administration.
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">

            <ManagementCard
              eyebrow="Analyse"
              title="Statistiques"
              description="Analysez les membres, utilisateurs, événements, activités et actualités de KBR à travers des indicateurs et tendances."
              href="/admin/statistics"
              action="Voir les statistiques"
            />

            <ManagementCard
              eyebrow="Membres"
              title="Gestion des membres"
              description="Recherchez les membres, consultez leurs profils, modifiez leurs informations, gérez leurs rôles et contrôlez l'état de leurs comptes."
              href="/admin/members"
              action="Gérer les membres"
            />

            <ManagementCard
              eyebrow="Événements"
              title="Gestion des événements"
              description="Créez, modifiez, publiez, annulez et supprimez les événements de KBR."
              href="/admin/events"
              action="Gérer les événements"
            />

            <ManagementCard
              eyebrow="Actualités"
              title="Gestion des actualités"
              description="Créez et gérez les articles publiés sur le site officiel de KBR."
              href="/admin/news"
              action="Gérer les actualités"
            />

            <ManagementCard
              eyebrow="Activités"
              title="Gestion des activités"
              description="Gérez les activités et projets présentés par KBR à sa communauté."
              href="/admin/activities"
              action="Gérer les activités"
            />

            <ManagementCard
              eyebrow="Messages"
              title="Messages de contact"
              description="Consultez les demandes envoyées depuis le formulaire de contact et gérez leur traitement."
              href="/admin/contact"
              action="Voir les messages"
            />

            <ManagementCard
              eyebrow="Système"
              title="Notifications"
              description="Surveillez les notifications et les communications importantes liées aux comptes KBR."
              href="/notifications"
              action="Voir les notifications"
            />
          </div>
        </section>

        {/* Quick actions */}
        <section className="mt-10">
          <div className="rounded-2xl border border-[#f5c400]/20 bg-[#f5c400]/[0.04] p-6 sm:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#f5c400]">
                  Actions rapides
                </p>

                <h2 className="mt-2 text-xl font-black text-white">
                  Administrer KBR
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                  Utilisez les outils d'administration pour
                  maintenir les comptes et le contenu du site
                  à jour.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link
                  to="/admin/members"
                  className="rounded-xl bg-[#f5c400] px-5 py-3 text-sm font-bold text-[#050505] transition hover:bg-[#ffd21a]"
                >
                  Membres
                </Link>

                <Link
                  to="/admin/events"
                  className="rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/5"
                >
                  Événements
                </Link>

                <Link
                  to="/"
                  className="rounded-xl border border-white/10 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/5"
                >
                  Voir le site
                </Link>
              </div>
            </div>
          </div>
        </section>
      </div>
    </section>
  );
}