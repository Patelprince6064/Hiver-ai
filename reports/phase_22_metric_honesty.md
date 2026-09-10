# Phase 22 — Metric Honesty & Headline Investigation

## 1. Objective

The objective of Phase 22 is to rigorously define, evaluate, and critique the primary headline metric for the Hiver AI Customer Support Agent. In direct response to the assignment prompt—*"What is misleading about my headline number?"*—this phase establishes an uncompromising standard of intellectual honesty. We identify the most meaningful metric, compare it against appropriate baselines, audit denominators, investigate sensitivity and gaming risks, and explicitly articulate what the number does **not** prove.

---

## 2. Candidate Headline Metrics

Five candidate metrics were formally evaluated using the selection criteria defined in `docs/HEADLINE_METRIC_SELECTION.md`:

1. **Verified Grounded Reply Quality Score (0.767):** Evaluates customer-facing answer quality across 6 rubric dimensions (Relevance, Groundedness, Correctness, Helpfulness, Completeness, Style).
2. **Intent Classification Macro F1 (0.857):** Measures multi-class classification discrimination across 10 balanced intent categories.
3. **Escalation Expected Cost (2.14):** Risk-weighted operational cost balancing human labor ($C_H = 1.0$) against customer dissatisfaction from missed escalations ($C_M = 10.0$).
4. **Grounding Verification Pass Rate (56.0%):** Rate at which candidate replies pass factual claim and entity checks without requiring repair or escalation.
5. **Auto-Handle Rate (70.0%):** Proportion of incoming requests handled autonomously without human agent involvement.

---

## 3. Selected Headline Metric

The selected primary headline metric is:

$$\textbf{Verified Grounded Reply Quality Score} = \mathbf{0.767} \quad (\text{on a } 0.0 - 1.0 \text{ scale})$$

- **Sample Size:** $N = 200$ test customer support conversations.
- **Evaluation Set:** Phase 18 Frozen Synthetic End-to-End Test Cohort.
- **Formula:** Mean across all 200 instances of the average 6-dimension score normalized to $[0.0, 1.0]$.
- **Justification:** An automated customer support agent is ultimately judged by the quality and safety of the answer it provides to the user. Upstream intent classification is merely an intermediate step, and high auto-handle rates can mask disastrous automated decisions. Reply quality directly measures the customer-facing output.

---

## 4. Supporting Metrics Package

To prevent deceptive metric isolation, the headline number is strictly bound to three supporting metrics:

| Metric Role | Metric Name | Value | Baseline | Delta | Key Operational Meaning |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **PRIMARY HEADLINE** | **Verified Reply Quality** | **0.767** | 0.500 | **+0.267** (+53.4%) | Final response quality delivered to the user |
| **Upstream Routing** | **Intent Macro F1** | **0.857** | 0.580 | **+0.277** (+47.8%) | Accuracy of categorizing user intent |
| **Operational Safety** | **Escalation Expected Cost** | **2.140** | 6.100 | **-3.960** (-64.9%) | Risk-weighted labor and error cost reduction |
| **Factual Integrity** | **Grounding Pass Rate** | **0.560** | 0.350 | **+0.210** (+60.0%) | Proportion of replies passing fact checks |

---

## 5. Baseline Comparison

A headline metric without a baseline is uninformative. We evaluated the final system against two distinct baselines:

1. **Historical Human Response Baseline (Strongest Baseline — 0.500):**
   - Retrieves the past human response previously sent by an agent for a similar historical issue.
   - Final system achieves **0.767 vs. 0.500**, representing an absolute gain of **+0.267** (+53.4% relative gain).
   - This proves that grounding an LLM in historical context produces more relevant, tailored replies than simply copy-pasting past human answers.
2. **Generic Template Baseline (0.265):**
   - Returns standard canned customer service macros.
   - Final system achieves **0.767 vs. 0.265**, an absolute gain of **+0.502** (+189.4% relative gain).

---

## 6. Confidence & Statistical Uncertainty

Using the sample standard deviation ($\sigma = 0.042$) across the $N = 200$ test set:
- **Standard Error:** $SE = \frac{0.042}{\sqrt{200}} \approx 0.00297$
- **95% Confidence Interval:** $[0.7612, 0.7728]$
- **Subgroup Stability:**
  - Easy cases: $0.785 \pm 0.008$
  - Hard cases: $0.724 \pm 0.012$
  - Common intents (`order_status`, `return`, `shipping`): $0.772 \pm 0.007$
  - Rare intents (`complaint`, `account`): $0.748 \pm 0.011$
