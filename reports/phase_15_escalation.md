# Phase 15: Auto-Handle vs Human Escalation

## Objective
Define clear rules for when the AI system can auto-handle a query vs when it must escalate to a human agent, prioritizing safety (no under-escalation) over coverage.

## Key Files

| File | Purpose |
|------|---------|
| `configs/escalation.yaml` | Configurable thresholds and policy parameters |
| `src/escalation/escalation_schema.py` | EscalationDecision Pydantic model |
| `src/escalation/reason_codes.py` | 20 ReasonCode enum values |
| `src/escalation/risk_signals.py` | RiskSignals dataclass, signal extraction |
| `src/escalation/rule_based_policy.py` | RuleBasedPolicy with configurable thresholds |
| `src/escalation/decision_engine.py` | Main EscalationDecisionEngine |
| `src/escalation/baselines.py` | AlwaysAutoHandle, AlwaysEscalate baselines |
| `src/evaluation/escalation_metrics.py` | EscalationMetrics, threshold analysis |
| `scripts/evaluate_escalation.py` | Run evaluation on dev split |
| `scripts/analyze_escalation_tradeoff.py` | Threshold tradeoff analysis |
| `scripts/analyze_escalation_errors.py` | Error categorization |
| `docs/ESCALATION_POLICY.md` | Decision rules, Mermaid diagram |
| `docs/ESCALATION_ANNOTATION_GUIDE.md` | Annotation guidelines |

## Policy v1.0

- Minimum intent confidence for auto-handle: **0.70**
- Retrieval evidence required: **yes**
- Grounding status must be: **pass**
- High-risk reasons always escalate: **yes**
- Ambiguous intent escalates: **yes**
- Multi-intent escalates: **yes**

## 20 Reason Codes

**High Risk (always escalate):** BILLING_CLAIM, PERSONAL_INFO, CANCELLATION_REQUEST, REFUND_REQUEST, LEGAL_THREATS, THREATS_ABUSE, ACCOUNT_SECURITY

**Retrieval:** RETRIEVAL_LOW_SCORE, RETRIEVAL_NO_EVIDENCE, INSUFFICIENT_CONTEXT

**Grounding:** UNSUPPORTED_CLAIMS, GROUNDING_FAILED

**Policy:** LOW_INTENT_CONFIDENCE, AMBIGUOUS_INTENT, MULTI_INTENT, LOW_REPLY_CONFIDENCE, MISSING_INSTRUCTION, FINANCIAL_CLAIM, ACCOUNT_SPECIFIC, EMOTIONAL_CUSTOMER

## Key Safety Metric

**FALSE_AUTO_HANDLE_RATE**: Rate of cases where system auto-handles but gold label is ESCALATE_TO_HUMAN. Target: <5%.

## Results

| Metric | Value |
|--------|-------|
| Auto-Handle Rate | ~40% (placeholder) |
| Escalate Rate | ~60% (placeholder) |
| False Auto-Handle Rate | <5% (target) |

Actual metrics pending dataset download and real evaluation.

## Threshold Analysis

Analyzed tradeoff between auto-handle rate and false auto-handle rate at thresholds [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95].

Current recommendation: **0.70** (default) — balances coverage with safety.

## Files Created

1. `configs/escalation.yaml`
2. `src/escalation/__init__.py`
3. `src/escalation/escalation_schema.py`
4. `src/escalation/reason_codes.py`
5. `src/escalation/risk_signals.py`
6. `src/escalation/rule_based_policy.py`
7. `src/escalation/decision_engine.py`
8. `src/escalation/baselines.py`
9. `src/evaluation/escalation_metrics.py`
10. `scripts/evaluate_escalation.py`
11. `scripts/analyze_escalation_tradeoff.py`
12. `scripts/analyze_escalation_errors.py`
13. `scripts/annotate_escalation.py`
14. `docs/ESCALATION_POLICY.md`
15. `docs/ESCALATION_ANNOTATION_GUIDE.md`

## Tests

| Test File | Tests |
|-----------|-------|
| test_escalation_schema.py | ~10 |
| test_escalation_policy.py | ~15 |
| test_escalation_metrics.py | ~10 |
| test_escalation_baselines.py | ~8 |
| test_escalation_signals.py | ~12 |
| **Total** | **~55** |

## Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| 133 | Conservative escalation: uncertain → ESCALATE | Safety-first: under-escalation costs more than over-escalation |
| 134 | 20 reason codes across 4 categories | Granular, actionable escalation reasons |
| 135 | Rule-based policy over learned | Explainable, auditable, easy to tune for production |
| 136 | Confidence threshold 0.70 default | Balanced: ~40% auto-handle, ~60% escalate |
| 137 | HIGH_RISK as separate from retrieval/grounding | Billing, legal, threats always escalate regardless of other signals |
| 138 | False Auto-Handle Rate as primary safety metric | Most critical: wrong auto-handle on billing/threat = real harm |
| 139 | Threshold analysis with plot | Enables data-driven threshold tuning |
| 140 | Annotator guideline: "when in doubt, escalate" | Reduces false auto-handles at cost of more escalations |
| 141 | Pydantic EscalationDecision for schema validation | Structured, validated output for downstream systems |

## Next Phase
Phase 16: Production deployment readiness
