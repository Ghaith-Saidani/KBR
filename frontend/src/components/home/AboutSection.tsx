import { Link } from "react-router-dom";

const values = [
  {
    number: "01",
    title: "Esports",
    description:
      "Promouvoir la pratique et la culture de l'Esports à Bizerte et en Tunisie.",
  },
  {
    number: "02",
    title: "Compétition",
    description:
      "Accompagner les passionnés et les joueurs dans leur participation aux compétitions officielles.",
  },
  {
    number: "03",
    title: "Communauté",
    description:
      "Créer une communauté soudée autour des sports électroniques et de la passion du gaming.",
  },
];

export default function AboutSection() {
  return (
    <section className="border-t border-white/10 bg-[#0A0A0A] py-24 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-16 lg:grid-cols-[1fr_1.2fr] lg:items-center">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.25em] text-[#F5C400]">
              À propos de KBR
            </p>

            <h2 className="mt-4 max-w-xl text-4xl font-black tracking-tight text-white sm:text-5xl">
              L'Esports tunisien commence aussi à{" "}
              <span className="text-[#F5C400]">Bizerte.</span>
            </h2>

            <div className="mt-6 h-1 w-16 rounded-full bg-[#F5C400]" />
          </div>

          <div>
            <p className="text-lg leading-8 text-white/70">
              Knights of Bizertin Rise est un club Esports basé à Bizerte.
              Notre objectif est de promouvoir les sports électroniques et de
              permettre aux passionnés de participer aux différents événements
              officiels organisés en Tunisie et à l'international.
            </p>

            <p className="mt-5 text-base leading-7 text-white/50">
              KBR rassemble joueurs, passionnés et membres de la communauté
              autour d'une même ambition : développer l'Esports local et
              représenter Bizerte au-delà de ses frontières.
            </p>

            <Link
              to="/about"
              className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
            >
              Découvrir KBR
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>

        <div className="mt-20 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-3">
          {values.map((value) => (
            <div
              key={value.number}
              className="bg-[#121212] p-8 transition hover:bg-[#181818]"
            >
              <span className="text-sm font-bold text-[#F5C400]">
                {value.number}
              </span>

              <h3 className="mt-6 text-xl font-bold text-white">
                {value.title}
              </h3>

              <p className="mt-3 text-sm leading-6 text-white/50">
                {value.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}