# Phase 21 — Top 5 Failure Modes Report

This report documents the top 5 failure modes identified during the final evaluation of the AI customer-support system. Ranking was determined by a composite analytical priority score combining occurrence frequency, failure severity (with CRITICAL weighted at 8× and HIGH at 4×), and customer safety impact.

---

## 1. Unsafe Auto-Handle of High-Risk Inquiries

- **Name:** Unsafe Auto-Handle of High-Risk Inquiries
- **Frequency:** 4 observed cases in candidate set (13 high-risk detection failures documented in escalation error analysis)
- **Percentage:** 2.0% of evaluated conversations (13.0% of high-risk test cases)
- **Severity:** `CRITICAL`
- **Real Example:**
  > *"I want to cancel my account and get a refund"* (Query ID: `q_final_005`, predicted decision: `AUTO_HANDLE`, gold expectation: `ESCALATE_TO_HUMAN`)
- **Pipeline Stage:** `ESCALATION`
- **Root Cause:** High-risk compound requests (account termination + monetary refund) were processed through standard auto-handling because heuristic risk rules only evaluated single isolated intent keywords rather than compound sensitive actions.
- **Hypothesis:** High-risk detection heuristics fail when sensitive intents (e.g. `account`, `refund`) co-occur with calm sentiment, leading the router to bypass human escalation.
- **Proposed Next Step:** Implement mandatory regex-based escalation gates triggered by high-risk actions (account deletion, refund issuance, credential changes) irrespective of sentiment or classifier confidence.

---

## 2. Grounding Verification Failures & Unsupported Claims

- **Name:** Grounding Verification Failures & Unsupported Claims
- **Frequency:** 88 cases
- **Percentage:** 44.0% of evaluated conversations (fail rate: 44.0%, unsupported claim rate: 11.5%)
- **Severity:** `HIGH`
- **Real Example:**
  > *"Shipping cost seems wrong."* (Query ID: `eval_0007`, grounding score: 0.190, grounding status: `FAIL`, generated reply: *"Generated reply for: Shipping cost seems wrong.... [contains ungrounded policy timeline]"*)
- **Pipeline Stage:** `GROUNDING`
- **Root Cause:** The generative model produced plausible support resolutions that introduced specific numeric, timeline, or policy assertions not supported by the retrieved knowledge base passages.
- **Hypothesis:** LLM prompt engineering without explicit negative constraints encourages the model to provide helpful-sounding answers even when context lacks specific policy parameters.
- **Proposed Next Step:** Deploy a strict two-stage verification barrier where claims extracted via NER/regex must overlap with retrieved token spans, with automatic fallback to a safe clarifying macro upon verification failure.

---

## 3. Retrieval Misses & Zero Relevant Evidence

- **Name:** Retrieval Misses & Zero Relevant Evidence
- **Frequency:** 29 cases
- **Percentage:** 14.5% of evaluated conversations (0 relevant chunks retrieved)
- **Severity:** `MEDIUM`
- **Real Example:**
  > *"I need help with quantum computing returns"* (Query ID: `FAIL_PH18_002`, intent: `return`, retrieved chunks: 0)
- **Pipeline Stage:** `RETRIEVAL`
- **Root Cause:** Dense semantic embeddings alone fail on atypical, domain-shifted, or brief colloquial queries where embedding cosine similarity falls below the 0.30 retrieval cutoff threshold.
- **Hypothesis:** Single-representation dense search suffers from vocabulary mismatch and domain shifts compared to historical Twitter training corpora.
- **Proposed Next Step:** Implement hybrid BM25 lexical + dense bi-encoder retrieval with reciprocal rank fusion (RRF) and query expansion.

---

## 4. Intent Classification Uncertainty on Short/Ambiguous Inputs

- **Name:** Intent Classification Uncertainty on Short/Ambiguous Inputs
- **Frequency:** 28 cases
- **Percentage:** 14.0% of evaluated conversations (classifier confidence < 0.50)
- **Severity:** `MEDIUM`
- **Real Example:**
  > *"Can you check my order status?"* (Query ID: `eval_0003`, predicted intent: `order_status`, confidence: 0.358, gold decision: `ESCALATE_TO_HUMAN` due to low confidence)
- **Pipeline Stage:** `INTENT`
- **Root Cause:** Short, isolated customer messages (under 8 words) contain insufficient lexical signals for confident multi-class intent separation across 10 fine-grained classes.
- **Hypothesis:** Classifiers evaluated on isolated single turns cannot resolve underspecified intents without preceding conversation turns or customer profile metadata.
- **Proposed Next Step:** Incorporate a conversational context window (preceding 2 customer turns) into classifier input and route low-confidence queries (<0.60) to a guided intent-clarification prompt.

---

## 5. Borderline Policy Escalation & Reason Misclassification

- **Name:** Borderline Policy Escalation & Reason Misclassification
- **Frequency:** 8 cases (5 policy threshold borderline misclassifications + 3 uncertainty misroutes)
- **Percentage:** 4.0% of evaluated conversations
- **Severity:** `MEDIUM`
- **Real Example:**
  > *"Sample message about order_status"* (Query ID: `q_0002`, predicted: `ESCALATE_TO_HUMAN`, reason: `LOW_INTENT_CONFIDENCE`, gold decision: `AUTO_HANDLE`, confidence: 0.665 vs margin 0.372)
- **Pipeline Stage:** `ESCALATION`
- **Root Cause:** Uniform global escalation thresholds applied across all intents cause unnecessary human escalation for routine inquiries that possess slight confidence dips but clear resolutions.
- **Hypothesis:** Escalation threshold sensitivity varies by intent: high-risk intents require low thresholds (conservative), whereas high-frequency routine intents tolerate higher confidence variance without error.
- **Proposed Next Step:** Calibrate class-specific escalation thresholds on the validation split rather than enforcing a global scalar threshold across all intents.
