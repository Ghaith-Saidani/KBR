import ReactMarkdown from "react-markdown";
import {
  Bot,
  User,
} from "lucide-react";

import type {
  AIMessage as AIMessageType,
} from "../../features/ai/ai.types";

interface AIMessageProps {
  message: AIMessageType;
}

export default function AIMessage({
  message,
}: AIMessageProps) {
  const isUser =
    message.role === "user";

  return (
    <div
      className={[
        "flex gap-3",
        isUser
          ? "justify-end"
          : "justify-start",
      ].join(" ")}
    >
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#F5C400] text-[#050505]">
          <Bot
            className="h-4 w-4"
            strokeWidth={2.5}
            aria-hidden="true"
          />
        </div>
      )}

      <div
        className={[
          "max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-6",
          isUser
            ? "rounded-br-md bg-[#F5C400] font-medium text-[#050505]"
            : "rounded-bl-md border border-slate-200 bg-white text-slate-700 shadow-sm",
        ].join(" ")}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">
            {message.content}
          </p>
        ) : (
          <div
            className={[
              "break-words",
              "[&_p]:my-1.5",
              "[&_p:first-child]:mt-0",
              "[&_p:last-child]:mb-0",
              "[&_strong]:font-bold",
              "[&_ul]:my-2",
              "[&_ol]:my-2",
              "[&_ul]:list-disc",
              "[&_ol]:list-decimal",
              "[&_ul]:pl-5",
              "[&_ol]:pl-5",
              "[&_li]:my-0.5",
              "[&_a]:font-semibold",
              "[&_a]:underline",
              "[&_h1]:mb-2",
              "[&_h1]:mt-3",
              "[&_h1]:text-base",
              "[&_h1]:font-bold",
              "[&_h2]:mb-2",
              "[&_h2]:mt-3",
              "[&_h2]:text-base",
              "[&_h2]:font-bold",
              "[&_h3]:mb-1",
              "[&_h3]:mt-2",
              "[&_h3]:font-bold",
              "[&_code]:rounded",
              "[&_code]:bg-slate-100",
              "[&_code]:px-1",
              "[&_code]:py-0.5",
              "[&_code]:text-xs",
            ].join(" ")}
          >
            <ReactMarkdown>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#050505] text-white">
          <User
            className="h-4 w-4"
            strokeWidth={2}
            aria-hidden="true"
          />
        </div>
      )}
    </div>
  );
}