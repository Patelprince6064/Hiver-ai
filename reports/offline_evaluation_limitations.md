# Offline Evaluation Limitations

This report explicitly documents what offline benchmark evaluations **cannot** measure, establishing the boundaries between experimental metrics and production reality.

---

## 1. What Offline Evaluation Genuinely Measures

- **Proxy Alignment:** How closely generated replies match defined rubric criteria (relevance, groundedness, completeness, style) according to a simulated annotator and automated judge.
- **Classification Separation:** Mathematical discrimination of input text embeddings across predefined intent categories on frozen test samples.
- **Syntactic & Rule Compliance:** Whether outputs satisfy deterministic checks (no ungrounded entities, no blacklisted claims, escalation flags raised on confidence dips).

---

## 2. What Offline Evaluation CANNOT Measure

### A. Real Customer Satisfaction (CSAT)
An offline evaluator may award 5/5 stars to a response because it is polite, grammatically flawless, and cites policy correctly. However, a real customer facing a delayed medical delivery or lost wallet may find that same response infuriating and dismissive. Offline scores measure stylistic compliance, not emotional or practical satisfaction.

### B. Actual Problem Resolution Rate (FCR)
A support interaction is truly successful only if the customer's real-world problem is resolved (e.g. package found, refund processed, account unlocked). Offline evaluation only reviews the text of the message; it does not connect to backend APIs, execute database transactions, or verify whether the customer needed to reach out again 20 minutes later.

### C. True Escalation Burden & Human Agent Fatigue
Our simulated escalation cost model assumes a static 1.0 vs 10.0 penalty ratio. In production:
- Unnecessary escalations overwhelm human agent queues, causing SLA breaches and burnout.
- Escalated tickets that lack proper AI diagnostic summaries increase human handle time (AHT), negating expected cost savings.

### D. Actual Business ROI & Cost Savings
Claiming monetary savings from an offline 70% auto-handle rate assumes every auto-handled message completely eliminates a paid agent interaction. In reality, customers who receive unhelpful automated responses often re-open tickets or switch channels (calling phone support), which significantly multiplies operational costs.

### E. Production Latency & Concurrency Stress
Offline batched evaluation processes items asynchronously without live websocket timeouts, token generation streaming, or multi-tenant database contention. Simulated latencies (50ms intent, 500ms generation) do not reflect network jitter or API rate-limiting under peak load.

### F. Real-World Distribution Shift
Production customer support is subject to sudden exogenous shifts:
- Website outages or payment gateway crashes that generate unseen error codes.
- Viral social media backlash that overwhelms sentiment classifiers.
- New seasonal promotional codes not indexed in historical knowledge bases.

### G. Historical Response Drift
The knowledge base relies on historical support conversations. Historical replies reflect past company policies, former shipping partners, and deprecated refund rules. Using past replies as evidence risks reviving outdated policies that contradict current terms of service.
