import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useMarkAllNotificationsAsRead,
  useMarkNotificationAsRead,
  useNotifications,
} from "../features/notifications/notifications.hooks";

import type {
  NotificationType,
} from "../features/notifications/notifications.types";

function formatDate(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function getTypeLabel(
  type: NotificationType,
) {
  switch (type) {
    case "success":
      return "Succès";

    case "warning":
      return "Attention";

    case "error":
      return "Erreur";

    case "info":
    default:
      return "Information";
  }
}

function getTypeClass(
  type: NotificationType,
) {
  switch (type) {
    case "success":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

    case "warning":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";

    case "error":
      return "border-red-500/20 bg-red-500/10 text-red-300";

    case "info":
    default:
      return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }
}

function getTypeDotClass(
  type: NotificationType,
) {
  switch (type) {
    case "success":
      return "bg-emerald-400";

    case "warning":
      return "bg-amber-400";

    case "error":
      return "bg-red-400";

    case "info":
    default:
      return "bg-blue-400";
  }
}

export default function NotificationsPage() {
  const [
    unreadOnly,
    setUnreadOnly,
  ] = useState(false);

  const {
    data,
    isLoading,
    isError,
  } = useNotifications({
    limit: 50,
    unread_only:
      unreadOnly,
  });

  const markAsRead =
    useMarkNotificationAsRead();

  const markAllAsRead =
    useMarkAllNotificationsAsRead();

  function handleMarkAsRead(
    notificationId: string,
  ) {
    markAsRead.mutate(
      notificationId,
    );
  }

  function handleMarkAllAsRead() {
    markAllAsRead.mutate();
  }

  return (
    <section className="min-h-[70vh] bg-[#050505] px-6 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <Link
              to="/account"
              className="text-sm font-semibold text-slate-500 transition hover:text-[#f5c400]"
            >
              ← Retour au compte
            </Link>

            <p className="mt-8 text-sm font-semibold uppercase tracking-[0.2em] text-[#f5c400]">
              KBR
            </p>

            <h1 className="mt-3 text-4xl font-black text-white sm:text-5xl">
              Notifications
            </h1>

            <p className="mt-4 max-w-2xl text-slate-400">
              Retrouvez vos dernières
              notifications et informations
              importantes.
            </p>
          </div>

          {data &&
            data.unread_count > 0 && (
              <div className="rounded-xl border border-[#f5c400]/20 bg-[#f5c400]/10 px-4 py-3">
                <p className="text-sm font-bold text-[#f5c400]">
                  {data.unread_count}{" "}
                  notification
                  {data.unread_count >
                  1
                    ? "s"
                    : ""}{" "}
                  non lue
                  {data.unread_count >
                  1
                    ? "s"
                    : ""}
                </p>
              </div>
            )}
        </div>

        <div className="mb-8 flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex rounded-xl border border-white/10 bg-[#0b0b0b] p-1">
            <button
              type="button"
              onClick={() =>
                setUnreadOnly(false)
              }
              className={[
                "rounded-lg px-4 py-2 text-sm font-semibold transition",
                !unreadOnly
                  ? "bg-[#f5c400] text-black"
                  : "text-slate-400 hover:text-white",
              ].join(" ")}
            >
              Toutes
            </button>

            <button
              type="button"
              onClick={() =>
                setUnreadOnly(true)
              }
              className={[
                "rounded-lg px-4 py-2 text-sm font-semibold transition",
                unreadOnly
                  ? "bg-[#f5c400] text-black"
                  : "text-slate-400 hover:text-white",
              ].join(" ")}
            >
              Non lues
            </button>
          </div>

          {data &&
            data.unread_count > 0 && (
              <button
                type="button"
                onClick={
                  handleMarkAllAsRead
                }
                disabled={
                  markAllAsRead.isPending
                }
                className="rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:border-[#f5c400]/40 hover:text-[#f5c400] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {markAllAsRead.isPending
                  ? "Traitement..."
                  : "Tout marquer comme lu"}
              </button>
            )}
        </div>

        {isLoading && (
          <div className="space-y-4">
            {Array.from({
              length: 5,
            }).map((_, index) => (
              <div
                key={index}
                className="animate-pulse rounded-2xl border border-white/10 bg-white/[0.04] p-6"
              >
                <div className="h-4 w-24 rounded bg-white/5" />

                <div className="mt-4 h-6 w-2/3 rounded bg-white/5" />

                <div className="mt-3 h-4 w-full rounded bg-white/5" />

                <div className="mt-2 h-4 w-4/5 rounded bg-white/5" />
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <h2 className="text-xl font-bold text-white">
              Impossible de charger les
              notifications
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Une erreur est survenue lors
              du chargement des notifications.
            </p>
          </div>
        )}

        {!isLoading &&
          !isError &&
          data?.items.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-2xl">
                ✓
              </div>

              <h2 className="mt-5 text-xl font-bold text-white">
                Aucune notification
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                {unreadOnly
                  ? "Vous n'avez aucune notification non lue."
                  : "Vous n'avez aucune notification pour le moment."}
              </p>
            </div>
          )}

        {!isLoading &&
          !isError &&
          data &&
          data.items.length > 0 && (
            <div className="space-y-4">
              {data.items.map(
                (notification) => (
                  <article
                    key={
                      notification.id
                    }
                    className={[
                      "rounded-2xl border p-6 transition",
                      notification.is_read
                        ? "border-white/10 bg-white/[0.03]"
                        : "border-[#f5c400]/20 bg-white/[0.05]",
                    ].join(" ")}
                  >
                    <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                      <div
                        className={[
                          "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border",
                          getTypeClass(
                            notification.type,
                          ),
                        ].join(" ")}
                      >
                        <span
                          className={[
                            "h-2.5 w-2.5 rounded-full",
                            getTypeDotClass(
                              notification.type,
                            ),
                          ].join(" ")}
                        />
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex flex-wrap items-center gap-3">
                            {!notification.is_read && (
                              <span className="h-2 w-2 rounded-full bg-[#f5c400]" />
                            )}

                            <h2 className="text-lg font-bold text-white">
                              {
                                notification.title
                              }
                            </h2>

                            <span
                              className={[
                                "rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
                                getTypeClass(
                                  notification.type,
                                ),
                              ].join(" ")}
                            >
                              {getTypeLabel(
                                notification.type,
                              )}
                            </span>
                          </div>

                          <time className="shrink-0 text-xs text-slate-600">
                            {formatDate(
                              notification.created_at,
                            )}
                          </time>
                        </div>

                        <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-400">
                          {
                            notification.message
                          }
                        </p>

                        {!notification.is_read && (
                          <button
                            type="button"
                            onClick={() =>
                              handleMarkAsRead(
                                notification.id,
                              )
                            }
                            disabled={
                              markAsRead.isPending
                            }
                            className="mt-5 text-sm font-bold text-[#f5c400] transition hover:text-[#ffd21a] disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {markAsRead.isPending
                              ? "Traitement..."
                              : "Marquer comme lu →"}
                          </button>
                        )}
                      </div>
                    </div>
                  </article>
                ),
              )}
            </div>
          )}
      </div>
    </section>
  );
}