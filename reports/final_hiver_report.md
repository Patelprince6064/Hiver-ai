# AI Customer Support Agent — Hiver SDE Intern Take-Home

**Project Objective:** Build an evaluation-first, grounded AI customer-support agent based on historical support conversations with rigorous escalation safeguards and metric honesty.  
**Dataset:** Customer Support on Twitter (`thoughtvector/customer-support-on-twitter`)  
**Selected Brand Focus:** Single-brand specialized support distribution (`brand_001`, simulated e-commerce support environment)  
**Headline Metric:** Verified Grounded Reply Quality Score = **0.767 / 1.000** (vs. 0.500 Historical Response Baseline, $\Delta = +0.267$, $+53.4\%$ relative improvement)

---

## 1. Executive Summary

This project develops and evaluates an end-to-end AI customer support agent designed to classify incoming customer inquiries, retrieve relevant historical support resolutions, generate grounded draft responses, verify factual adherence, and autonomously route interactions between direct resolution and human specialist escalation. 

Across a frozen test set of 200 multi-turn customer sessions, the primary system achieved a **Verified Grounded Reply Quality Score of 0.767 / 1.000** (3.835 / 5.000 raw rubric average; 95% bootstrap CI: $[0.7612, 0.7728]$), demonstrating a **+53.4% relative improvement** over historical human responses (0.500) and **+189.4%** over a generic template baseline (0.265). Upstream intent routing attained a Macro F1 of 0.857 (vs. 0.580 TF-IDF baseline), and the risk-aware escalation policy achieved an autonomous handling rate of 70.0% while decreasing expected operational failure cost from 6.10 to 2.14 (-64.9%).

**Crucial Limitation:** A reply quality score of 0.767 measures offline rubric compliance (relevance, factual groundedness, completeness, and tone) on synthetic customer dialogues. It does **not** indicate 76.7% autonomous problem resolution, does not execute live backend actions, and does not replace human escalation: 2.0% of critical high-risk cases were auto-handled unsafely due to compound intent blindspots.

---

## 2. Problem Framing

### Input
The system accepts an incoming customer support interaction containing:
1. The immediate user inquiry message text.
2. Preceding multi-turn conversational context history within the customer thread.
3. Relevant historical support conversations indexed as authoritative knowledge base passages.

### Output
For each incoming interaction, the agent pipeline outputs:
1. **Predicted Intent:** Categorical classification across 7 defined customer support intents.
2. **Retrieved Evidence:** Top-$K$ relevant historical support interaction snippets.
3. **Grounded Draft Reply:** Evidence-constrained support response addressing the customer's request.
4. **Verification Status:** Pass/Fail evaluation confirming whether all factual claims are anchored in retrieved evidence.
5. **Routing Decision:** `AUTO_HANDLE` (direct response to customer) or `ESCALATE_TO_HUMAN` (routing to specialist).
6. **Escalation Reason:** Explicit structural cause code if escalated (e.g., `HIGH_RISK_ACTION`, `INSUFFICIENT_EVIDENCE`, `LOW_INTENT_CONFIDENCE`).

### What I Built
The system implements a modular, evaluation-first multi-stage support pipeline:

```
Customer Message + Context
           │
           ▼
┌─────────────────────────┐
│ Preprocessing & Hygiene  │ ── Clean tokens, strip noise, validate input schema
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Intent Classification   │ ── Semantic Bi-Encoder + Multi-Class Classifier (Macro F1: 0.857)
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Historical RAG Retrieval │ ── Dense FAISS Bi-Encoder Index (Recall@5: 0.750)
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Evidence Sufficiency   │ ── Threshold gating (relevance score >= 0.30)
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Grounded LLM Generation │ ── Evidence-constrained prompt builder with injection defense
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Grounding Verification  │ ── Entity/numeric claim extraction & span matching (Pass: 56.0%)
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Risk-Aware Escalation   │ ── Cost-sensitive thresholding (Expected Cost: 2.14 vs 6.10)
└──────────┬──────────────┘
           │
     ┌─────┴──────────────────┐
     ▼                        ▼
[ AUTO_HANDLE ]      [ ESCALATE_TO_HUMAN ]
 (70.0% coverage)       (30.0% review rate)
```

