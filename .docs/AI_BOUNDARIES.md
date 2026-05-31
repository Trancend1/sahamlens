# AI Boundaries

## Purpose

AI in SahamLens is an explanation layer. It may summarize evidence, highlight caveats, critique a plan, and help the user reflect. It must not make trading decisions for the user.

## Allowed

- Summarize selected market, fundamental, news, journal, and risk context.
- Explain why a screener result matched transparent rules.
- Point out missing data, stale sources, and unsupported conclusions.
- Critique a user-written trade plan using evidence and caveats.
- Generate weekly journal reflection.
- Redact private data before sending context to an LLM.

## Not Allowed

- Say buy, sell, hold, strong buy, safe, guaranteed, pasti naik, or equivalent signal language.
- Predict exact future prices as fact.
- Approve a trade plan.
- Place, prepare, or automate broker orders.
- Use private portfolio/journal data without user-controlled context building.
- Present sparse, stale, failed, or unknown data as reliable.
- Produce public recommendations or content for clients/audience.

## Required Output Shape

Every AI answer used in product flows must include:

- `evidence`: non-empty list of cited facts or observations.
- `caveats`: non-empty list of limitations.
- `not_financial_advice`: true.

If evidence is insufficient, the model must say data is insufficient and avoid inference.

## Data Quality Rules

AI must respect:

- Freshness state.
- Coverage tier.
- Fundamental completeness.
- Provider trust tier.
- Source timestamps.

Behavior:

- Fresh data: normal explanation with caveats.
- Delayed data: mention delay.
- Stale or failed data: explain why decision support is limited.
- Partial data: identify missing fields.
- Unknown data: do not infer.

## Prompt Boundary

Prompts should instruct the model to:

- Use decision-support language.
- Separate facts from interpretation.
- Prefer "what this may indicate" over "what to do".
- Ask for missing user assumptions when needed.
- Keep responses short and evidence-led.

Prompts must not ask the model to rank stocks as buys, generate signals, or predict future price targets.

## Provider Direction

V1 is provider-ready but not multi-provider UX. Feature code should call the existing AI wrapper and avoid hardcoding a vendor. Switching providers is an implementation detail, not a product promise.

## Failure Handling

When safety validation fails:

- Block the unsafe answer.
- Show a short fallback message.
- Log the validation reason locally.
- Do not retry with broader or less safe instructions.
