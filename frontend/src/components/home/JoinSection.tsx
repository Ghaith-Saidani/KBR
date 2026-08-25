import { Link } from "react-router-dom";

export default function JoinSection() {
  return (
    <section className="bg-[#F5C400]">
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-10 lg:flex-row lg:items-center">
          <div className="max-w-3xl">
            <p className="text-sm font-black uppercase tracking-[0.2em] text-black/60">
              Rejoindre KBR
            </p>

            <h2 className="mt-4 text-4xl font-black uppercase tracking-tight text-[#050505] sm:text-5xl">
              Prêt à entrer dans l'arène ?
            </h2>

            <p className="mt-5 max-w-2xl text-lg leading-8 text-black/65">
              KBR rassemble les passionnés d'eSports autour de la
              compétition, de la communauté et de l'ambition.
            </p>
          </div>

          <Link
            to="/contact"
            className="inline-flex shrink-0 items-center justify-center rounded-lg bg-[#050505] px-7 py-4 font-bold text-white transition hover:bg-[#151515]"
          >
            Contacter KBR
          </Link>
        </div>
      </div>
    </section>
  );
}