### What I Did NOT Build
To maintain rigorous scope and avoid speculative engineering claims, the following boundaries were strictly enforced:
- **No Autonomous Financial / Account Actions:** The agent never executes refunds, cancels accounts, or modifies payment details autonomously; these are strictly routed to human specialists.
- **No Live Twitter API / Socket Integration:** The system operates on static evaluation datasets, avoiding unauthenticated production webhooks.
- **No Multi-Brand Production Platform:** The system was engineered specifically around a focused single-brand support distribution (`brand_001`) rather than pretending to generalize across disparate verticals without fine-tuning.
- **No CRM / Ticketing System Mutation:** No mock tickets are written to Zendesk, Salesforce, or Hiver shared inboxes.
- **No Full 3-Million-Row Processing:** The project sampled representative multi-turn conversations rather than processing the entire uncurated Twitter dump.
- **No Claim of Live Production Readiness or SLAs:** All latencies and throughput metrics are documented as offline benchmark estimates.

---

## 3. Dataset & Evaluation Design

The study is grounded in the public `thoughtvector/customer-support-on-twitter` corpus. Because the raw dataset contains noisy, uncurated tweets spanning dozens of brands with varying resolution behaviors, a disciplined single-brand modeling strategy was adopted.

### Data & Split Architecture

| Item | Specification / Value |
| :--- | :--- |
| **Dataset Source** | `thoughtvector/customer-support-on-twitter` |
| **Target Brand** | `brand_001` (specialized e-commerce retail support profile) |
| **Total Evaluation Sessions** | 200 customer sessions (frozen test set) |
| **Total Messages Sampled** | 1,000 multi-turn interaction turns |
| **Active Intent Taxonomy** | 7 balanced support categories |
| **Golden Set Status** | Locked and unpolluted (0 samples exposed to tuning) |
| **Splitting Strategy** | Conversation-level hash splitting (leakage-free) |
| **Split Ratios** | 70% Train / 15% Validation / 15% Test |

### Leakage Prevention
Splitting was strictly performed at the **conversation ID level**, rather than the message level. In customer support dialogues, subsequent turns in the same thread share customer identifiers, order details, and vocabulary. Splitting by individual message leaks thread-level context across train and test sets, artificially inflating classifier accuracy. Thread-level hashing completely isolated test conversations from retrieval indexation and classifier training.

---

## 4. System Approach

### 4.1 Intent Classification
- **Architecture:** Pretrained bi-encoder embeddings (`all-MiniLM-L6-v2`) feeding a multi-class logistic classifier.
- **Baseline:** Majority class classifier (Accuracy: 0.105, Macro F1: 0.020) and TF-IDF baseline (Accuracy: 0.650, Macro F1: 0.580).
- **Metric:** Macro F1 was chosen as the primary optimization metric rather than accuracy. In customer support, rare high-risk intents (e.g., account cancellation, billing disputes) have severe operational costs if misclassified. Macro F1 weights all classes equally regardless of volume.

### 4.2 Historical Support Retrieval
- **Architecture:** Dense semantic vector retrieval using FAISS IndexFlatIP over historical support dialogue turns.
- **Top-$K$ Setup:** Top 5 passages retrieved per turn with a minimum cosine relevance threshold of 0.30.
- **Leakage Defense:** Historical test conversations are quarantined; the knowledge base index is constructed solely from the training partition.

### 4.3 Grounded Reply Generation
- **Architecture:** Prompt-engineered instruction generation with hard evidence constraints.
- **Negative Constraint Prompting:** Generative prompts strictly forbid inventing policy parameters, shipping timelines, or refund amounts not explicitly present in the provided retrieved passages.
- **Security:** Incoming customer messages are sanitized to strip prompt injection attempts and system prompt override delimiters.

### 4.4 Grounding Verification
- **Architecture:** Two-stage verification combining deterministic entity/numeric extraction with token span overlap checking.
- **Behavior:** Verifies whether numeric values (order numbers, currency, dates) and policy assertions in the candidate reply exist verbatim in the retrieved context.
- **Fail-Closed Gate:** If verification score falls below 0.70 or an unsupported claim is identified, the system repairs the draft by excising speculative statements or triggers mandatory escalation.

### 4.5 Risk-Aware Escalation Policy
- **Policy Engine (V1.1):** Evaluates multi-dimensional risk signals: intent classification confidence, retrieval cosine score, grounding verification status, detected high-risk intent keywords, and customer sentiment.
- **Asymmetric Cost Matrix:** The policy optimizes an asymmetric operational loss function:
  $$\text{Cost} = 10.0 \times \text{False Auto-Handle} + 1.0 \times \text{False Escalation}$$
  Auto-handling an inquiry that required human expertise carries an order-of-magnitude higher penalty than sending a routine inquiry to human review.

---

## 5. Results

Every component was benchmarked against trivial and competitive baselines on the identical frozen test partition ($N = 200$).

