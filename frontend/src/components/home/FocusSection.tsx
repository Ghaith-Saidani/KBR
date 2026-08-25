const focuses = [
  {
    number: "01",
    title: "Compétition",
    description:
      "Développer l'esprit compétitif et permettre aux joueurs de participer à des événements eSports officiels.",
  },
  {
    number: "02",
    title: "Communauté",
    description:
      "Rassembler les passionnés d'eSports à Bizerte et créer une communauté active autour du gaming.",
  },
  {
    number: "03",
    title: "Rayonnement",
    description:
      "Porter les couleurs de KBR au-delà de Bizerte, en Tunisie et sur la scène internationale.",
  },
];

export default function FocusSection() {
  return (
    <section className="bg-[#050505] py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F5C400]">
            Notre vision
          </p>

          <h2 className="mt-4 text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
            Construire la prochaine
            <span className="block text-[#F5C400]">
              génération eSports.
            </span>
          </h2>
        </div>

        <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-3">
          {focuses.map((focus) => (
            <article
              key={focus.number}
              className="bg-[#0B0B0B] p-8 transition hover:bg-[#121212]"
            >
              <span className="text-sm font-black text-[#F5C400]">
                {focus.number}
              </span>

              <h3 className="mt-8 text-2xl font-black uppercase text-white">
                {focus.title}
              </h3>

              <p className="mt-4 leading-7 text-white/55">
                {focus.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
