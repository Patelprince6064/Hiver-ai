# Phase 13 — Grounding Verification & Hallucination Protection

## Objective

Detect and prevent hallucinated, unsupported, or risky claims in generated replies before they reach the customer.

## What Was Built

### Verification Pipeline

A multi-layer grounding verification pipeline that checks every generated reply against retrieved evidence:

1. **Claim Extraction** (`src/evaluation/claim_extractor.py`) — Splits replies into sentences and clauses, classifies each into 15 fact types (instruction, policy, action, timeline, price, quantity, identifier, contact_method, guarantee, status, resolution, technical_claim, refund, personal_information, account_action, order_status, financial_claim, other).

2. **Evidence Support Check** (`src/evaluation/evidence_support.py`) — Multi-signal heuristic cascade: exact match → customer message match → partial token overlap → entity inference. Returns support confidence from 0.1 to 0.95.

3. **Numeric Claim Checker** (`src/evaluation/numeric_claim_checker.py`) — Detects prices, percentages, durations, quantities, dates, and order numbers using regex. Verifies numeric claims exist in evidence.

4. **URL Checker** (`src/evaluation/url_checker.py`) — Detects URLs in replies. Verifies each URL exists in evidence or the customer's original message. Strips trailing punctuation to prevent false mismatches.

5. **Semantic Grounding** (`src/evaluation/semantic_grounding.py`) — Embedding similarity (when available) or token overlap fallback. Estimates whether reply content is semantically supported by evidence.

6. **Hybrid Verdict** (`src/evaluation/grounding_score.py`) — Combines all signals into a priority-ordered verdict: pass, review, fail, or insufficient_evidence.

### Reply Repair

`src/generation/reply_repair.py` — When grounding verification fails, a targeted repair prompt instructs the LLM to remove unsupported claims while preserving supported content.

### Fact Type System

`src/evaluation/fact_types.py` — 15 fact-type categories with priority-ordered classification. High-risk types (price, guarantee, timeline, refund, identifier, personal_information, account_action, order_status, financial_claim) trigger automatic failure when unsupported.

### Grounding Schema

`src/evaluation/grounding_schema.py` — Pydantic models for `GroundingVerification` and `ClaimVerification`, providing structured output for downstream consumption.

### Grounding Metrics

`src/evaluation/grounding_metrics.py` — Aggregated metrics: pass rate, review rate, fail rate, unsupported claim rate, high-risk unsupported rate, repair rate, repair success rate, final rejection rate.

## Files Created

### Source Modules
- `src/evaluation/fact_types.py` — FactType enum and classification
- `src/evaluation/claim_extractor.py` — Claim extraction from replies
- `src/evaluation/evidence_support.py` — Evidence support checking
- `src/evaluation/numeric_claim_checker.py` — Numeric claim verification
- `src/evaluation/url_checker.py` — URL support verification
- `src/evaluation/semantic_grounding.py` — Semantic grounding check
- `src/evaluation/grounding_score.py` — Hybrid verdict computation
- `src/evaluation/grounding_schema.py` — Verification result schema
- `src/evaluation/grounding_metrics.py` — Aggregated grounding metrics
- `src/generation/reply_repair.py` — Reply repair strategy

### Configuration
- `configs/grounding.yaml` — Grounding pipeline configuration

### Scripts
- `scripts/evaluate_grounding.py` — End-to-end grounding evaluation
- `scripts/analyze_grounding_failures.py` — Failure categorization

### Tests (98 new, 449 total)
- `tests/test_claim_extractor.py` — 21 tests
- `tests/test_evidence_support.py` — 9 tests
- `tests/test_numeric_claim_checker.py` — 18 tests
- `tests/test_url_checker.py` — 16 tests
- `tests/test_grounding_verifier.py` — 16 tests
- `tests/test_reply_repair.py` — 8 tests
- `tests/test_grounding_pipeline.py` — 8 tests (integration)

## Verdict Policy

The verdict is computed in priority order:

| Priority | Condition | Verdict |
|----------|-----------|---------|
| 1 | No evidence available | insufficient_evidence |
| 2 | Unsupported high-risk claim | fail |
| 3 | Unsupported URL | fail |
| 4 | Historical PII/identifier leakage | fail |
| 5 | Multiple unsupported claims | fail |
| 6 | One unsupported claim | review |
| 7 | Low semantic grounding | review |
| 8 | All claims supported | pass |

## Test Results

```
449 passed, 1 warning in 12.95s
```

All 98 new Phase 13 tests pass. All 351 existing tests continue to pass.

## Decisions Logged

- Decision 112: Multi-Layer Grounding Verification
- Decision 113: Claim Extraction via Sentence/Clause Splitting
- Decision 114: Fact-Type Priority Ordering
- Decision 115: Hybrid Grounding Verdict Policy
- Decision 116: Claim Support Uses Multi-Signal Heuristic
- Decision 117: Reply Repair as Second LLM Call
- Decision 118: Semantic Grounding Uses Token Overlap Fallback
- Decision 119: Grounding Metrics Report Pass/Review/Fail Rates
- Decision 120: URL Checker Strips Trailing Punctuation

## Limitations

- Deterministic checks may miss subtle semantic hallucinations
- Token-overlap heuristics can produce false positives on common phrases
- Semantic grounding without embeddings is approximate
- Repair adds latency and cost
- All metrics are placeholders pending dataset download

## Next Steps

- Phase 14: Human Escalation Decision
- Full pipeline integration with dataset download
- Real LLM evaluation with OpenAI API
