"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

interface LlmConfig {
  provider: string;
  baseUrl: string;
  model: string;
}

export function LlmConfigForm() {
  const [provider, setProvider] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch("/api/config?section=llm");
        if (!res.ok) return;
        const { config } = await res.json() as { section: string; config: LlmConfig };
        if (cancelled) return;
        setProvider(config.provider);
        setBaseUrl(config.baseUrl);
        setModel(config.model);
      } catch {
        // silent
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const body: Record<string, string> = {};
      if (provider) body.provider = provider;
      if (baseUrl) body.baseUrl = baseUrl;
      if (model) body.model = model;
      if (apiKey) body.apiKey = apiKey;

      const res = await fetch("/api/config?section=llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json() as { ok?: boolean; error?: string };

      if (res.ok && data.ok) {
        toast.success("LLM configuration saved.");
      } else {
        toast.error(data.error ?? "Failed to save LLM configuration.");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save LLM configuration.");
    } finally {
      setSaving(false);
    }
  }, [provider, baseUrl, model, apiKey]);

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 rounded-md border border-muted/30 bg-white/[0.02] p-5">
      <h2 className="text-sm font-medium">LLM Provider Configuration</h2>
      <label className="grid gap-1">
        <span className="text-sm font-medium">Provider</span>
        <input
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="rounded-md border border-muted/30 px-3 py-2 text-sm bg-black/30"
          placeholder="e.g. openrouter"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-sm font-medium">Base URL</span>
        <input
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          className="rounded-md border border-muted/30 px-3 py-2 text-sm bg-black/30"
          placeholder="e.g. https://openrouter.ai/api/v1"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-sm font-medium">Model</span>
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="rounded-md border border-muted/30 px-3 py-2 text-sm bg-black/30"
          placeholder="e.g. anthropic/claude-sonnet-4-6"
        />
      </label>
      <label className="grid gap-1">
        <span className="text-sm font-medium">API Key</span>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="rounded-md border border-muted/30 px-3 py-2 text-sm bg-black/30"
          placeholder="Enter new API key to change"
        />
      </label>
      <p className="text-xs text-muted">API key is never returned by the server. Leave blank to keep the existing key.</p>
      <button
        type="submit"
        disabled={saving}
        className="self-start rounded border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10 disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save LLM Configuration"}
      </button>
    </form>
  );
}