| Pipeline Component | Strongest Baseline | Final System | Primary Metric | Baseline Value | Final Value | Absolute Delta | Relative Delta |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Intent Routing** | TF-IDF Classifier | Semantic Bi-Encoder | Macro F1 | 0.580 | **0.857** | +0.277 | +47.8% |
| **Intent Accuracy** | Majority Class | Semantic Bi-Encoder | Accuracy | 0.105 | **0.855** | +0.750 | +714.3% |
| **Knowledge Retrieval**| Lexical BM25 Search | Dense FAISS Index | Recall@5 | 0.300 | **0.750** | +0.450 | +150.0% |
| **Reply Generation** | Historical Human Reply| Grounded Generator | Rubric Score | 0.500 | **0.767** | +0.267 | +53.4% |
| **Reply Generation** | Generic Template | Grounded Generator | Rubric Score | 0.265 | **0.767** | +0.502 | +189.4% |
| **Grounding Control** | Ungrounded Base LLM | Verified Pipeline | Pass Rate | 0.350 | **0.560** | +0.210 | +60.0% |
| **Escalation Policy** | Always-Auto Baseline| Risk-Aware V1.1 | Expected Cost | 6.100 | **2.140** | -3.960 | -64.9% |
| **Escalation Accuracy**| Always-Escalate | Risk-Aware V1.1 | Policy Accuracy| 0.610 | **0.690** | +0.080 | +13.1% |
| **Autonomous Routing** | Always-Auto Baseline| Final Agent Policy | Safe Auto Rate | 0.390 | **0.680** | +0.290 | +74.4% |

### Analytical Interpretations:
1. **Intent Classification:** Moving from surface TF-IDF n-grams to dense semantic embeddings boosted Macro F1 by +0.277 (+47.8%), specifically resolving colloquial phrasing on rare intents.
2. **Retrieval:** Semantic FAISS retrieval outperformed keyword BM25 by +0.450 (+150.0% Recall@5), though 14.5% of queries still suffered from zero-evidence retrieval due to vocabulary mismatch.
3. **Reply Quality:** The grounded generative pipeline exceeded historical human support quality by +0.267 (+53.4%) because human Twitter replies were often terse or fragmented across multiple tweets.
4. **Escalation Cost:** Risk-aware thresholding reduced expected operational penalty from 6.10 to 2.14 (-64.9%), protecting human agent capacity while filtering risky automated outputs.

---

## 6. Headline Metric: "What Is Misleading About My Headline Number?"

### Headline Number
- **Metric Name:** Mean Verified Grounded Reply Quality Score
- **Headline Value:** **0.767 / 1.000** (Raw: 3.835 / 5.000 across 6 rubric dimensions)
- **Evaluation Partition:** Phase 18 Frozen Multi-Turn Test Set ($N = 200$ customer sessions)
- **Statistical Uncertainty:** 95% Bootstrap Confidence Interval $[0.7612, 0.7728]$ ($SE = 0.0030$)

### Why This Metric Was Chosen
Rather than selecting throughput metrics that are trivial to inflate (such as Auto-Handle Rate, which can be forced to 95% by lowering thresholds), reply quality directly evaluates the end-to-end output that a customer would actually receive: relevance, grounded correctness, helpfulness, and tone.

### What It Actually Measures
It measures the degree to which generated support drafts conform to an explicit, six-dimensional quality rubric when judged against retrieved knowledge passages and conversation context.

### What It Does NOT Measure
- **It does NOT measure real customer resolution:** It cannot verify if the customer's problem was resolved in the real world.
- **It does NOT measure backend transaction success:** The system generates advice; it does not issue refunds or update database records.
- **It does NOT measure autonomous handling percentage:** Autonomous routing volume is 70.0%, an entirely distinct operational decision.
- **It does NOT guarantee zero hallucinations:** Despite a 0.767 score, 11.5% of candidate replies contained unsupported claims caught during verification.

### What Could Mislead the Reader
An uncritical reader might interpret "0.767 quality score" as meaning "the agent resolves 77% of support tickets autonomously with high satisfaction." In reality, the agent auto-handles 70.0% of requests, escalates 30.0% to humans, and on 2.0% of requests, auto-handles a critical high-risk issue unsafely.

### Most Important Caveat
> *Rubric compliance on synthetic text is a necessary but insufficient condition for customer support automation. High text fluency can mask silent factual omissions or dangerous policy violations.*

---

## 7. Top 5 Failure Modes

Analysis of the 200 test sessions revealed 160 operational failure signals across the pipeline stages. The top 5 failure modes were ranked using a severity-weighted risk index:

