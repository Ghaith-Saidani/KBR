import { Link } from "react-router-dom";

const values = [
  {
    number: "01",
    title: "Compétition",
    description:
      "Développer l'esprit compétitif et donner aux joueurs les moyens de progresser et de participer à des compétitions officielles.",
  },
  {
    number: "02",
    title: "Communauté",
    description:
      "Créer une communauté soudée autour de l'eSports, du gaming et des valeurs qui nous rassemblent à Bizerte.",
  },
  {
    number: "03",
    title: "Développement",
    description:
      "Accompagner les talents, encourager la progression et construire un environnement dans lequel chaque membre peut évoluer.",
  },
  {
    number: "04",
    title: "Rayonnement",
    description:
      "Porter les couleurs de Bizerte et de KBR sur les scènes tunisienne et internationale.",
  },
];

const pillars = [
  {
    number: "01",
    title: "Joueurs",
    description:
      "Identifier, accompagner et développer les joueurs qui souhaitent évoluer dans un environnement compétitif.",
  },
  {
    number: "02",
    title: "Équipes",
    description:
      "Construire des équipes organisées capables de représenter KBR dans différentes compétitions.",
  },
  {
    number: "03",
    title: "Événements",
    description:
      "Participer aux événements eSports et créer des opportunités de rencontre pour la communauté.",
  },
  {
    number: "04",
    title: "Communauté",
    description:
      "Rassembler les passionnés autour d'une identité commune et faire grandir la scène eSports locale.",
  },
];

