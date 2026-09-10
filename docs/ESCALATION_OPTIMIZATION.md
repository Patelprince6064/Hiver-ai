# Escalation Policy Optimization

## Problem Definition

### Primary Objective

Reduce unsafe AUTO_HANDLE decisions — cases where the system auto-handles a request that should have been escalated to a human.

### Secondary Objective

Increase useful AUTO_HANDLE coverage where safe — handle more requests automatically when there is strong evidence and low risk.

### Constraints

1. **Golden evaluation set remains locked** — no tuning on golden data
2. **No tuning on golden** — all threshold optimization uses DEV data only
3. **No fabricated labels** — all metrics are computed from actual data
4. **No fabricated metrics** — no placeholder or estimated numbers
5. **No unsupported business-policy assumptions** — no claims about what the business "should" do
6. **No autonomous account/order actions** — the system does not execute real-world changes

## Safety Principle

The most dangerous failure mode is:

```
System says: AUTO_HANDLE
when it should have: ESCALATE_TO_HUMAN
```

This is called a **false auto-handle** and is the primary safety metric to minimize.

### Why False Auto-Handle Is Worse Than False Escalation

| Failure Mode | Impact |
|--------------|--------|
| False Auto-Handle | Customer receives incorrect/incomplete response on sensitive topic (billing, legal, account) |
| False Escalation | Unnecessary human workload, slower response times |

False auto-handle causes **real harm** to customers. False escalation causes **inefficiency**.

## Trade-off: Coverage vs Safety

```
                    ┌─────────────────────────────────┐
                    │          SAFETY                  │
                    │   (minimize false auto-handles)  │
                    └─────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────┐
│                 COVERAGE                             │
│   (maximize useful auto-handling)                    │
└─────────────────────────────────────────────────────┘
```

### The Fundamental Trade-off

- **More aggressive policy** → Higher auto-handle rate → More false auto-handles
- **More conservative policy** → Lower auto-handle rate → Fewer false auto-handles

### Optimization Goal

Find the sweet spot where:
1. False auto-handle rate is acceptably low (safety constraint)
2. Auto-handle rate is as high as possible (coverage objective)

## Policy Versions

### v1.0 (Phase 15)

Conservative rule-based policy:
- Intent confidence threshold: 0.70
- Retrieval evidence required
- Grounding status must be "pass"
- High-risk claims always escalate
- Ambiguous intent escalates
- Multi-intent escalates

### v1.1 (Phase 16)

Improved risk-aware policy with:
- Confidence margin analysis
- Retrieval quality signals
- Grounding safety gates
- High-risk request detection
- Conversation complexity signals
- Repeated unresolved issue detection

## Evaluation Methodology

### Data Splits

- **DEV**: Used for threshold optimization and policy development
- **GOLDEN**: Locked evaluation set, used only for final reporting
- **No tuning on GOLDEN**: All optimization decisions are made on DEV

### Metrics

| Metric | Definition | Safety Critical |
|--------|------------|-----------------|
| AUTO_HANDLE_RATE | % of requests auto-handled | No |
| ESCALATE_RATE | % of requests escalated | No |
| FALSE_AUTO_HANDLE_RATE | % of escalated requests that were auto-handled | **YES** |
| FALSE_ESCALATION_RATE | % of auto-handle requests that were escalated | No |
| ACCURACY | % of correct decisions | No |

### Primary Optimization Objective

```
minimize: FALSE_AUTO_HANDLE_RATE
subject to: AUTO_HANDLE_RATE >= configurable_threshold
```

### Safety Constraint

```
FALSE_AUTO_HANDLE_RATE <= safety_target
```

The safety target is a **policy constraint**, not an industry standard. It reflects the organization's risk tolerance.

## Cost Analysis

### Assumed Costs (Modeling Assumptions)

| Error Type | Assumed Cost | Rationale |
|------------|--------------|-----------|
| False Auto-Handle | 10 | Real customer harm, potential legal/regulatory issues |
| False Escalation | 1 | Inconvenience, slower response time |

**Important**: These are modeling assumptions, not actual business costs. They reflect that unsafe automation is more serious than unnecessary human review.

### Expected Policy Cost

```
Expected Cost = (False Auto-Handle Rate × Cost) + (False Escalation Rate × Cost)
```

## Limitations

1. **Single annotator** — no inter-annotator agreement measurement
2. **No production data** — all evaluation is on historical data
3. **Heuristic signals** — some signals are approximate
4. **Threshold sensitivity** — small changes may affect decisions
5. **Intent classification errors** — upstream errors propagate to escalation

## Commands

```bash
# Optimize thresholds on DEV data
python scripts/optimize_escalation_thresholds.py

# Compare policies
python scripts/compare_escalation_policies.py

# Plot risk-coverage curve
python scripts/plot_escalation_risk_coverage.py

# Analyze policy stability
python scripts/analyze_policy_stability.py

# Analyze per-intent escalation
python scripts/analyze_escalation_by_intent.py

# Analyze escalation errors
python scripts/analyze_escalation_errors.py
```
