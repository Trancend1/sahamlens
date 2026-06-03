"use client";

import { useRef, useState } from "react";
import type { ChatResponse } from "@/lib/stockBrief";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

interface Props {
  symbol: string;
}

export function ChatPanel({ symbol }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`/api/stocks/${symbol}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const body = (await res.json()) as ChatResponse | { error: string };
      if (!res.ok || "error" in body) {
        const errMsg = "error" in body ? body.error : `HTTP ${res.status}`;
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `The AI response could not be generated. ${errMsg}` },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: body.answer, response: body },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `The AI response could not be generated. ${
            error instanceof Error ? error.message : "Check local runtime readiness and try again."
          }`,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold uppercase tracking-widest text-muted">
        Ask AI
      </h2>

      {messages.length === 0 ? (
        <p className="text-xs text-muted">
          Ask about {symbol} using available local data. Review evidence and caveats before making
          decisions.
        </p>
      ) : null}

      <div className="flex flex-col gap-3">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={message.role === "user" ? "flex justify-end" : "flex flex-col gap-2"}>
            {message.role === "user" ? (
              <span className="max-w-prose rounded-lg bg-accent/20 px-3 py-2 text-sm">
                {message.content}
              </span>
            ) : (
              <AssistantBubble message={message} />
            )}
          </div>
        ))}
        {loading ? (
          <p className="animate-pulse text-xs text-muted">Generating response...</p>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={`Ask about ${symbol}...`}
          disabled={loading}
          className="flex-1 rounded border border-muted/30 bg-white/[0.03] px-3 py-2 text-sm placeholder:text-muted/50 focus:border-accent/50 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded border border-accent/40 px-3 py-2 text-sm text-accent hover:bg-accent/10 disabled:opacity-50"
        >
          Ask
        </button>
      </form>

      <p className="text-xs text-muted/60">
        Not financial advice. AI explains; you decide.
      </p>
    </section>
  );
}

function AssistantBubble({ message }: { message: ChatMessage }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const response = message.response;

  return (
    <div className="flex flex-col gap-2 rounded border border-muted/20 bg-white/[0.02] p-3">
      <p className="text-sm">{message.content}</p>

      {response ? (
        <>
          {response.caveats.length > 0 ? (
            <ul className="list-disc pl-4 text-xs text-muted">
              {response.caveats.map((caveat, index) => (
                <li key={`${caveat}-${index}`}>{caveat}</li>
              ))}
            </ul>
          ) : null}

          {response.evidence.length > 0 ? (
            <button
              onClick={() => setShowEvidence((value) => !value)}
              className="self-start text-xs text-accent/70 hover:text-accent"
              type="button"
            >
              {showEvidence ? "Hide" : "View"} evidence ({response.evidence.length})
            </button>
          ) : null}

          {showEvidence ? (
            <ul className="flex flex-col gap-1">
              {response.evidence.map((evidence, index) => (
                <li key={`${evidence.type}-${index}`} className="flex gap-2 text-xs">
                  <span className="shrink-0 rounded bg-accent/10 px-1.5 py-0.5 text-accent">
                    {evidence.type}
                  </span>
                  <span className="text-muted">{evidence.value}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