```
Failure Severity Distribution:
CRITICAL (2.5%) ── 4 cases (Escalation safety)
HIGH (55.6%)     ── 89 cases (Grounding & hallucination)
MEDIUM (38.8%)   ── 62 cases (Retrieval & intent uncertainty)
LOW (3.1%)       ── 5 cases (Minor style / verbosity)
```

### Failure #1 — Unsafe Auto-Handle of High-Risk Inquiries
- **Prevalence:** 4 cases (2.0% of total sessions; 13.0% of high-risk inquiries) | **Severity:** `CRITICAL`
- **Observed Behavior:**
  > Customer: *"I want to cancel my account and get a refund"* (Query ID: `q_final_005`)  
  > System Output: Routed to `AUTO_HANDLE` (Predicted intent: `account`, Confidence: 0.70)
- **Why It Failed:** The high-risk escalation heuristic checked for isolated keywords but failed on compound actions where account termination co-occurred with monetary refund requests under calm user sentiment.
- **Hypothesis:** Single-label intent classification collapses multi-intent customer messages, allowing the primary label to bypass compound risk checks.
- **Next Improvement:** Deploy a hard pre-classifier regex filter that mandates immediate human escalation for any compound financial or credential termination intent.

### Failure #2 — Grounding Verification Failures & Unsupported Claims
- **Prevalence:** 88 cases (44.0% initial fail rate; 11.5% unsupported claims) | **Severity:** `HIGH`
- **Observed Behavior:**
  > Customer: *"Shipping cost seems wrong."* (Query ID: `eval_0007`)  
  > System Output: *"Your order qualifies for free standard 3-day delivery once updated..."* (Retrieved evidence contained no delivery timeline).
- **Why It Failed:** When retrieved passages lack specific numerical parameters, the generative model invents plausible standard timelines to make the reply sound complete.
- **Hypothesis:** Generative language models prioritize conversational completeness over strict epistemic abstinence unless penalized by hard token-level constraints.
- **Next Improvement:** Implement token span-level extraction where any ungrounded timeline or numeric claim is automatically replaced with a safe fallback template macro.

### Failure #3 — Retrieval Misses & Zero Evidence Retrieved
- **Prevalence:** 29 cases (14.5% zero-evidence rate) | **Severity:** `MEDIUM`
- **Observed Behavior:**
  > Customer: *"I need help with quantum computing returns"* (Query ID: `FAIL_PH18_002`)  
  > System Output: 0 chunks retrieved above the 0.30 cosine similarity threshold.
- **Why It Failed:** Dense bi-encoders trained on general corpora experience embedding drift on atypical, highly technical, or colloquial Twitter queries with vocabulary mismatch.
- **Hypothesis:** Dense semantic retrieval alone lacks lexical precision on out-of-vocabulary domain tokens.
- **Next Improvement:** Implement hybrid dense + BM25 lexical retrieval combined via Reciprocal Rank Fusion (RRF).

### Failure #4 — Intent Classification Uncertainty on Short Inputs
- **Prevalence:** 28 cases (14.0% low-confidence rate) | **Severity:** `MEDIUM`
- **Observed Behavior:**
  > Customer: *"Can you check my order status?"* (Query ID: `eval_0003`)  
  > System Output: Predicted intent `order_status` with confidence 0.358 (triggered escalation).
- **Why It Failed:** Extremely short user queries (under 6 words) provide insufficient contextual features for the classifier to produce high probability margins over overlapping classes.
- **Hypothesis:** Isolated single-turn representations discard previous turn trajectories that disambiguate customer intent.
- **Next Improvement:** Concatenate the preceding 2 conversational turns into the classifier feature vector and add a clarification prompt for borderline confidence queries.

### Failure #5 — Borderline Escalation Threshold & Reason Misclassification
- **Prevalence:** 8 cases (4.0% misclassification rate) | **Severity:** `MEDIUM`
- **Observed Behavior:**
  > Customer: *"Sample message about order_status"* (Query ID: `q_0002`)  
  > System Output: Escalated to human due to `LOW_INTENT_CONFIDENCE` (Confidence: 0.665 vs. 0.700 threshold), despite obvious routine inquiry.
- **Why It Failed:** A rigid global scalar threshold (0.70) was applied uniformly across all intents, forcing benign, easily resolvable queries into human queues.
- **Hypothesis:** Optimal escalation thresholds vary by intent risk: routine queries can safely operate at lower thresholds (0.55), while high-risk intents require conservative thresholds (0.80).
- **Next Improvement:** Calibrate per-intent escalation thresholds on validation data to minimize unnecessary human escalation.

