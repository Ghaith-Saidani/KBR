import { Link } from "react-router-dom";

export default function EventsPreview() {
  return (
    <section className="bg-[#0B0B0B] py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#F5C400]">
              Compétitions
            </p>

            <h2 className="mt-3 text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
              Prochains événements
            </h2>
          </div>

          <Link
            to="/events"
            className="font-bold text-[#F5C400] transition hover:text-[#FFD21A]"
          >
            Voir tous les événements →
          </Link>
        </div>

        <div className="mt-12 rounded-2xl border border-dashed border-white/15 bg-[#050505] px-6 py-16 text-center">
          <p className="text-lg font-bold text-white">
            Les prochains événements KBR seront bientôt disponibles.
          </p>

          <p className="mx-auto mt-3 max-w-xl text-white/50">
            Cette section sera alimentée directement par la plateforme KBR
            lorsque les événements seront publiés.
          </p>
        </div>
      </div>
    </section>
  );
}
