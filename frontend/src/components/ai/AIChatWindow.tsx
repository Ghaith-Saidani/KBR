import {
  Bot,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import { useAIChat } from "../../features/ai/ai.hooks";

import type {
  AIMessage,
  AIRequestMessage,
} from "../../features/ai/ai.types";

import AIMessageComponent from "./AIMessage";

interface AIChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
}

const INITIAL_MESSAGE: AIMessage = {
  id: "initial-assistant-message",
  role: "assistant",
  content:
    "Bonjour ! 👋 Je suis l'assistant officiel de KBR. Je peux vous renseigner sur le club, nos membres, les événements, les activités, les actualités et la manière de nous rejoindre.",
};

const SUGGESTIONS = [
  "Quand est le prochain événement ?",
  "Comment rejoindre KBR ?",
  "Quelles activités propose KBR ?",
];

export default function AIChatWindow({
  isOpen,
  onClose,
}: AIChatWindowProps) {
  const [messages, setMessages] =
    useState<AIMessage[]>([
      INITIAL_MESSAGE,
    ]);

  const [input, setInput] =
    useState("");

  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  const textareaRef =
    useRef<HTMLTextAreaElement | null>(
      null,
    );

  const {
    mutateAsync,
    isPending,
    isError,
    reset,
  } = useAIChat();

  const hasUserMessages =
    messages.some(
      (message) =>
        message.role === "user",
    );

  const showSuggestions =
    !hasUserMessages &&
    !isPending;

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [
    messages,
    isPending,
    isOpen,
  ]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const timeout =
      window.setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [isOpen]);

  const sendMessage = async (
    content: string,
  ) => {
    const trimmedContent =
      content.trim();

    if (
      !trimmedContent ||
      isPending
    ) {
      return;
    }

    const userMessage: AIMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedContent,
    };

    const conversation = [
      ...messages,
      userMessage,
    ];

    setMessages(conversation);
    setInput("");
    reset();

    /*
     * Convert UI messages into API messages.
     *
     * AIMessage contains an `id` used only by React.
     * The backend only needs `role` and `content`.
     */
    const apiMessages: AIRequestMessage[] =
      conversation
        .filter(
          (message) =>
            message.role === "user" ||
            message.role === "assistant",
        )
        .map(
          ({
            role,
            content,
          }) => ({
            role,
            content,
          }),
        );

    try {
      const response =
        await mutateAsync({
          messages: apiMessages,
          temperature: 0.2,
        });

      const assistantMessage: AIMessage =
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            response.content,
        };

      setMessages(
        (currentMessages) => [
          ...currentMessages,
          assistantMessage,
        ],
      );
    } catch {
      /*
       * React Query exposes the error
       * through isError.
       */
    }
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    await sendMessage(input);
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      void sendMessage(input);
    }
  };

  const clearConversation = () => {
    if (isPending) {
      return;
    }

    const confirmed =
      window.confirm(
        "Voulez-vous vraiment supprimer cette conversation ?",
      );

    if (!confirmed) {
      return;
    }

    reset();

    setMessages([
      {
        ...INITIAL_MESSAGE,
        id: crypto.randomUUID(),
      },
    ]);

    setInput("");
  };

  return (
    <section
      aria-label="Assistant KBR"
      aria-hidden={!isOpen}
      className={[
        "fixed bottom-24 right-5 z-[60]",
        "flex h-[min(680px,calc(100vh-8rem))]",
        "w-[min(420px,calc(100vw-2rem))]",
        "flex-col overflow-hidden",
        "rounded-2xl border border-slate-200",
        "bg-white shadow-2xl",
        "transition-all duration-200",
        isOpen
          ? "visible translate-y-0 opacity-100"
          : "pointer-events-none invisible translate-y-4 opacity-0",
      ].join(" ")}
    >
      {/* Header */}
      <header className="shrink-0 bg-[#050505] px-4 py-4 text-white">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F5C400] text-[#050505]">
              <Bot
                className="h-5 w-5"
                strokeWidth={2.5}
              />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="truncate text-sm font-bold">
                  KBR AI
                </h2>

                <span className="flex items-center gap-1 rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-semibold text-white/70">
                  <Sparkles className="h-3 w-3" />
                  IA
                </span>
              </div>

              <p className="mt-0.5 text-xs text-white/50">
                Assistant officiel de KBR
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={clearConversation}
              disabled={isPending}
              aria-label="Nouvelle conversation"
              title="Nouvelle conversation"
              className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              <RefreshCw className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={onClose}
              aria-label="Fermer l'assistant"
              title="Fermer"
              className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white"
            >
              <span className="text-xl leading-none">
                ×
              </span>
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50 px-4 py-5">
        <div className="flex flex-col gap-4">
          {messages.map(
            (message) => (
              <AIMessageComponent
                key={message.id}
                message={message}
              />
            ),
          )}

          {/* Suggestions */}
          {showSuggestions && (
            <div className="mt-1">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-[#D4A900]" />

                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Suggestions
                </p>
              </div>

              <div className="flex flex-col gap-2">
                {SUGGESTIONS.map(
                  (suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() =>
                        void sendMessage(
                          suggestion,
                        )
                      }
                      disabled={isPending}
                      className={[
                        "group flex w-full items-center",
                        "rounded-xl border",
                        "border-slate-200",
                        "bg-white",
                        "px-3 py-3",
                        "text-left text-xs",
                        "font-medium text-slate-600",
                        "shadow-sm",
                        "transition-all duration-150",
                        "hover:-translate-y-0.5",
                        "hover:border-[#F5C400]",
                        "hover:bg-yellow-50",
                        "hover:text-slate-900",
                        "hover:shadow-md",
                        "disabled:cursor-not-allowed",
                        "disabled:opacity-50",
                      ].join(" ")}
                    >
                      <span className="mr-2.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500 transition-colors group-hover:bg-[#F5C400] group-hover:text-[#050505]">
                        <Sparkles className="h-3 w-3" />
                      </span>

                      <span>
                        {suggestion}
                      </span>
                    </button>
                  ),
                )}
              </div>
            </div>
          )}

          {/* Loading */}
          {isPending && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#F5C400] text-[#050505]">
                <Bot
                  className="h-4 w-4"
                  strokeWidth={2.5}
                />
              </div>

              <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs leading-5 text-red-700">
              <p className="font-semibold">
                Impossible de contacter
                l'assistant.
              </p>

              <p className="mt-1 text-red-600/80">
                Vérifiez que le serveur
                KBR est disponible puis
                réessayez.
              </p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-slate-200 bg-white p-3"
      >
        <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-slate-50 p-2 transition focus-within:border-[#F5C400] focus-within:ring-2 focus-within:ring-[#F5C400]/20">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(event) =>
              setInput(
                event.target.value,
              )
            }
            onKeyDown={handleKeyDown}
            disabled={isPending}
            rows={1}
            maxLength={2000}
            placeholder="Posez votre question..."
            aria-label="Message à l'assistant KBR"
            className="max-h-32 min-h-10 flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={
              !input.trim() ||
              isPending
            }
            aria-label="Envoyer le message"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#F5C400] text-[#050505] transition hover:bg-[#FFD21A] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send
              className="h-4 w-4"
              strokeWidth={2.5}
            />
          </button>
        </div>

        <div className="mt-2 flex items-center justify-between px-1">
          <p className="text-[10px] text-slate-400">
            Entrée pour envoyer · Shift+Entrée
            pour une nouvelle ligne
          </p>

          <div className="flex items-center gap-3">
            {messages.length > 1 && (
              <button
                type="button"
                onClick={clearConversation}
                disabled={isPending}
                className="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-400 transition hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Trash2 className="h-3 w-3" />
                Effacer
              </button>
            )}

            <span className="text-[10px] text-slate-400">
              {input.length}/2000
            </span>
          </div>
        </div>
      </form>
    </section>
  );
}