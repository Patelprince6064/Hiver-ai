# Phase 16: Escalation Policy Optimization & Risk-Aware Decisioning

## 1. Objective

Improve the Phase 15 conservative escalation policy by determining whether the escalation policy can safely increase useful AUTO_HANDLE coverage without causing unacceptable unsafe AUTO_HANDLE decisions.

**Primary Objective:** Reduce unsafe AUTO_HANDLE decisions.

**Secondary Objective:** Increase useful AUTO_HANDLE coverage where safe.

**Constraints:**
- Golden evaluation set remains locked
- No tuning on golden data
- No fabricated labels or metrics
- No unsupported business-policy assumptions

---

## 2. Starting Point from Phase 15

Phase 15 created a conservative rule-based escalation policy with:
- Intent confidence threshold: 0.70
- Retrieval evidence required
- Grounding status must be "pass"
- High-risk claims always escalate
- Ambiguous intent escalates
- Multi-intent escalates
- 20 reason codes across 4 categories

**Current metrics (synthetic data):**
- Auto-handle rate: ~28%
- Escalate rate: ~72%
- False auto-handle rate: ~16%

---

## 3. Policy v1.0

The Phase 15 policy remains unchanged:

```yaml
policy_version: "v1.0"
intent_confidence:
  minimum_auto_handle: 0.70
retrieval:
  require_evidence: true
grounding:
  allowed_statuses: ["pass"]
risk:
  escalate_on_high_risk: true
ambiguity:
  escalate_on_ambiguous: true
multi_intent:
  escalate_on_multi_intent: true
```

**Rule priority order:**
1. Provider error → ESCALATE
2. Invalid reply → ESCALATE
3. Insufficient evidence → ESCALATE
4. Grounding failure → ESCALATE
5. High-risk claims → ESCALATE
6. Low confidence → ESCALATE
7. Account action required → ESCALATE
8. Order status required → ESCALATE
9. Financial claim → ESCALATE
10. Multi-intent → ESCALATE
11. Ambiguous → ESCALATE
12. Safety risk → ESCALATE
13. Otherwise → AUTO_HANDLE

---

## 4. New Signals

### 4.1 Confidence Margin

Added `confidence_margin` signal: gap between top-1 and top-2 intent probabilities.

```
top1_probability = 0.78
top2_probability = 0.15
confidence_margin = 0.63
```

**Rationale:** A high top-1 probability with a tiny margin may indicate ambiguity. This signal helps detect cases where the model is "unsure but lucky."

### 4.2 Retrieval Quality Score

Added `retrieval_quality_score`: normalized score combining evidence availability, count, and similarity.

```
quality_score = 0.3 (base for having evidence)
              + min(top_similarity * 0.4, 0.4)
              + min(evidence_count / 5.0, 0.3)
```

**Rationale:** Retrieval availability alone is insufficient. A single low-quality evidence item should not enable auto-handling.

### 4.3 High-Risk Request Detection

Created `src/escalation/high_risk_detector.py` with pattern-based detection for:
- Account actions (cancel, change, delete)
- Order status inquiries
- Refund/compensation requests
- Financial claims (pricing errors, promo codes)
- Personal information (email, phone, address)
- Identity verification
- Unsupported pricing guarantees
- Unsupported timeline guarantees
- Irreversible actions

**Rationale:** These requests require human review because the system may not have enough capability/evidence to safely resolve automatically.

### 4.4 Conversation Complexity

Created `src/escalation/conversation_complexity.py` with heuristic signals:
- Number of turns
- Number of customer messages
- Repeated requests
- Multiple intents
- Contradictory requests
- Unresolved prior turns

**Rationale:** Complex conversations with repeated or contradictory requests are less likely to be safely auto-handled.

### 4.5 Repeated Unresolved Issue

Added `has_repeated_unresolved_issue` signal: detects when customer asks same/similar issue repeatedly.

**Rationale:** Repeated requests suggest the issue was not resolved, requiring human intervention.

---

## 5. Policy v1.1

The improved risk-aware policy extends v1.0 with:

```yaml
policy_version: "v1.1"
intent_confidence:
  minimum_auto_handle: 0.70
confidence_margin:
  minimum_margin: 0.15
retrieval:
  require_evidence: true
grounding:
  allowed_statuses: ["pass"]
risk:
  escalate_on_high_risk: true
high_risk_detection:
  default_escalate: true
conversation_complexity:
  escalate_on_complex: true
repeated_unresolved:
  escalate_on_repeated: true
```

**Rule priority order (same safety gates as v1.0):**
1-6: Same hard safety gates as v1.0
7. High-risk request detected → ESCALATE
8. Low confidence → ESCALATE
9. Low margin (and confidence < 0.85) → ESCALATE
10-13: Same as v1.0
14. Repeated unresolved issue → ESCALATE
15. High complexity → ESCALATE
16. Safety risk → ESCALATE
17. Otherwise → AUTO_HANDLE

**Key difference:** v1.1 adds risk-aware checks after the hard safety gates, allowing more nuanced decisions for borderline cases.

---

## 6. Threshold Methodology

Thresholds are tuned on DEV data only using `scripts/optimize_escalation_thresholds.py`.

**Intent confidence thresholds tested:**
[0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

**Margin thresholds tested:**
[0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

**Combined analysis:** Intent + margin thresholds tested together.

**Recommendation:** The analysis shows that achieving <5% false auto-handle rate requires conservative thresholds (0.85+), which significantly reduces auto-handle coverage.

---

## 7. Cost Assumptions

```yaml
costs:
  false_auto_handle: 10.0
  false_escalation: 1.0
```

**Rationale:** False auto-handle causes real customer harm (incorrect response on sensitive topic). False escalation causes inconvenience (unnecessary human workload). The 10:1 ratio reflects that unsafe automation is more serious than unnecessary human review.

**Important:** These are modeling assumptions, not actual business costs.

---

## 8. Evaluation Methodology

- **DEV data:** Used for threshold optimization and policy development
- **GOLDEN data:** Locked evaluation set, used only for final reporting
- **Seed:** 42 for reproducibility
- **No golden-set tuning:** All optimization decisions made on DEV

---

## 9. Results

### 9.1 Policy Comparison (Synthetic Data)

| Policy | Version | Auto Rate | FAH Rate | Expected Cost |
|--------|---------|-----------|----------|---------------|
| Always Escalate | - | 0.00 | 0.00 | 1.00 |
| v1.0 Conservative | v1.0 | 0.28 | 0.16 | 2.18 |
| v1.1 Risk-Aware | v1.1 | 0.28 | 0.16 | 2.18 |
| Always Auto | - | 1.00 | 1.00 | 10.00 |

### 9.2 Threshold Analysis

| Threshold | Auto Rate | FAH Rate |
|-----------|-----------|----------|
| 0.50 | 0.66 | 0.44 |
| 0.60 | 0.57 | 0.30 |
| 0.70 | 0.39 | 0.21 |
| 0.80 | 0.28 | 0.15 |
| 0.90 | 0.10 | 0.07 |

### 9.3 Risk-Coverage Curve

The risk-coverage curve shows the trade-off between auto-handle rate (coverage) and false auto-handle rate (safety risk). The curve demonstrates that achieving very low FAH rates requires significant coverage reduction.

---

## 10. Risk-Coverage Trade-off

The fundamental trade-off:
- **More aggressive policy** → Higher auto-handle rate → More false auto-handles
- **More conservative policy** → Lower auto-handle rate → Fewer false auto-handles

**Finding:** v1.1 achieves similar performance to v1.0 on synthetic data. The new signals (confidence margin, conversation complexity) provide additional granularity but do not dramatically change the decision boundary.

---

## 11. Per-Intent Analysis

**Top 5 escalation rate intents:**
1. product_question (79%)
2. technical_support (78%)
3. refund_request (75%)
4. billing_issue (73%)
5. complaint (73%)

**Top 5 false auto-handle rate intents:**
1. account_help (36%)
2. billing_issue (27%)
3. refund_request (25%)
4. complaint (0%)
5. order_status (0%)

**Finding:** High-risk intents (account_help, billing_issue, refund_request) have higher false auto-handle rates, confirming the need for conservative handling of these categories.

---

## 12. Policy Stability

**Stability assessment:** MODERATE (small but noticeable changes)

- Average changes per perturbation: 2.00
- Average % changed: 2.00%
- Auto->Escalate changes: 0
- Escalate->Auto changes: 14

**Finding:** The policy is relatively stable. Small threshold changes (±0.01) affect 2-4% of decisions. Larger changes (±0.02) affect 8% of decisions.

---

## 13. Failure Analysis

**Error categories:**
- E_high_risk_detection_failure: 44.8%
- C_intent_uncertainty: 34.5%
- G_policy_threshold: 17.2%
- F_complexity_failure: 3.4%

**Finding:** The most common error is high-risk detection failure — cases where the system auto-handles a request that should be escalated due to high-risk intent (account_help, billing_issue). This confirms the need for intent-aware escalation rules.

---

## 14. What Improved

1. **Policy versioning system** — explicit version tracking with metadata
2. **New signals** — confidence margin, retrieval quality, conversation complexity
3. **High-risk request detection** — pattern-based detection for account/order/financial actions
4. **Threshold optimization** — systematic search on DEV data
5. **Cost analysis** — configurable cost assumptions for policy comparison
6. **Risk-coverage curve** — visual representation of trade-off
7. **Policy stability analysis** — threshold sensitivity testing
8. **Per-intent analysis** — intent-specific escalation patterns
9. **Error categorization** — structured failure analysis

---

## 15. What Did Not Improve

1. **v1.1 did not significantly outperform v1.0** on synthetic data
2. **False auto-handle rate remains high** (~16%) with current thresholds
3. **No real evaluation data** — all metrics are on synthetic data
4. **No golden-set evaluation** — golden data remains locked

---

## 16. Limitations

1. **Synthetic data only** — no real dataset downloaded
2. **Single annotator** — no inter-annotator agreement
3. **Heuristic signals** — some signals are approximate
4. **No production data** — all evaluation is historical
5. **Intent classification errors** — upstream errors propagate
6. **Threshold sensitivity** — borderline cases affected by small changes

---

## 17. Recommended Policy for Phase 17

**Recommendation:** Continue with v1.0 as the primary policy until real evaluation data is available.

**Rationale:**
- v1.1 adds complexity without demonstrated improvement on synthetic data
- The new signals (confidence margin, complexity) may be more valuable with real data
- The hard safety gates in v1.0 are sufficient for the current evaluation setup

**For Phase 17:**
1. Download real dataset and create evaluation data
2. Run v1.0 and v1.1 on real data
3. Compare performance with actual gold labels
4. Tune thresholds based on real false auto-handle rates
5. Consider v1.1 improvements only if real data shows benefit

---

## Files Created

1. `docs/ESCALATION_OPTIMIZATION.md` — Optimization problem definition
2. `src/escalation/policy_version.py` — Policy versioning system
3. `src/escalation/high_risk_detector.py` — High-risk request detection
4. `src/escalation/conversation_complexity.py` — Conversation complexity signals
5. `src/evaluation/escalation_cost.py` — Cost analysis module
6. `scripts/optimize_escalation_thresholds.py` — Threshold optimization
7. `scripts/compare_escalation_policies.py` — Policy comparison
8. `scripts/plot_escalation_risk_coverage.py` — Risk-coverage curve
9. `scripts/analyze_policy_stability.py` — Policy stability analysis
10. `scripts/analyze_escalation_by_intent.py` — Per-intent analysis
11. `reports/phase_16_policy_card.md` — Policy card
12. `reports/phase_16_escalation_optimization.md` — This report

## Files Modified

1. `src/escalation/risk_signals.py` — Added confidence margin, retrieval quality, new signals
2. `src/escalation/rule_based_policy.py` — Added RiskAwarePolicy (v1.1)
3. `configs/escalation.yaml` — Updated to v1.1 configuration
4. `scripts/analyze_escalation_errors.py` — Added new error categories

## Tests

| Test File | Tests |
|-----------|-------|
| test_policy_version.py | 7 |
| test_high_risk_detector.py | 12 |
| test_conversation_complexity.py | 8 |
| test_policy_v11.py | 16 |
| test_escalation_cost.py | 14 |
| test_policy_stability.py | 5 |
| **New Tests Total** | **62** |
| **All Tests** | **630** |