---

## 8. Human vs. LLM-as-Judge Evaluation

To explore automated evaluation scalability, an LLM-as-judge system was developed using an identical blinded six-dimension rubric (Relevance, Groundedness, Correctness, Helpfulness, Completeness, Style on a 1–5 scale). System identities were anonymized (A/B/C/D) to eliminate model name bias.

### Reliability and Agreement Analysis ($N = 10$ Common Benchmark Interactions)
- **Mean Score:** Human Annotator = 3.00 / 5.00 vs. LLM Judge = 2.55 / 5.00
- **Mean Absolute Difference (MAD):** 0.952 points
- **Exact Score Agreement:** 20.0%
- **Within-1 Point Agreement:** 50.0%
- **Within-2 Point Agreement:** 100.0%
- **Rank Correlation (Spearman $\rho$):** 0.091

### Key Finding & Limitation
The LLM judge exhibited systematic conservative bias (-0.45 point mean offset) and penalized natural conversational brevity. While within-2 point agreement was 100%, the near-zero rank correlation ($\rho = 0.091$) indicates that **the LLM judge cannot serve as an authoritative substitute for human ground truth**. It is suitable only as a coarse, supplementary batch-screening filter.

---

## 9. Escalation Safety & Operational Tradeoffs

Customer support automation involves an inescapable tradeoff between coverage and risk:

```
[ Aggressive Auto-Handling ] ── High Coverage (85%) ── High Risk (Unsafe Auto-Handle: 8.0%)
[ Risk-Aware Policy V1.1  ] ── Balanced (70%)     ── Low Risk (Unsafe Auto-Handle: 2.0%)
[ Conservative Escalation  ] ── Low Coverage (39%)  ── Zero Risk (Unsafe Auto-Handle: 0.0%)
```

### Escalation Label Limitations
Gold escalation labels in this benchmark were derived using a multi-signal risk heuristic combining intent severity, sentiment toxicity, and entity risk keywords. They do **not** reflect real-time enterprise routing logs or historical human agent dispatch records. Consequently, "safe auto-handle" (68.0%) indicates policy compliance under our defined cost matrix, not absolute operational infallibility.

---

## 10. Prioritized Next-Week Improvement Plan

Derived directly from the Phase 21 root-cause failure analysis, the following experiments represent the highest-ROI engineering priorities:

| Priority | Improvement Experiment | Targeted Root Cause | Expected Impact | Engineering Effort |
| :---: | :--- | :--- | :--- | :---: |
| **P0** | **Pre-Classifier Hard Escalation Gate** | 4 critical unsafe auto-handles on compound cancellation/refund requests | Eliminate 100% of high-risk unsafe auto-handles (2.0% $\rightarrow$ 0.0%) | 1 day |
| **P1** | **Token Span Claim Extractor + Macro Fallback** | 88 grounding failures (11.5% unsupported claim rate) | Reduce unsupported claims to < 3.0%; raise grounding pass to > 85% | 2 days |
| **P2** | **Hybrid Dense + BM25 Lexical Retrieval (RRF)** | 29 zero-retrieval cases due to semantic vocabulary mismatch | Increase Recall@5 from 0.75 to > 0.85; drop zero-retrieval to < 5% | 2 days |
| **P3** | **Context-Aware Multi-Turn Intent Classifier** | 28 low-confidence classification cases on short queries (<6 words) | Reduce low-confidence queries by 40%; increase Macro F1 to > 0.88 | 2 days |
| **P4** | **Per-Intent Calibrated Escalation Thresholds**| 8 borderline false escalations from global scalar threshold | Increase policy accuracy from 69% to > 76%; reduce human queue volume | 1 day |

---

## 11. Conclusion

This project demonstrates that building a trustworthy AI customer support agent requires treating evaluation and escalation safety as primary system constraints rather than post-hoc checks. By combining dense semantic intent classification, grounded retrieval-augmented generation, deterministic grounding verification, and an asymmetric risk-aware escalation policy, the system achieved a Verified Grounded Reply Quality Score of **0.767 / 1.000** (+53.4% over historical human baseline) with a 70.0% autonomous handling rate.

However, intellectual honesty requires acknowledging the system's hard boundaries: offline rubric compliance does not prove real-world customer satisfaction, synthetic single-brand distributions do not guarantee multi-vertical generalization, and 2.0% of high-risk inquiries evaded heuristic escalation. Real-world deployment demands hard pre-routing safety gates, hybrid retrieval, and continuous human-in-the-loop oversight.
