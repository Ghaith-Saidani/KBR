import {
  useMemo,
  useState,
} from "react";

import {
  useAdminContactMessages,
  useDeleteContactMessage,
  useUpdateContactMessageStatus,
} from "../features/contact/contact.hooks";

import type {
  ContactMessage,
  ContactMessageStatus,
} from "../features/contact/contact.types";

function formatDate(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleDateString(
    "fr-FR",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  );
}

function formatDateTime(
  value: string,
) {
  return new Date(
    value,
  ).toLocaleString(
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

function statusLabel(
  status: ContactMessageStatus,
) {
  switch (status) {
    case "new":
      return "Nouveau";

    case "read":
      return "Lu";

    case "replied":
      return "Répondu";

    case "archived":
      return "Archivé";

    default:
      return status;
  }
}

function statusClass(
  status: ContactMessageStatus,
) {
  switch (status) {
    case "new":
      return "border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]";

    case "read":
      return "border-blue-500/20 bg-blue-500/10 text-blue-300";

    case "replied":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";

    case "archived":
      return "border-slate-500/20 bg-slate-500/10 text-slate-400";

    default:
      return "border-white/10 bg-white/5 text-slate-400";
  }
}

function MessageSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-white/10 bg-white/[0.04] p-5">
      <div className="flex gap-4">
        <div className="h-11 w-11 rounded-full bg-white/10" />

        <div className="flex-1">
          <div className="h-4 w-40 rounded bg-white/10" />

          <div className="mt-3 h-3 w-64 rounded bg-white/10" />

          <div className="mt-4 h-4 w-3/4 rounded bg-white/10" />

          <div className="mt-2 h-3 w-1/2 rounded bg-white/10" />
        </div>
      </div>
    </div>
  );
}

interface MessageModalProps {
  message: ContactMessage;
  onClose: () => void;
  onStatusChange: (
    status: ContactMessageStatus,
  ) => void;
  isUpdating: boolean;
}

