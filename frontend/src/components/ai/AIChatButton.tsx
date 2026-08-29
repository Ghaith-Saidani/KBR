import {
  Bot,
  X,
} from "lucide-react";

interface AIChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

export default function AIChatButton({
  isOpen,
  onClick,
}: AIChatButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={
        isOpen
          ? "Fermer l'assistant KBR"
          : "Ouvrir l'assistant KBR"
      }
      aria-expanded={isOpen}
      className={[
        "group fixed bottom-5 right-5 z-[60]",
        "flex h-14 w-14 items-center justify-center",
        "rounded-full shadow-xl",
        "transition-all duration-200",
        "focus:outline-none focus:ring-2",
        "focus:ring-[#F5C400] focus:ring-offset-2",
        "focus:ring-offset-slate-50",
        isOpen
          ? "bg-[#050505] text-white hover:scale-105"
          : "bg-[#F5C400] text-[#050505] hover:scale-105 hover:bg-[#FFD21A]",
      ].join(" ")}
    >
      {isOpen ? (
        <X
          className="h-6 w-6"
          strokeWidth={2.5}
        />
      ) : (
        <Bot
          className="h-7 w-7"
          strokeWidth={2.2}
        />
      )}

      {/* Online indicator */}
      {!isOpen && (
        <span className="pointer-events-none absolute right-0 top-0 flex h-3.5 w-3.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#F5C400] opacity-75" />

          <span className="relative inline-flex h-3.5 w-3.5 rounded-full border-2 border-white bg-green-500" />
        </span>
      )}

      {/* Tooltip */}
      <span
        className={[
          "pointer-events-none absolute right-0 top-full mt-2",
          "whitespace-nowrap rounded-lg bg-[#050505]",
          "px-3 py-1.5 text-xs font-semibold text-white",
          "opacity-0 shadow-lg transition-opacity",
          "group-hover:opacity-100",
          isOpen ? "hidden" : "",
        ].join(" ")}
      >
        Assistant KBR
      </span>
    </button>
  );
}