- **Verdict:** The metric demonstrates narrow statistical variance on the evaluation set, but drops by ~0.05 on complex, edge-case inquiries.

---

## 7. Dataset Representativeness

- **Selected Brand Scoping:** The dataset is restricted to a single e-commerce/retail brand. Performance cannot be assumed to transfer to fintech, healthcare, or SaaS domains without re-indexing and re-evaluation.
- **Synthetic Test Generation:** Because the external Twitter customer support corpus was not downloaded, all 200 evaluation cases originate from a frozen synthetic generator. While systematically stratified across 10 intents and 3 difficulty tiers, it lacks the full morphological messiness (typos, slang, unpunctuated stream-of-consciousness) of live customer messages.

---

## 8. Denominator Audit

A common method of inflating AI performance is silent denominator shifting (e.g., calculating reply quality only over "successfully answered" tickets while ignoring failures). 

Our denominator audit (`evaluation/results/denominator_audit.json`) confirms:
- **Verified Reply Quality:** Evaluated over **all 200 incoming test requests**, including cases requiring grounding fallback templates or human escalation.
- **Auto-Handle Rate (70.0%):** Denominator is **all 200 eligible requests** ($140 / 200$), not a pre-filtered subset.
- **Unsupported Claim Rate (11.5%):** Denominator is **all 200 candidate replies** ($23 / 200$).
- **Unsafe Auto-Handle Rate (2.0%):** Evaluated over all 200 interactions ($4 / 200$), and also reported over the high-risk cohort ($4 / 31 = 12.9\%$).

---

## 9. Success Definition

The project explicitly rejects vague, hand-waving definitions of "AI Success". Success is defined along three independent, audited dimensions:
1. **Routing Success:** Classified into the correct intent with confidence $\ge 0.50$.
2. **Factual Success:** Passes token-span grounding verification without ungrounded claims.
3. **Policy Success:** Low-risk routine requests are auto-handled; high-risk actions are escalated.

A response is **not** labeled "successful" simply because the LLM generated fluent English.

---

## 10. Potential Sources of Metric Inflation

1. **Synthetic Grammar Cleanliness:** Synthetic inputs lack extreme spelling corruptions, leading to higher intent classification confidence than live Twitter streams.
2. **Template Macro Scoring:** Fallback template replies are grammatically polished, which inflates Style scores (0.760) even when the specific resolution requires follow-up.
3. **Strawman Baseline Framing:** Comparing against generic canned macros (+0.502 gain) creates a visually dramatic chart, whereas the genuine technical benchmark is the historical retrieval baseline (+0.267 gain).

---

## 11. What the Number Does NOT Prove

The headline number (**0.767**) does **NOT** prove:
1. **Customer Problem Resolution:** It does not verify that a package was delivered, a database record updated, or money returned to a bank account.
2. **Customer Satisfaction (CSAT):** It measures alignment with an internal evaluation rubric, not how a stressed customer feels.
3. **Escalation Safety:** Polished language can mask catastrophic policy errors; 4 high-risk account cancellations were auto-handled with high stylistic fluency.
4. **Generalization Across Organizations:** It reflects one brand's policies under one set of prompts.

---

## 12. What Is Misleading About It

If presented without context to an executive, **0.767** is easily misinterpreted as:
- *"The agent can resolve 77% of all customer tickets autonomously."* (False: Auto-handle rate is 70%, and resolution requires backend actions).
- *"The error rate is only 23%."* (False: Grounding failed on 44% of raw generations, and 2.0% of requests exhibited critical safety failures).

---

## 13. Skeptical Interviewer Questions Summary

- *Q: Why not use accuracy?* A: Accuracy is an intermediate routing step. A model with 90% intent accuracy can still hallucinate refund amounts in the reply.
- *Q: Could your metric be gamed?* A: We audited the full cohort; no hard cases or failed generations were excluded from the denominator.
- *Q: Does this prove production readiness?* A: No. A 2.0% unsafe auto-handle rate on critical account actions prevents production deployment without a deterministic safety gate.

*(Full 12-question defense is documented in `reports/skeptical_interviewer_questions.md`).*

---

## 14. Final Honest Interpretation

On a controlled 200-example synthetic support benchmark, grounding generative models in retrieved historical evidence and enforcing post-generation claim verification improves textual response quality from **0.500 to 0.767** over raw historical reuse. However, this number reflects offline rubric compliance under controlled conditions and must **not** be interpreted as autonomous production readiness, guaranteed factual truth, or real-world customer satisfaction.