function MessageModal({
  message,
  onClose,
  onStatusChange,
  isUpdating,
}: MessageModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-4 py-6 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
    >
      <div className="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-2xl border border-white/10 bg-[#0b0b0b] shadow-2xl">
        <div className="flex items-start justify-between border-b border-white/10 p-6">
          <div className="min-w-0 pr-6">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={[
                  "rounded-full border px-2.5 py-1 text-xs font-bold",
                  statusClass(
                    message.status,
                  ),
                ].join(" ")}
              >
                {statusLabel(
                  message.status,
                )}
              </span>

              <span className="text-xs text-slate-600">
                {formatDateTime(
                  message.created_at,
                )}
              </span>
            </div>

            <h2 className="mt-3 text-xl font-black text-white sm:text-2xl">
              {message.subject}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 text-lg text-slate-400 transition hover:bg-white/5 hover:text-white"
            aria-label="Fermer"
          >
            ×
          </button>
        </div>

        <div className="max-h-[calc(90vh-180px)] overflow-y-auto p-6">
          <div className="rounded-xl border border-white/10 bg-white/[0.025] p-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-bold text-white">
                  {message.name}
                </p>

                <a
                  href={`mailto:${message.email}`}
                  className="mt-1 block text-sm text-[#f5c400] hover:underline"
                >
                  {message.email}
                </a>
              </div>

              {message.user_id && (
                <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs font-bold text-blue-300">
                  Membre KBR
                </span>
              )}
            </div>
          </div>

          <div className="mt-6">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Message
            </p>

            <div className="whitespace-pre-wrap rounded-xl border border-white/10 bg-[#080808] p-5 text-sm leading-7 text-slate-300">
              {message.message}
            </div>
          </div>

          <div className="mt-6">
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Modifier le statut
            </p>

            <div className="flex flex-wrap gap-2">
              {(
                [
                  "new",
                  "read",
                  "replied",
                  "archived",
                ] as ContactMessageStatus[]
              ).map((status) => (
                <button
                  key={status}
                  type="button"
                  disabled={
                    isUpdating ||
                    message.status ===
                      status
                  }
                  onClick={() =>
                    onStatusChange(
                      status,
                    )
                  }
                  className={[
                    "rounded-lg border px-3 py-2 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-40",
                    message.status ===
                    status
                      ? statusClass(
                          status,
                        )
                      : "border-white/10 text-slate-400 hover:bg-white/5 hover:text-white",
                  ].join(" ")}
                >
                  {statusLabel(
                    status,
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end border-t border-white/10 p-5">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-white/10 px-5 py-2.5 text-sm font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminContactPage() {
  const [
    search,
    setSearch,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<
    "all" | ContactMessageStatus
  >("all");

  const [
    selectedMessage,
    setSelectedMessage,
  ] =
    useState<ContactMessage | null>(
      null,
    );

  const [
    deletingId,
    setDeletingId,
  ] = useState<string | null>(
    null,
  );

  const params = useMemo(
    () => ({
      search:
        search.trim() ||
        undefined,

      status:
        statusFilter === "all"
          ? undefined
          : statusFilter,

      skip: 0,
      limit: 50,
    }),
    [
      search,
      statusFilter,
    ],
  );

  const {
    data,
    isLoading,
    isError,
  } =
    useAdminContactMessages(
      params,
    );

  const updateMutation =
    useUpdateContactMessageStatus();

  const deleteMutation =
    useDeleteContactMessage();

  function handleOpenMessage(
    message: ContactMessage,
  ) {
    setSelectedMessage(message);

    if (
      message.status === "new"
    ) {
      updateMutation.mutate({
        messageId: message.id,
        status: "read",
      });
    }
  }

  function handleStatusChange(
    status: ContactMessageStatus,
  ) {
    if (!selectedMessage) {
      return;
    }

    updateMutation.mutate(
      {
        messageId:
          selectedMessage.id,
        status,
      },
      {
        onSuccess: (
          updatedMessage,
        ) => {
          setSelectedMessage(
            updatedMessage,
          );
        },
      },
    );
  }

  function handleDelete(
    message: ContactMessage,
  ) {
    const confirmed =
      window.confirm(
        `Supprimer définitivement le message de ${message.name} ?`,
      );

    if (!confirmed) {
      return;
    }

    setDeletingId(
      message.id,
    );

    deleteMutation.mutate(
      message.id,
      {
        onSuccess: () => {
          if (
            selectedMessage?.id ===
            message.id
          ) {
            setSelectedMessage(
              null,
            );
          }
        },

        onSettled: () => {
          setDeletingId(null);
        },
      },
    );
  }

  const messages =
    data?.items ?? [];

  return (
    <section className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#f5c400]">
            Administration
          </p>

          <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
            Messages de contact
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Consultez et gérez les
            messages envoyés depuis le
            formulaire de contact de KBR.
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6 grid gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 lg:grid-cols-[1fr_auto]">
          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            placeholder="Rechercher par nom, email ou sujet..."
            className="min-w-0 rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-[#f5c400]"
          />

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value as
                  | "all"
                  | ContactMessageStatus,
              )
            }
            className="rounded-xl border border-white/10 bg-[#0b0b0b] px-4 py-3 text-sm text-white outline-none focus:border-[#f5c400]"
          >
            <option value="all">
              Tous les statuts
            </option>

            <option value="new">
              Nouveaux
            </option>

            <option value="read">
              Lus
            </option>

            <option value="replied">
              Répondus
            </option>

            <option value="archived">
              Archivés
            </option>
          </select>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            {Array.from({
              length: 5,
            }).map((_, index) => (
              <MessageSkeleton
                key={index}
              />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-red-500/20 bg-red-500/10 text-xl font-black text-red-300">
              !
            </div>

            <h2 className="mt-4 text-lg font-bold text-white">
              Impossible de charger les
              messages
            </h2>

            <p className="mt-2 text-sm text-red-200/70">
              Vérifiez votre session
              administrateur et réessayez.
            </p>
          </div>
        )}

        {/* Empty */}
        {!isLoading &&
          !isError &&
          messages.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-12 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-2xl">
                ✉
              </div>

              <h2 className="mt-5 text-xl font-bold">
                Aucun message
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Aucun message ne correspond
                aux filtres sélectionnés.
              </p>
            </div>
          )}

        {/* Messages */}
        {!isLoading &&
          !isError &&
          messages.length > 0 && (
            <div className="space-y-3">
              {messages.map(
                (message) => {
                  const isNew =
                    message.status ===
                    "new";

                  return (
                    <article
                      key={
                        message.id
                      }
                      className={[
                        "overflow-hidden rounded-2xl border bg-white/[0.04] transition",
                        isNew
                          ? "border-[#f5c400]/20"
                          : "border-white/10",
                      ].join(" ")}
                    >
                      <div className="flex flex-col gap-5 p-5 lg:flex-row lg:items-center">
                        {/* Avatar */}
                        <div
                          className={[
                            "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-sm font-black",
                            isNew
                              ? "border border-[#f5c400]/20 bg-[#f5c400]/10 text-[#f5c400]"
                              : "border border-white/10 bg-white/[0.03] text-slate-400",
                          ].join(" ")}
                        >
                          {message.name
                            .charAt(
                              0,
                            )
                            .toUpperCase()}
                        </div>

                        {/* Content */}
                        <button
                          type="button"
                          onClick={() =>
                            handleOpenMessage(
                              message,
                            )
                          }
                          className="min-w-0 flex-1 text-left"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={[
                                "rounded-full border px-2.5 py-1 text-xs font-bold",
                                statusClass(
                                  message.status,
                                ),
                              ].join(
                                " ",
                              )}
                            >
                              {statusLabel(
                                message.status,
                              )}
                            </span>

                            <span className="text-xs text-slate-600">
                              {formatDate(
                                message.created_at,
                              )}
                            </span>
                          </div>

                          <div className="mt-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-2">
                            <h2
                              className={[
                                "truncate text-base font-bold",
                                isNew
                                  ? "text-white"
                                  : "text-slate-200",
                              ].join(
                                " ",
                              )}
                            >
                              {
                                message.name
                              }
                            </h2>

                            <span className="hidden text-slate-700 sm:inline">
                              ·
                            </span>

                            <span className="truncate text-sm text-slate-500">
                              {
                                message.email
                              }
                            </span>
                          </div>

                          <h3 className="mt-2 truncate text-sm font-bold text-slate-300">
                            {
                              message.subject
                            }
                          </h3>

                          <p className="mt-1 truncate text-sm text-slate-600">
                            {
                              message.message
                            }
                          </p>
                        </button>

                        {/* Actions */}
                        <div className="flex shrink-0 flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() =>
                              handleOpenMessage(
                                message,
                              )
                            }
                            className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-300 transition hover:bg-white/5 hover:text-white"
                          >
                            Voir
                          </button>

                          {message.status ===
                            "new" && (
                            <button
                              type="button"
                              disabled={
                                updateMutation.isPending
                              }
                              onClick={() =>
                                updateMutation.mutate(
                                  {
                                    messageId:
                                      message.id,
                                    status:
                                      "read",
                                  },
                                )
                              }
                              className="rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs font-bold text-blue-300 transition hover:bg-blue-500/20 disabled:opacity-50"
                            >
                              Marquer lu
                            </button>
                          )}

                          {message.status ===
                            "read" && (
                            <button
                              type="button"
                              disabled={
                                updateMutation.isPending
                              }
                              onClick={() =>
                                updateMutation.mutate(
                                  {
                                    messageId:
                                      message.id,
                                    status:
                                      "replied",
                                  },
                                )
                              }
                              className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs font-bold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                            >
                              Répondu
                            </button>
                          )}

                          <button
                            type="button"
                            disabled={
                              deletingId ===
                              message.id
                            }
                            onClick={() =>
                              handleDelete(
                                message,
                              )
                            }
                            className="rounded-lg border border-white/10 px-3 py-2 text-xs font-bold text-slate-400 transition hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50"
                          >
                            {deletingId ===
                            message.id
                              ? "Suppression..."
                              : "Supprimer"}
                          </button>
                        </div>
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          )}

        {/* Footer count */}
        {data && (
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600">
            <span>
              {messages.length}{" "}
              message
              {messages.length !==
              1
                ? "s"
                : ""}{" "}
              affiché
              {messages.length !==
              1
                ? "s"
                : ""}{" "}
              sur {data.total}
            </span>

            {data.total > 0 && (
              <span>
                Limite actuelle :{" "}
                {data.limit}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Modal */}
      {selectedMessage && (
        <MessageModal
          message={
            selectedMessage
          }
          onClose={() =>
            setSelectedMessage(
              null,
            )
          }
          onStatusChange={
            handleStatusChange
          }
          isUpdating={
            updateMutation.isPending
          }
        />
      )}
    </section>
  );
}