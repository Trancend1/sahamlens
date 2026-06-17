"use client";

import { useEffect, useRef } from "react";

interface AutoRefreshOptions {
  isStale: boolean;
  onRefresh: () => Promise<unknown>;
  enabled?: boolean;
}

/**
 * Auto-refresh stale data once on page load.
 * Uses a ref to prevent infinite loops — only fires once per mount.
 */
export function useAutoRefresh({ isStale, onRefresh, enabled = true }: AutoRefreshOptions): void {
  const attempted = useRef(false);

  useEffect(() => {
    if (!enabled) return;
    const flag = process.env.NEXT_PUBLIC_AUTO_REFRESH_ON_LOAD;
    const shouldRefresh = flag === "true" || flag === "1" || !flag;
    if (isStale && shouldRefresh && !attempted.current) {
      attempted.current = true;
      onRefresh().catch(() => {});
    }
  }, [isStale, onRefresh, enabled]);
}
