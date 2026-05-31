# ADR-0007: Documentation Language and Style

Status: Accepted
Date: 2026-05-31

## Context

The project mixes Indonesian product context with English technical naming. Documentation must stay easy for the owner and future agents to use.

## Decision

Use clear English for canonical technical docs, while preserving Indonesian user/product terms when they are the natural domain language.

Rules:

- Prefer short sections and source-of-truth mapping.
- Avoid duplicating the same decision across files.
- Keep historical planning out of active docs.
- Use ASCII punctuation to avoid encoding issues.

## Consequences

Positive:

- Future implementation agents can scan docs quickly.
- Technical names stay consistent with code.
- Indonesian product intent is not lost.

Trade-offs:

- Some user-facing phrasing may still need Indonesian localization in the app.

## Follow-Up

If docs become noisy again, rewrite the canonical file instead of appending another planning artifact.
