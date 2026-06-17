# Sprint 3: Operations Dashboard — Design Spec

> **Phase:** CLI-WebUI Integration — Sprint 3
> **Status:** Approved
> **Author:** AI Architect
> **Date:** 2026-06-17

---

## 1. Goal

User dapat memonitor & manage semua operasi data dari WebUI tanpa terminal. Satu halaman terpadu untuk health, jobs, dan config.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    /operations/*                          │
│                                                          │
│  /api/health (single source of truth)                    │
│       ↓                                                  │
│  runPython → Python subprocess → DuckDB + sys info       │
│                                                          │
│  /api/config?section=llm|app                            │
│       ↓                                                  │
│  Node.js fs → read/write .env.local + config/*.yml       │
│                                                          │
│  /api/data/freshness (existing)                          │
│       ↓                                                  │
│  runPython → scripts.freshness check --json              │
└──────────────────────────────────────────────────────────┘
```

## 3. Routes & Pages

### 3.1 Layout — `/operations/layout.tsx`

```
SahamLens / Operations / [tab]
                          │
  [Providers] [Health] [Config]
```

- Tab pills, active state highlighted
- Breadcrumb: `SahamLens / Operations / {tab}`
- Default redirect: `/operations` → `/operations/providers`

### 3.2 Providers — `/operations/providers/page.tsx`

Daftar semua data operation dengan status freshness + Run Now.

| Column | Source |
|--------|--------|
| Operation | Registry (lib/operations.ts) |
| Last Run | `GET /api/data/freshness` |
| Status | FreshnessBadge (reuse existing) |
| Action | `POST /api/operations/{id}/run` |

**Operations registry** (`lib/operations.ts`):

```ts
interface Operation {
  id: string;
  name: string;
  description: string;
  category: "provider" | "analysis" | "review";
  route: string;            // API route to POST
  freshnessKey: string;      // key in freshness report
  timeoutMs: number;
}
```

### 3.3 Health — `/operations/health/page.tsx`

Reads `GET /api/health` as single source of truth.

```
Overall Status
  🟢 Healthy — All required services available.
  🟡 Degraded — Some non-critical services unavailable.
  🔴 Unhealthy — Core services unavailable.

System Health
  ├─ Core Engine   ✅ Available
  ├─ Database      ✅ Ready
  ├─ LLM Provider  ⚠️ Optional
  └─ Runtime       ✅ Ready

Data Refresh
  Mode: Manual
  Refresh occurs through provider actions and stale-data banners.
  Automatic scheduling: planned.

[View Full Health JSON]
```

### 3.4 Config — `/operations/config/page.tsx`

Read/write config files via `GET/POST /api/config?section=...`

**Sections (Sprint 3):**

1. **LLM Provider**
   - Provider dropdown (anthropic, openai_compatible, openrouter, tokenrouter, etc.)
   - Model text field
   - Base URL text field
   - API Key password field (write-only, never read back)
   - Status ✅/❌
   - [Test Connection] [Save]

2. **Application**
   - Timezone dropdown (default: Asia/Jakarta)
   - Data directory (read-only display)

**Not in Sprint 3:**
- Watchlist → already at `/watchlist`
- RSS Feeds → deferred to Providers page (Sprint 4+)
- Indicators → deferred to Screener settings (Sprint 4+)

---

## 4. API Routes

### 4.1 `GET /api/health`

Returns combined health status. Single source of truth.

```json
{
  "overall": "healthy" | "degraded" | "unhealthy",
  "checks": {
    "python": { "status": "ok", "version": "3.12.7" },
    "database": { "status": "ok", "size_mb": 4.2, "tables": 31 },
    "runtime": { "status": "ok", "schema": "ready", "pending_migrations": 0 },
    "llm": { "status": "ok" | "degraded", "provider": "openrouter", "model": "...", "configured": true },
    "data_refresh": { "mode": "manual" }
  }
}
```

### 4.2 `GET/POST /api/config`

Read/write config via `?section=llm|app`.

- `GET /api/config?section=llm` — returns current LLM config (without API key value)
- `POST /api/config?section=llm` — updates LLM config
- Reads `.env.local` directly via Node.js `fs`

### 4.3 `POST /api/operations/[type]/run`

Unified route untuk Run Now buttons. Maps operation type → Python script via `operations.ts` registry.

```ts
// lib/operations.ts registry entry:
{ id: "provider_health", route: "api/operations/provider_health/run", ... }
```

The API route calls `runPython()` with the correct script + args from a mapping.

**Supported types:** `provider_health`, `prices`, `fundamentals`, `news`, `alerts`, `screener`, `strategy_rules`, `weekly_review`

### 4.4 Existing — freshness API

Reuse `GET /api/data/freshness` (read report) and `POST /api/data/freshness` (refresh all stale) for operations data.

---

## 5. File Mapping

### Create (11 files)

| File | Purpose |
|------|---------|
| `apps/web/src/app/operations/layout.tsx` | Layout + tabs |
| `apps/web/src/app/operations/page.tsx` | Redirect → /operations/providers |
| `apps/web/src/app/operations/providers/page.tsx` | Ops table + Run Now |
| `apps/web/src/app/operations/health/page.tsx` | Health overview |
| `apps/web/src/app/operations/config/page.tsx` | Config editor |
| `apps/web/src/app/api/health/route.ts` | Health JSON endpoint |
| `apps/web/src/app/api/config/route.ts` | Read/write .env.local |
| `apps/web/src/app/api/operations/[type]/run/route.ts` | Unified Run Now route |
| `apps/web/src/lib/operations.ts` | Operations registry |
| `apps/web/src/lib/health.ts` | Health types + fetch |
| `apps/web/src/components/OperationsTable.tsx` | Ops table (client) |
| `apps/web/src/components/HealthOverview.tsx` | Health overview (client) |

### Modify (2 files)

| File | Change |
|------|--------|
| `apps/web/src/app/page.tsx` | + "Operations" card |
| `package.json` | + `js-yaml` |

---

## 6. Component Tree

```
layout.tsx
  └─ /operations
       ├─ page.tsx (redirect)
       ├─ providers/page.tsx
       │    └─ OperationsTable (client)
       │         └─ OperationButton (reuse) → POST /api/operations/{type}/run
       ├─ health/page.tsx
       │    └─ HealthOverview (client)         → GET /api/health
       └─ config/page.tsx
            └─ ConfigForm (client, inline)    → GET/POST /api/config

/api
  ├─ health/route.ts                          → GET
  ├─ config/route.ts                          → GET, POST
  └─ operations/[type]/run/route.ts           → POST
```

---

## 7. Key Decisions

| Decision | Rationale |
|----------|-----------|
| `/operations` not `/admin` | User-centric naming, domain-aligned |
| Tab layout | Extensible for Sprint 4 (Hermes logs, jobs) |
| `/api/health` as SoT | Enables reuse: CLI doctor, Hermes, future installers |
| Config via `?section=` | Prevents god endpoint, enables partial updates |
| API key write-only | Security best practice |
| No Watchlist in Config | Avoids dual source of truth with /watchlist page |
| `operations.ts` as registry | Auto-generate Run Now buttons, typed metadata |

---

## 8. Acceptance Criteria

- [ ] `/operations` accessible from dashboard card
- [ ] Tab navigation works: Providers | Health | Config
- [ ] Operations table shows all data operations from freshness report
- [ ] "Run Now" triggers correct operation
- [ ] Run All Stale refreshes all stale data
- [ ] Health page shows overall status + system health + data refresh mode
- [ ] Config page reads/writes LLM provider settings
- [ ] Config page never leaks API key in responses
- [ ] `/api/health` returns JSON for all components
- [ ] No terminal commands needed for any operation
