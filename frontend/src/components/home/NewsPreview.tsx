import { Link } from "react-router-dom";

export default function NewsPreview() {
  return (
    <section className="bg-[#050505] py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F5C400]">
              Actualités
            </p>

            <h2 className="mt-3 text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
              La vie de KBR
            </h2>
          </div>

          <Link
            to="/news"
            className="font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
          >
            Toutes les actualités →
          </Link>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <article
              key={item}
              className="min-h-64 rounded-2xl border border-white/10 bg-[#0B0B0B] p-7"
            >
              <div className="h-2 w-12 rounded-full bg-[#F5C400]" />

              <p className="mt-12 text-sm font-semibold uppercase tracking-wider text-white/35">
                KBR News
              </p>

              <h3 className="mt-3 text-xl font-black text-white">
                Les actualités KBR seront bientôt disponibles.
              </h3>

              <p className="mt-3 text-sm leading-6 text-white/45">
                Les publications officielles du club apparaîtront ici.
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
