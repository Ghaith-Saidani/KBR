import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import Logo from "../ui/Logo";

const navigation = [
  { label: "Accueil", to: "/" },
  { label: "Le club", to: "/about" },
  { label: "Équipes", to: "/members" },
  { label: "Événements", to: "/events" },
  { label: "Activités", to: "/activities" },
  { label: "Actualités", to: "/news" },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#050505]/95 backdrop-blur">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo dark />

        <nav className="hidden items-center gap-1 lg:flex">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "rounded-lg px-3 py-2 text-sm font-semibold transition",
                  isActive
                    ? "text-[#F5C400]"
                    : "text-white/70 hover:text-white",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Link
            to="/contact"
            className="px-3 py-2 text-sm font-semibold text-white/70 transition hover:text-white"
          >
            Contact
          </Link>

          <Link
            to="/login"
            className="rounded-lg bg-[#F5C400] px-5 py-2.5 text-sm font-bold text-[#050505] transition hover:bg-[#FFD21A]"
          >
            Espace membre
          </Link>
        </div>

        <button
          type="button"
          aria-label={isOpen ? "Fermer le menu" : "Ouvrir le menu"}
          aria-expanded={isOpen}
          onClick={() => setIsOpen((current) => !current)}
          className="rounded-lg p-2 text-white transition hover:bg-white/10 lg:hidden"
        >
          <span className="block h-0.5 w-6 bg-current" />
          <span className="mt-1.5 block h-0.5 w-6 bg-current" />
          <span className="mt-1.5 block h-0.5 w-6 bg-current" />
        </button>
      </div>

      {isOpen && (
        <div className="border-t border-white/10 bg-[#0B0B0B] lg:hidden">
          <nav className="mx-auto flex max-w-7xl flex-col px-4 py-3 sm:px-6">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  [
                    "rounded-lg px-3 py-3 text-sm font-semibold transition",
                    isActive
                      ? "bg-[#F5C400] text-[#050505]"
                      : "text-white/70 hover:bg-white/5 hover:text-white",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}

            <div className="mt-2 flex flex-col gap-2 border-t border-white/10 pt-3">
              <Link
                to="/contact"
                onClick={() => setIsOpen(false)}
                className="rounded-lg px-3 py-3 text-sm font-semibold text-white/70 hover:bg-white/5 hover:text-white"
              >
                Contact
              </Link>

              <Link
                to="/login"
                onClick={() => setIsOpen(false)}
                className="rounded-lg bg-[#F5C400] px-3 py-3 text-center text-sm font-bold text-[#050505]"
              >
                Espace membre
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
