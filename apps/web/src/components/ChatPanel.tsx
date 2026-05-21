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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
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
          { role: "assistant", content: `[Error] ${errMsg}` },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: body.answer, response: body },
        ]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `[Error] ${e instanceof Error ? e.message : "Gagal memuat jawaban."}`,
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
        Tanya AI
      </h2>

      {messages.length === 0 && (
        <p className="text-xs text-muted">
          Tanyakan apapun tentang {symbol} berdasarkan data lokal.
        </p>
      )}

      <div className="flex flex-col gap-3">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "flex justify-end" : "flex flex-col gap-2"}>
            {msg.role === "user" ? (
              <span className="max-w-prose rounded-lg bg-accent/20 px-3 py-2 text-sm">
                {msg.content}
              </span>
            ) : (
              <AssistantBubble msg={msg} />
            )}
          </div>
        ))}
        {loading && (
          <p className="text-xs text-muted animate-pulse">Memproses…</p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Tanya tentang ${symbol}…`}
          disabled={loading}
          className="flex-1 rounded border border-muted/30 bg-white/[0.03] px-3 py-2 text-sm placeholder:text-muted/50 focus:border-accent/50 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded border border-accent/40 px-3 py-2 text-sm text-accent hover:bg-accent/10 disabled:opacity-50"
        >
          Kirim
        </button>
      </form>

      <p className="text-xs text-muted/60">
        Bukan saran keuangan. AI menjelaskan, kamu memutuskan.
      </p>
    </section>
  );
}

function AssistantBubble({ msg }: { msg: ChatMessage }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const response = msg.response;

  return (
    <div className="flex flex-col gap-2 rounded border border-muted/20 bg-white/[0.02] p-3">
      <p className="text-sm">{msg.content}</p>

      {response && (
        <>
          {response.caveats.length > 0 && (
            <ul className="list-disc pl-4 text-xs text-muted">
              {response.caveats.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          )}

          {response.evidence.length > 0 && (
            <button
              onClick={() => setShowEvidence((v) => !v)}
              className="self-start text-xs text-accent/70 hover:text-accent"
            >
              {showEvidence ? "Sembunyikan" : "Lihat"} evidence ({response.evidence.length})
            </button>
          )}

          {showEvidence && (
            <ul className="flex flex-col gap-1">
              {response.evidence.map((ev, i) => (
                <li key={i} className="flex gap-2 text-xs">
                  <span className="shrink-0 rounded bg-accent/10 px-1.5 py-0.5 text-accent">
                    {ev.type}
                  </span>
                  <span className="text-muted">{ev.value}</span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
