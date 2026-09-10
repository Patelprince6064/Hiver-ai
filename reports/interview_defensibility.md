# Interview Defensibility — Hiver AI Customer Support Agent

Concise, technical, evidence-based answers to 20 critical engineering interviewer challenges.

---

### Q1: Why did you choose this brand?
**Answer:** Brand selection was grounded in data suitability rather than post-hoc model accuracy. We evaluated conversation volume, multi-turn dialogue density, support response coverage, and issue diversity. A single specialized brand (`brand_001`, e-commerce profile) was chosen because customer support policies and tone vary dramatically across industries. Specializing on one brand allows deep knowledge base grounding, a domain-coherent intent taxonomy, and realistic escalation policies without cross-vertical dilution.

### Q2: Why this intent taxonomy?
**Answer:** We established a 7-class taxonomy derived directly from high-frequency and high-risk customer support actions in the dataset: `order_status`, `shipping`, `returns`, `refunds`, `account_help`, `product_question`, and `general_inquiry`. This balances operational utility with granularity: high-risk transactional categories (`refunds`, `account_help`) are cleanly partitioned from benign informational inquiries (`general_inquiry`), enabling distinct escalation rules.

### Q3: Why Macro F1?
**Answer:** Support intent distributions exhibit natural class imbalance. Accuracy can easily mask systemic failure on rare intents: a naive classifier predicting only the top 2 intents could achieve 70% accuracy while failing 100% of high-risk account or refund requests. Macro F1 computes the unweighted arithmetic mean of F1 scores across all 7 classes, penalizing models that sacrifice rare or safety-critical classes to maximize bulk accuracy.

### Q4: Why semantic embeddings?
**Answer:** Customer inquiries on social channels are brief, informal, and laden with typos and colloquialisms (e.g., "where is my stuff" vs. "track order status"). Surface n-grams and TF-IDF fail because of lexical divergence (0.580 Macro F1). Dense bi-encoder embeddings (`all-MiniLM-L6-v2`) project semantic concepts into a shared vector space, achieving 0.857 Macro F1 by capturing synonymous intent across varied phrasings.

### Q5: Why FAISS?
**Answer:** FAISS provides high-performance, deterministic vector indexing with zero runtime cloud overhead. For our historical support knowledge base, `IndexFlatIP` on normalized embeddings performs exact cosine similarity search in sub-millisecond time (<1ms per query), guaranteeing reproducible retrieval recall without approximate nearest neighbor (ANN) quantization artifacts.

### Q6: Why not fine-tune an LLM?
**Answer:** Fine-tuning an LLM embeds support policies and facts directly into parameter weights, which creates three fatal issues: (1) policies cannot be updated dynamically without retraining, (2) the model tends to hallucinate plausible facts when out-of-domain, and (3) training costs and compute overhead are high. Retrieval-Augmented Generation (RAG) decouples knowledge from reasoning: policies can be updated instantly in the vector index, and generations are strictly constrained to retrieved context.

### Q7: How did you prevent leakage?
**Answer:** Splitting was enforced strictly at the **conversation ID level** using deterministic hashing, never at the message level. Because multi-turn support threads share customer entities, timestamps, and order references, message-level splits cause severe train-test leakage. Furthermore, test conversations were completely quarantined from the knowledge base retrieval index.

### Q8: How did you create the golden set?
**Answer:** We designed an independent, hand-labeled golden set architecture stratified by intent class, query complexity, and ambiguity. Crucially, to maintain intellectual honesty, the golden set directory was locked and kept completely unpolluted during development so it could serve as a clean future evaluation benchmark without risk of overfitting.

### Q9: How did you evaluate reply quality?
**Answer:** We implemented a structured, multi-dimensional evaluation rubric spanning 6 dimensions on a 1–5 scale: Relevance, Groundedness, Correctness, Helpfulness, Completeness, and Tone/Style. Candidate outputs were evaluated blindly against retrieved evidence and customer history across multiple system configurations (Generic Template, Historical Human, Ungrounded LLM, and Grounded Verified LLM).

### Q10: How do you know replies are grounded?
**Answer:** We deploy a deterministic two-stage grounding verifier. The verifier extracts factual assertions, entity values, and numeric parameters (prices, delivery days, order numbers) from the draft reply and verifies their presence in retrieved passages using token span overlap. If an unverified factual claim is detected, the status is set to `FAIL`, triggering automated claim repair or mandatory escalation.

