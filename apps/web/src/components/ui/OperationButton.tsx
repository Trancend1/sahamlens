"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";

interface Props {
  label: string;
  runningLabel: string;
  action: () => Promise<{ ok: boolean; message?: string; error?: string }>;
  onComplete?: () => void;
  reloadOnComplete?: boolean;
  timeout?: number;
  variant?: "primary" | "secondary";
}

export function OperationButton({
  label,
  runningLabel,
  action,
  onComplete,
  reloadOnComplete,
  variant = "secondary",
}: Props) {
  const [running, setRunning] = useState(false);

  const handleClick = useCallback(async () => {
    if (running) return;
    setRunning(true);
    try {
      const result = await action();
      if (result.ok) {
        toast.success(result.message ?? "Selesai");
        if (reloadOnComplete) window.location.reload();
        onComplete?.();
      } else {
        toast.error(result.error ?? "Gagal");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Terjadi kesalahan");
    } finally {
      setRunning(false);
    }
  }, [running, action, onComplete, reloadOnComplete]);

  const base = "rounded px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50";
  const primary = `${base} bg-accent text-white hover:bg-accent/80`;
  const secondary = `${base} border border-accent/40 text-accent hover:bg-accent/10`;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={running}
      className={variant === "primary" ? primary : secondary}
    >
      {running ? (
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block size-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
          {runningLabel}
        </span>
      ) : (
        label
      )}
    </button>
  );
}
