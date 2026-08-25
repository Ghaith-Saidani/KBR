import { Link, useParams } from "react-router-dom";

import { useMemberBySlug } from "../features/members/members.hooks";

export default function MemberProfilePage() {
  const { slug } = useParams();

  const {
    data: member,
    isLoading,
    isError,
  } = useMemberBySlug(slug);

  if (isLoading) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-slate-50">
        <p className="text-sm font-semibold text-slate-500">
          Chargement du profil...
        </p>
      </section>
    );
  }

  if (isError || !member) {
    return (
      <section className="flex min-h-[70vh] items-center justify-center bg-slate-50 px-6">
        <div className="text-center">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#C39B00]">
            KBR
          </p>

          <h1 className="mt-3 text-3xl font-black text-[#0A0A0A]">
            Membre introuvable
          </h1>

          <p className="mt-3 text-slate-500">
            Ce profil n'existe pas ou n'est plus disponible.
          </p>

          <Link
            to="/members"
            className="mt-6 inline-flex rounded-xl bg-[#F5C400] px-6 py-3 text-sm font-bold text-[#0A0A0A]"
          >
            Retour aux membres
          </Link>
        </div>
      </section>
    );
  }

  const fullName = `${member.first_name} ${member.last_name}`;

  return (
    <section className="min-h-[70vh] bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <Link
        to="/members"
        className="inline-flex items-center rounded-lg border border-[#F5C400] bg-[#F5C400]/45 px-4 py-2.5 text-sm font-bold text-[#050505] transition hover:bg-[#F5C400] hover:text-[#050505]"
        >
        ← Retour aux membres
        </Link>

        <div className="mt-8 overflow-hidden rounded-3xl border border-black/10 bg-white">
          <div className="grid md:grid-cols-[320px_1fr]">
            <div className="aspect-square bg-[#111] md:aspect-auto">
              {member.profile_image ? (
                <img
                  src={member.profile_image}
                  alt={fullName}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full min-h-[320px] items-center justify-center">
                  <span className="text-7xl font-black text-[#F5C400]">
                    {member.first_name.charAt(0)}
                    {member.last_name.charAt(0)}
                  </span>
                </div>
              )}
            </div>

            <div className="p-8 sm:p-10">
              <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#C39B00]">
                {member.position || "Membre KBR"}
              </p>

              <h1 className="mt-3 text-4xl font-black tracking-tight text-[#0A0A0A]">
                {fullName}
              </h1>

              {member.bio && (
                <p className="mt-6 text-base leading-8 text-slate-500">
                  {member.bio}
                </p>
              )}

              <div className="mt-8 border-t border-black/10 pt-6">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Membre depuis
                </p>

                <p className="mt-2 font-semibold text-[#0A0A0A]">
                  {member.joined_at
                    ? new Intl.DateTimeFormat("fr-FR", {
                        dateStyle: "long",
                      }).format(
                        new Date(member.joined_at),
                      )
                    : "Date non renseignée"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}