### Q11: Why can the LLM judge be trusted?
**Answer:** The LLM judge cannot be trusted blindly as an authoritative oracle; our Phase 20 audit proved this. However, it is useful as a consistent, reproducible, high-throughput screening tool when blinded to system identity (A/B/C/D) and guided by an explicit rubric with concrete anchor examples.

### Q12: Can LLM-as-judge replace humans?
**Answer:** No. Our human-vs-LLM agreement analysis ($N = 10$) revealed a mean absolute difference of 0.952 points, a systematic conservative bias (-0.45 point offset), and a near-zero rank correlation ($\rho = 0.091$). While it achieved 100% agreement within 2 points, it frequently disagreed with human nuance on brevity and tone. It serves as a supplementary screening filter, not a replacement for human annotators.

### Q13: How do you decide escalation?
**Answer:** Escalation is governed by a multi-signal risk policy (V1.1). The agent escalates to human specialists if: (1) intent classification confidence < 0.70, (2) retrieval cosine similarity < 0.30, (3) grounding verification fails, (4) high-risk intent keywords are detected (cancellation, refunds, legal threats), or (5) customer sentiment exhibits high frustration. This policy optimizes an asymmetric loss matrix ($10\times$ penalty for false auto-handle vs $1\times$ for false escalation).

### Q14: What happens when evidence is insufficient?
**Answer:** When retrieved passages fail the sufficiency threshold (cosine similarity < 0.30 or zero chunks retrieved), the agent does not attempt speculative generation. The generation prompt is either blocked, or the system triggers a fail-closed escalation route (`INSUFFICIENT_EVIDENCE`), transferring the customer thread to a human specialist with pre-extracted intent metadata.

### Q15: What is the biggest failure mode?
**Answer:** The most dangerous failure mode is **Unsafe Auto-Handle of High-Risk Compound Inquiries** (2.0% rate, 4 observed cases). In these cases, a customer combined an account cancellation request with a monetary refund request in calm language (e.g., Query `q_final_005`). Because the classifier categorized the intent under `account` and sentiment was neutral, heuristic rules bypassed escalation and auto-handled the ticket.

### Q16: What is misleading about the headline metric?
**Answer:** Our headline score of **0.767 / 1.000** measures offline rubric compliance on synthetic text. It is misleading if interpreted as "76.7% customer satisfaction" or "77% autonomous ticket resolution." It measures response quality on eligible turns, while autonomous routing volume is 70.0%, and it does not verify whether the customer's issue was actually resolved in the real world.

### Q17: What would you improve next week?
**Answer:** My top P0 improvement is deploying a deterministic, pre-classifier regex hard gate for compound sensitive actions (account deletion + refund disputes) to reduce the unsafe auto-handle rate from 2.0% to 0.0%. Secondary priorities are implementing hybrid BM25 + dense retrieval (RRF) to eliminate 29 zero-retrieval cases, and token-level claim span masking for grounding repair.

### Q18: What would break this system in production?
**Answer:** Three major factors: (1) **Distribution shift:** New promotional campaigns, unexpected outages, or policy changes not present in the historical retrieval index. (2) **Adversarial inputs:** Prompt injections attempting to override system constraints to issue unauthorized discounts. (3) **Multi-turn topic drift:** Customers changing the topic mid-conversation, causing single-turn intent routing to misdirect the ticket.

### Q19: What would you monitor in production?
**Answer:**
1. *Escalation Rate Drift:* Sudden spikes or dips in the 30% human escalation rate.
2. *Zero-Retrieval Frequency:* Tracking queries where max retrieval score < 0.30 (identifying knowledge base gaps).
3. *Grounding Failure Rate:* Spikes in verification rejections indicating model hallucination or novel inquiry types.
4. *Human Agent Overturn Rate:* Frequency with which human specialists reject or rewrite agent-drafted replies.
5. *High-Risk Action Flagging:* 100% auditing of auto-handled conversations containing financial or credential keywords.

### Q20: What did you intentionally NOT build?
**Answer:** We explicitly excluded autonomous financial executions (refund processing, card updates), production CRM/Twitter API integrations, and multi-brand routing platforms. These boundaries were chosen to focus 100% of engineering bandwidth on evaluation integrity, grounding verification, and safety-critical escalation policy design.
