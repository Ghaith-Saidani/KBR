import { Link } from "react-router-dom";
import Logo from "../ui/Logo";

export default function Footer() {
  return (
    <footer className="bg-[#050505] text-white">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <Logo dark />

            <p className="mt-6 max-w-lg text-sm leading-7 text-white/50">
              Knights of Bizertin Rise est un club eSports basé à Bizerte.
              KBR a pour objectif de promouvoir les sports électroniques et
              d'accompagner les passionnés vers les événements officiels en
              Tunisie et à l'international.
            </p>

            <div className="mt-6 h-1 w-12 rounded-full bg-[#F5C400]" />
          </div>

          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              Navigation
            </h2>

            <div className="mt-5 flex flex-col gap-3 text-sm text-white/50">
              <Link className="transition hover:text-[#F5C400]" to="/">
                Accueil
              </Link>

              <Link className="transition hover:text-[#F5C400]" to="/about">
                Le club
              </Link>

              <Link className="transition hover:text-[#F5C400]" to="/members">
                Équipes
              </Link>

              <Link className="transition hover:text-[#F5C400]" to="/events">
                Événements
              </Link>

              <Link className="transition hover:text-[#F5C400]" to="/news">
                Actualités
              </Link>
            </div>
          </div>

          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              KBR
            </h2>

            <div className="mt-5 flex flex-col gap-3 text-sm text-white/50">
              <Link className="transition hover:text-[#F5C400]" to="/activities">
                Activités
              </Link>

              <Link className="transition hover:text-[#F5C400]" to="/contact">
                Contact
              </Link>

              <Link className="transition hover:text-[#F5C400]" to="/login">
                Espace membre
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-white/10 pt-6 text-sm text-white/40 sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {new Date().getFullYear()} Knights of Bizertin Rise.
          </p>

          <p>
            Bizerte · Tunisie · eSports
          </p>
        </div>
      </div>
    </footer>
  );
}