export default function AboutPage() {
  return (
    <div className="bg-[#050505] text-white">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_75%_35%,rgba(245,196,0,0.14),transparent_32%)]" />

        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8 lg:py-40">
          <div className="max-w-5xl">
            <p className="text-sm font-bold uppercase tracking-[0.3em] text-[#F5C400]">
              À propos de KBR
            </p>

            <h1 className="mt-5 text-5xl font-black uppercase leading-[0.92] tracking-tight sm:text-7xl lg:text-8xl">
              Built in
              <span className="block text-[#F5C400]">
                Bizerte.
              </span>
              Driven by
              <span className="block">
                competition.
              </span>
            </h1>

            <p className="mt-8 max-w-2xl text-lg leading-8 text-white/60 sm:text-xl">
              Knights of Bizertin Rise est un club eSports basé à
              Bizerte, créé autour d'une ambition simple : faire
              grandir la pratique des sports électroniques et donner
              aux passionnés les moyens de progresser.
            </p>
          </div>
        </div>
      </section>

      {/* Introduction */}
      <section className="border-b border-white/10 bg-[#0A0A0A] py-24 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-14 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
                Notre identité
              </p>

              <h2 className="mt-4 text-4xl font-black uppercase tracking-tight sm:text-5xl">
                Plus qu'un club.
                <span className="block text-[#F5C400]">
                  Une ambition.
                </span>
              </h2>
            </div>

            <div className="max-w-3xl">
              <p className="text-xl leading-9 text-white/75">
                KBR rassemble des joueurs, des passionnés et des
                membres de la communauté autour d'une même vision :
                construire une scène eSports ambitieuse à Bizerte
                et contribuer à son développement en Tunisie.
              </p>

              <p className="mt-6 leading-8 text-white/50">
                Nous voulons créer un environnement dans lequel les
                joueurs peuvent se développer, les équipes peuvent
                performer et la communauté peut se retrouver autour
                d'une passion commune pour la compétition et le
                gaming.
              </p>

              <p className="mt-6 leading-8 text-white/50">
                Notre objectif dépasse les résultats d'une seule
                compétition. KBR souhaite construire une identité
                durable et représenter Bizerte avec ambition sur la
                scène eSports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="bg-[#050505] py-24 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
              Nos valeurs
            </p>

            <h2 className="mt-4 text-4xl font-black uppercase tracking-tight sm:text-5xl">
              Ce qui fait
              <span className="block text-[#F5C400]">
                KBR.
              </span>
            </h2>

            <p className="mt-5 leading-7 text-white/50">
              Une identité construite autour de la performance,
              de la progression et de la communauté.
            </p>
          </div>

          <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-2 lg:grid-cols-4">
            {values.map((value) => (
              <article
                key={value.number}
                className="bg-[#0B0B0B] p-8 transition hover:bg-[#141414]"
              >
                <span className="text-sm font-black text-[#F5C400]">
                  {value.number}
                </span>

                <h3 className="mt-8 text-2xl font-black uppercase">
                  {value.title}
                </h3>

                <p className="mt-4 text-sm leading-7 text-white/50">
                  {value.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="border-y border-white/10 bg-[#0A0A0A] py-24 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-14 lg:grid-cols-[1fr_1.3fr] lg:items-center">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
                Notre mission
              </p>

              <h2 className="mt-4 text-4xl font-black uppercase tracking-tight sm:text-5xl">
                Donner une place
                <span className="block text-[#F5C400]">
                  aux talents.
                </span>
              </h2>
            </div>

            <div>
              <p className="text-xl leading-9 text-white/70">
                Nous voulons contribuer à la professionnalisation
                de l'eSports en créant les conditions nécessaires
                pour que les joueurs puissent progresser et
                représenter KBR dans les meilleures conditions.
              </p>

              <div className="mt-10 grid gap-4 sm:grid-cols-2">
                {[
                  "Développer les joueurs",
                  "Construire des équipes compétitives",
                  "Participer aux compétitions",
                  "Faire grandir la communauté",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-3 border border-white/10 bg-[#121212] px-5 py-4"
                  >
                    <span className="h-2 w-2 shrink-0 rounded-full bg-[#F5C400]" />
                    <span className="text-sm font-semibold text-white/75">
                      {item}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* KBR ecosystem */}
      <section className="bg-[#050505] py-24 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
                L'écosystème KBR
              </p>

              <h2 className="mt-4 text-4xl font-black uppercase tracking-tight sm:text-5xl">
                Une organisation
                <span className="block text-[#F5C400]">
                  en mouvement.
                </span>
              </h2>
            </div>

            <p className="max-w-md text-sm leading-6 text-white/40">
              Des joueurs aux événements, chaque partie de KBR
              participe à la construction du club.
            </p>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-2">
            {pillars.map((pillar) => (
              <article
                key={pillar.number}
                className="group rounded-2xl border border-white/10 bg-[#0B0B0B] p-8 transition hover:border-[#F5C400]/30 hover:bg-[#101010]"
              >
                <div className="flex items-start justify-between gap-6">
                  <span className="text-sm font-black text-[#F5C400]">
                    {pillar.number}
                  </span>

                  <span className="text-2xl text-white/10 transition group-hover:text-[#F5C400]/40">
                    ↗
                  </span>
                </div>

                <h3 className="mt-12 text-2xl font-black uppercase">
                  {pillar.title}
                </h3>

                <p className="mt-4 max-w-xl leading-7 text-white/50">
                  {pillar.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Closing statement */}
      <section className="bg-[#F5C400]">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 sm:py-24">
          <div className="flex flex-col justify-between gap-10 lg:flex-row lg:items-center">
            <div className="max-w-3xl">
              <p className="text-sm font-black uppercase tracking-[0.25em] text-black/60">
                La suite commence maintenant
              </p>

              <h2 className="mt-4 text-4xl font-black uppercase tracking-tight text-[#050505] sm:text-5xl">
                Prêt à rejoindre l'aventure KBR ?
              </h2>

              <p className="mt-5 max-w-2xl text-lg leading-8 text-black/60">
                Découvrez nos équipes, nos événements et les
                dernières actualités du club.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row lg:shrink-0">
              <Link
                to="/members"
                className="inline-flex items-center justify-center rounded-lg bg-[#050505] px-7 py-4 font-bold text-white transition hover:bg-[#151515]"
              >
                Nos équipes
              </Link>

              <Link
                to="/contact"
                className="inline-flex items-center justify-center rounded-lg border border-black/20 px-7 py-4 font-bold text-[#050505] transition hover:bg-black/10"
              >
                Contacter KBR
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}