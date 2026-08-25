import { Link } from "react-router-dom";

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-[#050505]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_75%_35%,rgba(245,196,0,0.12),transparent_35%)]" />

      <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl items-center px-4 py-20 sm:px-6 lg:px-8">
        <div className="max-w-4xl">
          <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-[#F5C400]/30 bg-[#F5C400]/5 px-4 py-2">
            <span className="h-2 w-2 rounded-full bg-[#F5C400]" />
            <span className="text-sm font-semibold uppercase tracking-[0.2em] text-[#F5C400]">
              Club eSports · Bizerte · Tunisie
            </span>
          </div>

          <h1 className="text-5xl font-black uppercase leading-[0.95] tracking-tight text-white sm:text-6xl lg:text-8xl">
            Knights of
            <span className="block text-[#F5C400]">
              Bizertin Rise
            </span>
          </h1>

          <p className="mt-8 max-w-2xl text-lg leading-8 text-white/65 sm:text-xl">
            Un club eSports basé à Bizerte, dédié à la passion du jeu
            compétitif, au développement des talents et à la participation
            aux événements officiels en Tunisie et à l'international.
          </p>

          <div className="mt-10 flex flex-col gap-4 sm:flex-row">
            <Link
              to="/events"
              className="kbr-button-primary"
            >
              Découvrir les événements
            </Link>

            <Link
              to="/about"
              className="kbr-button-secondary"
            >
              Découvrir KBR
            </Link>
          </div>

          <div className="mt-14 flex flex-wrap gap-x-10 gap-y-4 border-t border-white/10 pt-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-white/40">
                Base
              </p>
              <p className="mt-1 font-bold text-white">
                Bizerte, Tunisie
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-white/40">
                Ambition
              </p>
              <p className="mt-1 font-bold text-white">
                Tunisie & International
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-white/40">
                Univers
              </p>
              <p className="mt-1 font-bold text-[#F5C400]">
                eSports
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
