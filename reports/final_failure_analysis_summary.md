# Executive Summary — Final Failure Analysis & Root-Cause Investigation

**Project:** Hiver AI Support Agent (Phase 21)  
**Evaluation Scope:** 200 End-to-End Test Conversations | 160 Extracted Failure Signals  
**Core Finding:** The agent demonstrates high intent accuracy (85.5%) and strong baseline escalation policy stability (69% accuracy). However, the primary operational risks reside in two distinct stages: (1) **Grounding/Generation**, where 44.0% of outputs fail evidence verification thresholds due to speculative details, and (2) **Escalation**, where a rare but critical 2.0% of cases represent unsafe auto-handling of high-risk account or monetary requests.

---

## Top 5 Failure Modes Summary Matrix

| Rank | Failure Mode | Severity | Frequency (%) | Pipeline Stage | Primary Root Cause |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **Unsafe Auto-Handle of High-Risk Inquiries** | `CRITICAL` | 4 cases (2.0%) | ESCALATION | High-risk compound actions bypassed heuristic rule triggers |
| **2** | **Grounding Verification & Unsupported Claims** | `HIGH` | 88 cases (44.0%) | GROUNDING | Generation models hallucinated specific ungrounded policies/dates |
| **3** | **Retrieval Misses (Zero Evidence)** | `MEDIUM` | 29 cases (14.5%) | RETRIEVAL | Dense embeddings missed atypical or domain-shifted queries |
| **4** | **Intent Uncertainty on Short Queries** | `MEDIUM` | 28 cases (14.0%) | INTENT | Brief single-turn messages lacked lexical features (conf < 0.50) |
| **5** | **Borderline Policy Escalation Errors** | `MEDIUM` | 8 cases (4.0%) | ESCALATION | Rigid uniform scalar thresholds misclassified routine inquiries |

---

## Detailed Failure Mode Breakdowns

### 1. Unsafe Auto-Handle of High-Risk Requests (`CRITICAL`)
- **Real Example:** *"I want to cancel my account and get a refund"* (Query ID: `FAIL_PH18_005`, predicted: `AUTO_HANDLE`, gold: `ESCALATE_TO_HUMAN`).
- **Root-Cause Hypothesis:** Heuristic risk rules evaluated intents in isolation; when an account inquiry expressed calm sentiment, compound destructive/financial actions bypassed escalation.
- **Next-Week Plan:** Implement a deterministic pre-classifier regex filter that enforces mandatory human escalation on all account deletion, dispute, or refund execution requests.

### 2. Grounding Verification Failures & Unsupported Assertions (`HIGH`)
- **Real Example:** *"Shipping cost seems wrong."* (Query ID: `eval_0007`, grounding score: 0.190, status: `FAIL`).
- **Root-Cause Hypothesis:** When retrieved context contains general guidelines rather than exact numbers, LLM generation attempts to provide a helpful answer by guessing timeline or price specifics.
- **Next-Week Plan:** Deploy rigid negative prompt constraints ("Never provide exact fees unless explicitly stated in evidence") and an automated macro-fallback upon grounding score failure.

### 3. Retrieval Misses & Zero Evidence Retrieved (`MEDIUM`)
- **Real Example:** *"I need help with quantum computing returns"* (Query ID: `FAIL_PH18_002`, 0 chunks retrieved).
- **Root-Cause Hypothesis:** Dense semantic bi-encoders fail when query vocabulary diverges sharply from knowledge base indexing terms, falling below the similarity threshold.
- **Next-Week Plan:** Implement hybrid BM25 lexical + dense vector search combined via Reciprocal Rank Fusion (RRF) with synonym expansion.

### 4. Intent Classification Uncertainty on Brief Messages (`MEDIUM`)
- **Real Example:** *"Can you check my order status?"* (Query ID: `eval_0003`, confidence: 0.358).
- **Root-Cause Hypothesis:** Isolated single-turn queries under 8 words do not supply sufficient signal to distinguish between related classes (e.g., `order_status` vs `shipping`).
- **Next-Week Plan:** Integrate multi-turn conversational history into classification inputs and route queries with confidence < 0.60 to a lightweight intent-clarification prompt.

### 5. Borderline Policy Escalation Errors (`MEDIUM`)
- **Real Example:** *"Sample message about order_status"* (Query ID: `q_0002`, predicted: `ESCALATE_TO_HUMAN`, gold: `AUTO_HANDLE`, confidence: 0.665).
- **Root-Cause Hypothesis:** A single global confidence cutoff (0.70) is too conservative for routine, low-risk categories like `order_status` or `return`.
- **Next-Week Plan:** Calibrate category-specific confidence thresholds on validation data, allowing higher operational autonomy on routine inquiries while maintaining strict conservatism on sensitive tasks.

---

## Key Takeaway for System Deployment

1. **Do Not Trust Unconstrained LLM Generation:** Grounding checks are vital; 44% of raw generation required blocking or repair.
2. **Safety Must Be Deterministic:** Escalating critical financial/account actions cannot rely on probabilistic model confidence; rule-based safety nets are indispensable.
3. **Upstream Bottlenecks Propagate:** Improving retrieval recall directly alleviates generation hallucinations by supplying the necessary grounding evidence.
