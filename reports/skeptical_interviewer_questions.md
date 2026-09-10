# Skeptical Interviewer Questions & Evidence-Based Defenses

This report provides detailed, evidence-based answers to 12 adversarial questions that a senior machine learning interviewer or technical leader would ask about the evaluation results.

---

### Q1: "Why is this your headline metric?"
**Answer:** Because the ultimate business deliverable of an automated support agent is the quality and correctness of the reply given to the user. Upstream metrics like classification accuracy do not verify that a user received a helpful response, and operational metrics like auto-handle rate can be trivially inflated. Verified Grounded Reply Quality (0.767) captures the complete generation and verification pipeline across six essential rubric dimensions.

---

### Q2: "Why not use accuracy?"
**Answer:** Accuracy is an intermediate technical metric, not an end-to-end outcome metric. In customer support, an agent can achieve 85.5% classification accuracy on intent recognition while still hallucinating policy details in the reply or failing to escalate a critical account dispute. Furthermore, raw classification accuracy is vulnerable to class imbalance—a model can score 80% accuracy simply by mastering the top 3 common intents while failing every rare edge case.

---

### Q3: "Why not use the LLM judge score alone?"
**Answer:** Because our Phase 20 agreement audit demonstrated that the LLM judge possesses systematic length and strictness biases. In large disagreement cases, the LLM judge severely penalized concise answers (scoring 1.33/5.0) that human annotators rated as acceptable (3.0/3.0). Using an LLM judge as an unchecked single source of truth replaces human customer standards with model-specific stylistic preferences.

---

### Q4: "Why not use auto-handle rate?"
**Answer:** Reporting auto-handle rate as a headline success metric is dangerous and intellectually dishonest. A system can achieve a 95% auto-handle rate simply by lowering escalation thresholds, while silently providing wrong answers to thousands of customers. Automation volume is only meaningful if conditioned on safety; our failure analysis showed that even at a 70% auto-handle rate, 2% of cases involved critical high-risk actions that should never have been automated.

---

### Q5: "How representative is your evaluation set?"
**Answer:** It is representative of the defined synthetic benchmark distribution across 10 balanced intent classes and three difficulty levels. However, it is **not** fully representative of live customer support. Because the raw Twitter dataset was not downloaded locally, the evaluation cohort does not reflect the full spectrum of live spelling noise, emojis, multi-turn customer anger, or concurrent system outages.

---

### Q6: "Could your metric be inflated?"
**Answer:** Yes, in three specific ways:
1. The evaluation uses synthetic customer queries, which are cleaner and more grammatically coherent than live social media posts.
2. The benchmark evaluates isolated single turns or two-turn exchanges, avoiding multi-turn cumulative degradation.
3. The baseline against which we claim a +0.502 gain is a generic template, which is an easily beaten strawman (though our primary comparison is the tougher 0.500 historical reply baseline).

---

### Q7: "How do you know there isn't data leakage?"
**Answer:** In Phase 18 and Phase 6, we executed automated leakage audits (`scripts/final_leakage_check.py`) that verified zero token overlap and zero conversation ID overlap between the training corpus, the knowledge base retrieval index, and the evaluation test split. Knowledge base retrieval embeddings were constructed strictly from pre-split historical data.

---

### Q8: "Does your dataset reflect current customer support?"
**Answer:** No. The underlying customer support data source originates from historical Twitter support logs (2017). Support policies, return windows, delivery partners, and software features change constantly. Relying on historical conversations as evidence carries an inherent risk of historical response drift—recommending deprecated workflows that were valid in 2017 but obsolete today.

---

### Q9: "Can this result generalize to other brands?"
**Answer:** No. All experiments were constrained to a single selected retail brand. A model tuned on retail return policies will struggle if deployed on a B2B SaaS platform or fintech company with complex authentication protocols, stricter compliance mandates, and specialized technical vocabularies.

---

### Q10: "Does this prove customer satisfaction?"
**Answer:** Absolutely not. Offline reply quality evaluates whether a message reads well and cites retrieved text. A real customer who is waiting for a delayed urgent medication or experiencing unauthorized credit card charges does not care how beautifully written an AI response is if their physical issue is unresolved. Satisfaction requires backend operational resolution.

---

### Q11: "Does this prove production readiness?"
**Answer:** No. Phase 21 revealed that 2.0% of evaluated cases represented unsafe auto-handling of high-risk requests (e.g., account cancellation with refund demands). In an enterprise handling 100,000 tickets a month, a 2% unsafe auto-handle rate equals 2,000 severe customer incidents and potential financial losses. The system cannot be considered production-ready without a deterministic safety gate.

---

### Q12: "What would make your headline number fall?"
**Answer:** The 0.767 score would drop substantially under any of the following real-world conditions:
1. **Domain & Terminology Shift:** Testing on unindexed product catalog updates or holiday promotional codes would reduce retrieval recall, dropping reply quality by ~0.15–0.25.
2. **Adversarial / Complex Multi-Turn Inputs:** Our sensitivity analysis proved that over-weighting hard multi-turn cases reduces the mean score by 0.035 to 0.060.
3. **Strict Human Customer Panels:** Real customers evaluating whether their issue was resolved typically score conversational AI 20–30% lower than offline rubric annotators.
