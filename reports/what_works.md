# Phase 21 — What Works Well

A rigorous evaluation requires understanding not only what fails, but what components operate reliably and safely. This document summarizes the empirically verified strengths of the AI customer-support system across Phases 1–20.

---

## 1. Strongest Intent Categories

Across the 200 evaluated test cases and intent benchmark splits:

1. **`product_inquiry` & `billing`:** Achieved high F1 scores (>0.90) with clean lexical separation. Queries in these categories contain distinct domain vocabulary (e.g., "specifications", "features", "invoice", "charge") that are reliably classified.
2. **`general_inquiry`:** Strong baseline performance with low false positive escalation rate when clear greetings or general store policy questions are present.
3. **Semantic Classifier Superiority:** The semantic embedding classifier attained **85.5% overall accuracy** and **0.82 Macro F1**, outperforming the TF-IDF baseline (65% accuracy) by +20.5% and majority baseline (10% accuracy) by +75.5%.

---

## 2. Strongest Pipeline Stages

1. **Intent Classification Stage:**
   - 85.5% accuracy across all intents.
   - Fast inference latency (~50ms).
   - Serves as a stable upstream foundation for downstream retrieval filtering.
2. **Escalation Policy Architecture (V1.1 Risk-Aware):**
   - Outperformed naive baselines (`AlwaysAuto` at 39% accuracy, expected cost 10.0; `AlwaysEscalate` at 61% accuracy, cost 1.0).
   - Achieved **69.0% policy accuracy** with an expected cost of **2.18**, demonstrating an effective balance between operational handling and escalation protection.
   - Correctly handles routine, low-risk cases with high confidence without human intervention.
3. **Automated Safety & Claim Detection:**
   - The grounding verifier successfully identified **100% of synthetic injected ungrounded claims** during verification benchmarks.
   - Zero cases of silent corruption: whenever evidence was missing or unsupported assertions were made, the verifier actively flagged the output as `FAIL` or `REVIEW`.

---

## 3. Reliable Reply Categories

- **Standard Policy FAQs:** Inquiries regarding return time windows, basic shipping timelines, and operating hours are handled with high accuracy and high human review scores (3.0/3.0 human rating).
- **Template-Grounded Greetings & Acknowledgment:** Standard customer greetings and acknowledgments consistently score 5/5 in style and relevance under LLM-as-judge evaluation.

---

## 4. Historical Retrieval Efficacy

Historical conversation retrieval operates effectively when:
- Queries contain specific order-tracking terminology or return conditions (e.g., "original packaging", "damaged in transit").
- FAISS dense retrieval achieved a **Recall@5 of 0.75**, outperforming standard lexical BM25 search (0.30 Recall@5) by **+45.0 percentage points**.
- Retrieved historical agent replies provide high-quality stylistic phrasing and polite resolution cadences that grounded generators emulate effectively.

---

## 5. Grounded Generation Benefits

- **Hallucination Prevention:** By constraining generator context to retrieved historical snippets, factual hallucination was reduced from 35% (in ungrounded LLM generation) to **11.5%** in grounded generation.
- **Human Quality Scores:** Grounded LLM generation achieved an average reply score of **0.75** (vs. 0.30 for generic template baseline and 0.50 for raw historical reuse baseline), representing a **+0.45 improvement** over generic replies.
- **Repair Pipeline:** The automated repair pipeline successfully recovered 50% of borderline ungrounded claims by pruning speculative sentences and replacing them with verified macros.

---

## 6. Safe Escalation Behavior

- **Clean Escalation on Explicit Uncertainty:** In 100% of test cases where intent confidence was explicitly below 0.40, the system escalated to a human agent rather than guessing.
- **Clear Audit Trail:** Every escalation decision records structured reason codes (`LOW_INTENT_CONFIDENCE`, `HIGH_RISK_REQUEST`, `UNVERIFIED_CLAIM`), enabling human supervisors to understand routing rationale immediately.
