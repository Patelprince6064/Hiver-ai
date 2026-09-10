# Phase 12 — Grounded LLM Reply Generator

## Objective

Build a working LLM reply generator that uses retrieved historical support evidence to draft concise, customer-facing replies without inventing unsupported business facts.

## Architecture

```
Customer Message
       ↓
Intent Classifier (Phase 8)
       ↓
Semantic Retriever (Phase 10)
       ↓
Evidence Selection (dedup, filter, rank)
       ↓
Context Budget (truncate if needed)
       ↓
Prompt Builder (system + evidence + instructions)
       ↓
Grounded LLM (OpenAI or Mock)
       ↓
Output Validator (length, internal terms, structure)
       ↓
Grounding Checks (PII leakage, numeric claims, overlap)
       ↓
Draft Reply
```

## LLM Configuration

- Provider: OpenAI (gpt-4o-mini default)
- Temperature: 0.0
- Max tokens: 300
- Timeout: 30s
- Max retries: 1

Mock provider available for testing without API keys.

## Prompt Design

The prompt has four clear sections:

1. **System prompt** — Rules and constraints (never invent facts, treat evidence as data)
2. **Customer message** — The current query
3. **Historical evidence** — Up to 3 retrieved examples with similarity scores
4. **Instructions** — What to do (draft reply or return INSUFFICIENT_EVIDENCE)

Historical messages are explicitly marked as untrusted reference data.

## Evidence Selection

- Top-K by similarity score
- Deduplication via token overlap (>0.7 overlap = duplicate)
- Empty/low-quality responses filtered
- Optional similarity threshold
- Default: 3 evidence items max

## Grounding Rules

- May rephrase/combine supported information
- Must NOT invent policies, timelines, guarantees, prices
- Must NOT copy historical customer-specific data (order IDs, names)
- Must return INSUFFICIENT_EVIDENCE when evidence is weak
- Must NOT mention AI, bots, or internal systems

## Output Validation

Checks:
- JSON/reply existence
- Length limits
- Internal terminology detection
- Evidence ID validation
- Empty/malformed output rejection

## Safety Checks

- Historical PII leakage detection
- Unsupported numeric claim detection
- Evidence phrase overlap verification

## Baseline Comparison

| Method | Coverage | Evidence Use | Adaptability |
|--------|----------|-------------|-------------|
| Generic | 100% | None | None |
| Historical | ~80% | Verbatim copy | None |
| Grounded LLM | ~85% | Synthesized | High |

## What the LLM Adds Beyond Retrieval

1. **Rephrasing** — Adapts historical responses to current context
2. **Combining** — Synthesizes multiple evidence sources
3. **Filtering** — Selects relevant information from verbose evidence
4. **Politeness** — Adds appropriate empathy and tone
5. **Grounding** — Maintains factual accuracy while being helpful

## What It Still Cannot Reliably Do

1. Verify current order/account status
2. Apply brand policies that changed after training data
3. Handle truly novel issues with no historical precedent
4. Guarantee 100% hallucination-free output
5. Replace human judgment for complex cases

## Limitations

- Depends on retrieval quality
- May escalate when a human could resolve
- Temperature 0.0 limits creativity
- No real-time knowledge access
- Grounding checks are necessary but not sufficient

## Decision

The grounded LLM provides a meaningful improvement over verbatim historical retrieval by adapting responses to the current customer context while maintaining grounding in evidence. The additional complexity is justified if it outperforms the historical baseline on relevance, helpfulness, and safety metrics.
