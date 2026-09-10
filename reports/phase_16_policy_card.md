# Phase 16 Policy Card

## Policy: v1.1 (Risk-Aware)

**Purpose:** Risk-aware escalation policy that maximizes safe automation while minimizing unsafe auto-handling.

**Created:** Phase 16

---

## Inputs

| Signal | Source | Description |
|--------|--------|-------------|
| Intent confidence | Semantic classifier | Model confidence score for predicted intent |
| Confidence margin | Semantic classifier | Gap between top-1 and top-2 intent probabilities |
| Retrieval availability | Retriever | Whether historical evidence was found |
| Retrieval quality | Retriever | Score combining evidence count and similarity |
| Grounding status | Grounding verifier | pass/review/fail/insufficient_evidence |
| High-risk claims | Grounding verifier | Unsupported claims detected in reply |
| High-risk request | Request detector | Account/order/financial/refund patterns |
| Conversation complexity | Conversation analyzer | Turn count, repeated requests, contradictions |
| Repeated unresolved | Conversation analyzer | Same issue asked multiple times |

---

## Decision Rules

### Hard Safety Gates (Always Escalate)

1. **Provider error** → ESCALATE_TO_HUMAN
2. **Invalid reply** → ESCALATE_TO_HUMAN
3. **Insufficient evidence** → ESCALATE_TO_HUMAN
4. **Grounding failure** → ESCALATE_TO_HUMAN

### Risk Detection (Escalate by Default)

5. **High-risk claims** (price, timeline, refund) → ESCALATE_TO_HUMAN
6. **High-risk request** (account action, order status, financial) → ESCALATE_TO_HUMAN

### Intent Confidence

7. **Low confidence** (< 0.70) → ESCALATE_TO_HUMAN
8. **Low margin** (< 0.15) AND **confidence** (< 0.85) → ESCALATE_TO_HUMAN

### Account/Order Actions

9. **Account action required** → ESCALATE_TO_HUMAN
10. **Order status required** → ESCALATE_TO_HUMAN
11. **Financial claim** → ESCALATE_TO_HUMAN

### Multi-Intent and Ambiguity

12. **Multi-intent** → ESCALATE_TO_HUMAN
13. **Ambiguous** → ESCALATE_TO_HUMAN

### Complexity

14. **Repeated unresolved issue** → ESCALATE_TO_HUMAN
15. **High complexity** → ESCALATE_TO_HUMAN
16. **Safety risk** → ESCALATE_TO_HUMAN

### Default

17. **Otherwise** → AUTO_HANDLE

---

## Safety Priority

**Minimize unsafe auto-handling.**

The most dangerous failure is:
- System says: AUTO_HANDLE
- Should have: ESCALATE_TO_HUMAN

This policy prioritizes not making harmful mistakes over maximizing coverage.

---

## Known Limitations

1. **Single annotator** — no inter-annotator agreement measurement
2. **Heuristic signals** — some signals are approximate (e.g., repeated unresolved detection)
3. **No production data** — all evaluation is on historical data
4. **Intent classification errors** — upstream errors propagate to escalation
5. **Threshold sensitivity** — small changes may affect borderline cases

---

## Configuration

```yaml
policy_version: "v1.1"
intent_confidence:
  minimum_auto_handle: 0.70
confidence_margin:
  minimum_margin: 0.15
grounding:
  allowed_statuses:
    - "pass"
risk:
  escalate_on_high_risk: true
conversation_complexity:
  escalate_on_complex: true
repeated_unresolved:
  escalate_on_repeated: true
costs:
  false_auto_handle: 10.0
  false_escalation: 1.0
```

---

## Comparison with v1.0

| Aspect | v1.0 | v1.1 |
|--------|------|------|
| Intent confidence | ✓ | ✓ |
| Confidence margin | - | ✓ |
| Retrieval quality | - | ✓ |
| High-risk claims | ✓ | ✓ |
| High-risk request | - | ✓ |
| Conversation complexity | - | ✓ |
| Repeated unresolved | - | ✓ |

---

## Reproducibility

- **Policy version:** v1.1
- **Config version:** v1.1
- **Seed:** 42
- **Evaluation set:** DEV split (not golden)
- **No golden-set tuning**
