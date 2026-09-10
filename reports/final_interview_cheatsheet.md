# Hiver SDE Intern Take-Home — Final Interview Cheatsheet

Personal interview preparation notes summarizing the 18 core technical topics with rigorous, evidence-based responses.

---

### 1. One-Minute Project Explanation
"I built an evaluation-first, grounded AI customer support agent for Twitter e-commerce support. The core engineering philosophy was that an agent is only as good as its safety boundaries. The system classifies customer intent, retrieves historical brand support resolutions via FAISS vector search, generates evidence-constrained replies, deterministically verifies factual claims, and evaluates an asymmetric risk-aware escalation policy. On our frozen test partition of 200 sessions, it achieved a Verified Grounded Reply Quality Score of 0.767 / 1.000—a 53% improvement over historical human responses—while safely auto-handling 70% of routine inquiries and routing 30% to human review."

### 2. Architecture Explanation
"The pipeline is a sequential, fail-closed multi-stage architecture:
`Customer Input -> Preprocessing & Token Hygiene -> Dense Bi-Encoder Intent Classifier -> FAISS Knowledge Base Retrieval -> Relevance Gating (cosine >= 0.30) -> Evidence-Constrained Grounded Generation -> Deterministic NER/Numeric Span Verification -> Risk-Aware Escalation Policy -> Output (AUTO_HANDLE or ESCALATE_TO_HUMAN)`.
Every stage can emit risk signals that trigger immediate human escalation if uncertainty thresholds are crossed."

### 3. Why This Approach?
"Rather than treating support automation as an open-ended conversational problem where an LLM is given broad prompts, I structured it as an information retrieval and risk optimization problem. By decoupling knowledge retrieval from generation and enforcing a deterministic verification barrier, we prevent the model from inventing non-existent brand return policies or delivery timelines."

### 4. Why This Brand?
"Support policies, tone, and return rules differ radically across industries. An airline's cancellation policy has nothing in common with an apparel retail brand. Selecting a single specialized brand (`brand_001`, e-commerce profile) based on conversation volume and response density allowed constructing a coherent, high-density retrieval index and a domain-specific intent taxonomy without cross-vertical dilution."

### 5. Why This Intent Model?
"Customer support tweets are noisy, informal, and filled with colloquialisms. Keyword matching and TF-IDF failed on synonymous expressions (achieving only 0.580 Macro F1). A dense bi-encoder (`all-MiniLM-L6-v2`) mapped semantic meanings into vector space, lifting Macro F1 to 0.857. We optimized for Macro F1 rather than raw accuracy to ensure rare, safety-critical intents like account cancellations and payment disputes were not sacrificed to boost majority-class accuracy."

### 6. Why Retrieval?
"Fine-tuning model weights on historical support logs creates frozen, hallucination-prone models that cannot be updated when company policies change. Dense FAISS retrieval allows dynamic, instant policy updates without retraining and grounds generated drafts in actual historical brand resolutions."

### 7. Why Grounding?
"LLMs are conversational optimizers; when given brief context, they invent plausible details (e.g., claiming 'delivery takes 3-5 days' when context doesn't state it). Deterministic token-span and numeric claim extraction catches these subtle hallucinations (catching an 11.5% unsupported claim rate), ensuring unverified statements never reach customers."

### 8. Why Escalation?
"Zero-risk autonomous support is an illusion. An AI support system must know its own epistemic boundaries. Escalation is governed by an asymmetric loss matrix ($10\times$ penalty for false auto-handle vs. $1\times$ for false escalation), prioritizing customer trust and brand safety over vanity automation coverage."

### 9. Evaluation Methodology
"Evaluation was built first. We enforced strict conversation-level hash splitting (70/15/15) to prevent multi-turn dialogue leakage. We evaluated against trivial baselines (majority class, lexical BM25, generic templates, historical human replies, always-auto/always-escalate policies). We utilized a 6-dimension rubric (Relevance, Groundedness, Correctness, Helpfulness, Completeness, Tone) and audited human-judge agreement."

### 10. Strongest Result
"Our primary headline metric: **Verified Grounded Reply Quality Score of 0.767 / 1.000** (95% Bootstrap CI: $[0.7612, 0.7728]$), delivering a **+53.4% relative gain** over historical human responses (0.500) and **+189.4%** over generic template fallbacks (0.265), alongside reducing operational escalation loss by 64.9% (2.14 vs. 6.10)."

### 11. Strongest Baseline
"The **Historical Human Response Baseline (0.500)**. Past agent replies on Twitter were often fragmented across multiple tweets or contained unhelpful 'Please DM us' canned responses. The grounded LLM synthesized complete, helpful, contextually grounded answers that consistently surpassed the historical baseline."

### 12. Biggest Failure
"Our audit revealed 4 critical cases (2.0% of test sessions) where **high-risk compound requests were auto-handled unsafely**. For example, a customer calmly asked: *'I want to cancel my account and get a refund'*. Because the classifier predicted `account` and sentiment was neutral, single-keyword heuristic checks failed to recognize the destructive compound action. This is our P0 fix: adding a hard pre-classifier regex gate for sensitive actions."

### 13. Most Misleading Metric
"The headline score of **0.767 / 1.000** could easily be misinterpreted as '76.7% autonomous ticket resolution' or '77% customer satisfaction'. In reality, autonomous handling volume is an entirely separate policy decision (70.0%), and rubric compliance on text does not prove real-world problem resolution or backend transaction success."

### 14. Biggest Technical Tradeoff
"The tradeoff between **Coverage and Safety**. By tuning our escalation policy with an asymmetric $10\times$ penalty on false auto-handling, we deliberately capped autonomous handling at 70.0% and accepted a 30.0% human escalation burden. We could have achieved 85% coverage, but our unsafe auto-handle rate would have jumped from 2% to 8%."

### 15. What Would You Build Next?
"Prioritized engineering sprints from Phase 21:
1. *P0:* Hard regex pre-routing gate for compound destructive actions (eliminating the 2.0% unsafe auto-handle rate).
2. *P1:* Two-stage token span claim extractor with template fallback (reducing unsupported claims from 11.5% to <3%).
3. *P2:* Hybrid BM25 + dense retrieval (RRF) to eliminate the 14.5% zero-evidence rate on out-of-vocabulary terms."

### 16. What Would Break in Production?
"1. *Temporal Policy Drift:* New return policies or seasonal promotions not present in the vector index.
2. *Adversarial Injections:* Malicious users attempting prompt injection to negotiate discounts.
3. *Multi-turn Topic Switching:* Customers switching topics mid-thread, causing single-turn intent classifiers to misroute."

### 17. How Would You Monitor It?
"I would track five real-time operational telemetry signals:
1. *Human Escalation Rate Drift:* Alerting on deviations outside the expected 25%–35% band.
2. *Zero-Retrieval Spike Rate:* Monitoring queries with max cosine score < 0.30 to identify knowledge gaps.
3. *Grounding Failure Spike Rate:* Tracking verification failure bursts.
4. *Human Agent Overturn Rate:* Measuring how often human specialists discard drafted replies.
5. *High-Risk Action Auditing:* 100% human sampling of any auto-handled conversation containing financial keywords."

### 18. Why Should Hiver Hire You?
"Because I don't just build optimistic ML demos that look good in a slide deck; I build systems that are evaluated honestly. I understand data leakage, asymmetric operational loss, epistemic boundaries, and metric integrity. When my system had a 2% critical failure rate, I didn't hide it behind an 85% accuracy headline—I isolated it, root-caused it to compound intent heuristics, and designed an engineering roadmap to eliminate it. That is the engineering discipline Hiver needs for customer-facing AI."
