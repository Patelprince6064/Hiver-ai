# Phase 21 — Next-Week Improvement Hypotheses

> [!IMPORTANT]
> **Analytical Note:** The improvements proposed in this document are *working hypotheses* derived from Phase 21 failure evidence. They have NOT yet been implemented or validated. They represent prioritized engineering experiments recommended for subsequent work.

---

## Hypothesis 1: Hard Escalation Gate for High-Risk Compound Actions

- **Failure:** Unsafe auto-handle of high-risk requests (e.g., account cancellation with refund).
- **Evidence:** 4 observed critical failures in evaluation outputs; 13 high-risk detection failures documented in `escalation_error_analysis.json`.
- **Hypothesis:** High-risk requests often feature compound user intents (such as combining account operations with financial refunds). Single-label classifiers or calm sentiment scores bypass heuristic thresholds. Implementing an upstream regex/keyword hard-gate independent of model confidence will catch 100% of these critical cases.
- **Proposed Experiment:**
  1. Define a deterministic high-risk action registry (e.g., `cancel.*account`, `refund.*dispute`, `chargeback`, `legal`, `stolen.*card`).
  2. Evaluate policy decisions with this filter placed as a pre-classifier routing gate.
- **Success Metric:** Unsafe auto-handle rate reduces from 2.0% to 0.0% on evaluation set.
- **Expected Risk:** Pre-classifier keyword matching may create false positive escalations on benign informational queries (e.g., "What is your account cancellation policy?"), increasing human agent load.

---

## Hypothesis 2: Two-Stage Claim Verification with Macro Fallback

- **Failure:** Grounding verification failures and unsupported claims (44.0% fail rate, 11.5% unsupported claims).
- **Evidence:** 88 evaluated cases failed grounding score thresholds; LLM generator hallucinated specific numeric timelines and policy exceptions not present in evidence.
- **Hypothesis:** Generative models tend to complete conversational cadences by inventing plausible operational details when the retrieved snippet is generic. Restricting generation prompts with strict negative constraints ("If evidence does not contain exact dates, state that support will verify") coupled with deterministic claim-to-evidence span matching will eliminate ungrounded assertions.
- **Proposed Experiment:**
  1. Extract factual triples (entity, attribute, value) from the candidate reply using a lightweight claim extractor.
  2. Check exact string or high-cosine token overlap against retrieved context.
  3. If verification score < 0.70, replace the speculative portion with a pre-approved safe template macro.
- **Success Metric:** Unsupported claim rate decreases from 11.5% to < 3.0%; Grounding pass rate increases from 56.0% to >= 85.0%.
- **Expected Risk:** Fallback to generic template macros may reduce perceived conversational naturalness or customer satisfaction on open-ended queries.

---

## Hypothesis 3: Hybrid Lexical-Dense Retrieval with Reciprocal Rank Fusion

- **Failure:** Retrieval misses on short, specific, or atypical inquiries (14.5% zero-evidence rate).
- **Evidence:** 29 evaluated queries retrieved zero relevant evidence items due to cosine similarity falling below the 0.30 cutoff threshold.
- **Hypothesis:** Bi-encoder dense embeddings struggle with exact keywords, domain-specific terminology, and short queries. Combining BM25 lexical keyword matching with dense embedding similarity using Reciprocal Rank Fusion (RRF) will capture exact lexical matches that dense search overlooks.
- **Proposed Experiment:**
  1. Build a BM25 index over the existing knowledge base corpus.
  2. Implement RRF ranking: $RRF\_Score(d) = \sum_{m \in \{dense, BM25\}} \frac{1}{60 + rank_m(d)}$.
  3. Re-evaluate Recall@5 and evidence coverage on the 200 evaluation queries.
- **Success Metric:** Recall@5 increases from 0.75 to >= 0.85; Zero-retrieval rate drops from 14.5% to < 5.0%.
- **Expected Risk:** Lexical indexing increases memory overhead and introduces sensitivity to customer typos and colloquial Twitter misspellings.

---

## Hypothesis 4: Context-Aware Multi-Turn Intent Classification

- **Failure:** Low classifier confidence (<0.50) on short or ambiguous messages (14.0% rate).
- **Evidence:** 28 cases exhibited low intent confidence (e.g., "Can you check my order status?" at 0.358 confidence), causing routing hesitation or fallback escalation.
- **Hypothesis:** Single-turn messages lack sufficient token length for confident discrimination among overlapping classes (e.g., `order_status` vs `shipping`). Concatenating preceding customer messages or session metadata will increase classification confidence and accuracy.
- **Proposed Experiment:**
  1. Format input as: `[Context: <prior_turns>] [Current: <customer_message>]`.
  2. Fine-tune / embed concatenated representations and test classification confidence distributions.
- **Success Metric:** Proportion of predictions with confidence < 0.50 drops by >= 40%; Intent classification Macro F1 increases from 0.82 to >= 0.88.
- **Expected Risk:** Historical context turns may introduce stale topic noise that distracts the classifier from the customer's immediate new question.

---

## Hypothesis 5: Intent-Calibrated Escalation Thresholds

- **Failure:** Borderline threshold escalations and escalation reason misclassifications (4.0% rate).
- **Evidence:** 8 cases were escalated unnecessarily or misclassified due to a uniform global confidence threshold (e.g., Query `q_0002` at 0.665 confidence).
- **Hypothesis:** A single global confidence threshold (e.g., 0.70) is suboptimal across heterogeneous intents. High-volume routine intents with predictable template resolutions (e.g., `general_inquiry`, `return`) can safely operate at a lower threshold (0.55), while high-risk intents (`account`, `refund`) require higher thresholds (0.80).
- **Proposed Experiment:**
  1. Compute ROC curves and cost-optimal thresholds separately per intent category on the validation split.
  2. Replace scalar threshold with an intent-indexed configuration table.
- **Success Metric:** Escalation policy accuracy increases from 69.0% to >= 76.0%; Expected operational cost decreases from 2.18 to < 1.70.
- **Expected Risk:** Over-tuning thresholds per intent class on small validation samples could lead to overfitting on non-representative edge cases.
