import { useState } from "react";
import {
  Link,
  NavLink,
} from "react-router-dom";

import Logo from "../ui/Logo";
import { useAuthStore } from "../../stores/authStore";
import {
  useUnreadNotificationCount,
} from "../../features/notifications/notifications.hooks";

const navigation = [
  { label: "Accueil", to: "/" },
  { label: "Le club", to: "/about" },
  { label: "Équipes", to: "/members" },
  { label: "Événements", to: "/events" },
  { label: "Activités", to: "/activities" },
  { label: "Actualités", to: "/news" },
];

function NotificationBell() {
  const {
    data: unreadCount = 0,
  } = useUnreadNotificationCount();

  return (
    <Link
      to="/notifications"
      aria-label={
        unreadCount > 0
          ? `${unreadCount} notification${
              unreadCount > 1
                ? "s"
                : ""
            } non lue${
              unreadCount > 1
                ? "s"
                : ""
            }`
          : "Notifications"
      }
      className="relative flex h-10 w-10 items-center justify-center rounded-lg text-white/70 transition hover:bg-white/10 hover:text-white"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        className="h-5 w-5"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9a6 6 0 1 0-12 0v.75a8.967 8.967 0 0 1-2.31 6.022c1.74.64 3.59 1.08 5.454 1.31m5.713 0a24.255 24.255 0 0 1-5.713 0m5.713 0a3 3 0 1 1-5.713 0"
        />
      </svg>

      {unreadCount > 0 && (
        <span className="absolute right-0.5 top-0.5 flex min-h-4 min-w-4 items-center justify-center rounded-full bg-[#f5c400] px-1 text-[9px] font-black leading-none text-[#050505] ring-2 ring-[#050505]">
          {unreadCount > 99
            ? "99+"
            : unreadCount}
        </span>
      )}
    </Link>
  );
}

export default function Navbar() {
  const [isOpen, setIsOpen] =
    useState(false);

  const user = useAuthStore(
    (state) => state.user,
  );

  const isAuthenticated = Boolean(
    useAuthStore(
      (state) => state.accessToken,
    ),
  );

  const canAccessAdmin = Boolean(
    user &&
      (user.role === "admin" ||
        user.role === "staff"),
  );

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

          {canAccessAdmin && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                [
                  "rounded-lg px-3 py-2 text-sm font-semibold transition",
                  isActive
                    ? "text-[#F5C400]"
                    : "text-white/70 hover:text-white",
                ].join(" ")
              }
            >
              Administration
            </NavLink>
          )}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Link
            to="/contact"
            className="px-3 py-2 text-sm font-semibold text-white/70 transition hover:text-white"
          >
            Contact
          </Link>

          {isAuthenticated && (
            <NotificationBell />
          )}

          {isAuthenticated ? (
            <Link
              to="/account"
              className="rounded-lg bg-[#F5C400] px-5 py-2.5 text-sm font-bold text-[#050505] transition hover:bg-[#FFD21A]"
            >
              Mon compte
            </Link>
          ) : (
            <Link
              to="/login"
              className="rounded-lg bg-[#F5C400] px-5 py-2.5 text-sm font-bold text-[#050505] transition hover:bg-[#FFD21A]"
            >
              Espace membre
            </Link>
          )}
        </div>

        <div className="flex items-center gap-2 lg:hidden">
          {isAuthenticated && (
            <NotificationBell />
          )}

          <button
            type="button"
            aria-label={
              isOpen
                ? "Fermer le menu"
                : "Ouvrir le menu"
            }
            aria-expanded={isOpen}
            onClick={() =>
              setIsOpen(
                (current) => !current,
              )
            }
            className="rounded-lg p-2 text-white transition hover:bg-white/10"
          >
            <span className="block h-0.5 w-6 bg-current" />
            <span className="mt-1.5 block h-0.5 w-6 bg-current" />
            <span className="mt-1.5 block h-0.5 w-6 bg-current" />
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="border-t border-white/10 bg-[#0B0B0B] lg:hidden">
          <nav className="mx-auto flex max-w-7xl flex-col px-4 py-3 sm:px-6">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() =>
                  setIsOpen(false)
                }
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

            {canAccessAdmin && (
              <NavLink
                to="/admin"
                onClick={() =>
                  setIsOpen(false)
                }
                className={({ isActive }) =>
                  [
                    "rounded-lg px-3 py-3 text-sm font-semibold transition",
                    isActive
                      ? "bg-[#F5C400] text-[#050505]"
                      : "text-white/70 hover:bg-white/5 hover:text-white",
                  ].join(" ")
                }
              >
                Administration
              </NavLink>
            )}

            {isAuthenticated && (
              <Link
                to="/notifications"
                onClick={() =>
                  setIsOpen(false)
                }
                className="flex items-center justify-between rounded-lg px-3 py-3 text-sm font-semibold text-white/70 transition hover:bg-white/5 hover:text-white"
              >
                <span>
                  Notifications
                </span>

                <span className="text-xs text-slate-500">
                  Voir →
                </span>
              </Link>
            )}

            <div className="mt-2 flex flex-col gap-2 border-t border-white/10 pt-3">
              <Link
                to="/contact"
                onClick={() =>
                  setIsOpen(false)
                }
                className="rounded-lg px-3 py-3 text-sm font-semibold text-white/70 hover:bg-white/5 hover:text-white"
              >
                Contact
              </Link>

              {isAuthenticated ? (
                <Link
                  to="/account"
                  onClick={() =>
                    setIsOpen(false)
                  }
                  className="rounded-lg bg-[#F5C400] px-3 py-3 text-center text-sm font-bold text-[#050505]"
                >
                  Mon compte
                </Link>
              ) : (
                <Link
                  to="/login"
                  onClick={() =>
                    setIsOpen(false)
                  }
                  className="rounded-lg bg-[#F5C400] px-3 py-3 text-center text-sm font-bold text-[#050505]"
                >
                  Espace membre
                </Link>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}