import { Link } from "react-router-dom";

import { useMembers } from "../features/members/members.hooks";

function MemberCard({
  member,
}: {
  member: {
    id: string;
    first_name: string;
    last_name: string;
    slug: string;
    position: string | null;
    profile_image: string | null;
    bio: string | null;
  };
}) {
  const fullName = `${member.first_name} ${member.last_name}`;

  return (
    <article className="group overflow-hidden rounded-2xl border border-black/10 bg-white transition duration-300 hover:-translate-y-1 hover:shadow-xl">
      <div className="relative aspect-[4/3] overflow-hidden bg-[#111]">
        {member.profile_image ? (
          <img
            src={member.profile_image}
            alt={fullName}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-[#111]">
            <span className="text-5xl font-black text-[#F5C400]">
              {member.first_name.charAt(0)}
              {member.last_name.charAt(0)}
            </span>
          </div>
        )}

        <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 to-transparent" />
      </div>

      <div className="p-6">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#C39B00]">
          {member.position || "Membre KBR"}
        </p>

        <h2 className="mt-2 text-xl font-black text-[#0A0A0A]">
          {fullName}
        </h2>

        {member.bio && (
          <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500">
            {member.bio}
          </p>
        )}

        <Link
        to={`/members/${member.slug}`}
        className="inline-flex items-center rounded-lg bg-[#F5C400] px-4 py-2.5 text-sm font-bold text-[#050505] transition hover:bg-[#FFD21A]"
        >
        Voir le profil
        <span className="ml-1">→</span>
        </Link>
      </div>
    </article>
  );
}

export default function MembersPage() {
  const {
    data,
    isLoading,
    isError,
    isFetching,
  } = useMembers({
    status: "active",
    limit: 50,
  });

  if (isLoading) {
    return (
      <section className="min-h-[70vh] bg-slate-50 px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12">
            <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
            <div className="mt-4 h-12 w-72 animate-pulse rounded bg-slate-200" />
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div
                key={index}
                className="overflow-hidden rounded-2xl border border-black/5 bg-white"
              >
                <div className="aspect-[4/3] animate-pulse bg-slate-200" />

                <div className="space-y-3 p-6">
                  <div className="h-3 w-24 animate-pulse rounded bg-slate-200" />
                  <div className="h-6 w-40 animate-pulse rounded bg-slate-200" />
                  <div className="h-12 w-full animate-pulse rounded bg-slate-200" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-slate-50 px-6">
        <div className="max-w-md text-center">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#C39B00]">
            KBR
          </p>

          <h1 className="mt-3 text-3xl font-black text-[#0A0A0A]">
            Impossible de charger les membres
          </h1>

          <p className="mt-4 text-slate-500">
            Une erreur est survenue lors de la récupération
            des membres. Vérifiez que le backend KBR est bien
            démarré.
          </p>
        </div>
      </section>
    );
  }

  const members = data?.items ?? [];

  return (
    <section className="min-h-[70vh] bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#C39B00]">
            La communauté KBR
          </p>

          <h1 className="mt-4 text-4xl font-black tracking-tight text-[#0A0A0A] sm:text-5xl">
            Nos membres
          </h1>

          <p className="mt-5 text-lg leading-8 text-slate-500">
            Découvrez les membres actifs de Knights of Bizertin
            Rise et les passionnés qui font vivre notre
            communauté eSports.
          </p>
        </div>

        <div className="mt-12 flex items-center justify-between">
          <p className="text-sm font-semibold text-slate-500">
            {data?.total ?? 0} membre
            {(data?.total ?? 0) !== 1 ? "s" : ""}
          </p>

          {isFetching && (
            <p className="text-xs font-semibold text-slate-400">
              Mise à jour...
            </p>
          )}
        </div>

        {members.length === 0 ? (
          <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <h2 className="text-xl font-bold text-[#0A0A0A]">
              Aucun membre actif
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Les profils des membres apparaîtront ici.
            </p>
          </div>
        ) : (
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {members.map((member) => (
              <MemberCard
                key={member.id}
                member={member}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}