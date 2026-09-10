# Problem Framing

## Selected Brand

*To be filled after brand selection.*

---

## User Problem

Customers reach out to brands on Twitter with support requests, complaints, questions, and issues. These messages are public, short, often noisy (containing @mentions, hashtags, URLs, emojis), and may span multiple turns.

The goal is to build an AI support agent that can:

1. Understand what the customer is asking for (intent classification)
2. Draft a reply grounded in how the brand historically resolved similar issues
3. Decide whether to auto-handle the message or escalate to a human

---

## Agent Input

An incoming customer-support message, potentially with conversation context:

```
Customer: "@BrandName I've been waiting 3 weeks for my order #12345. Still no delivery!"
```

---

## Agent Output

The agent should produce:

| Output | Description |
|--------|-------------|
| **Intent** | Classification of the customer's request (e.g., "order_status", "refund_request", "technical_issue") |
| **Draft Reply** | A response grounded in historical support behavior |
| **Auto-Handle vs Escalate** | Decision on whether the agent can handle this automatically |
| **Escalation Reason** | If escalating, why (e.g., "insufficient evidence", "high-risk request", "ambiguous intent") |
| **Supporting Evidence** | Historical conversations used to ground the reply |

---

## What "Good" Means

### Intent Classification

The predicted intent should accurately represent the customer's request.

- **Good:** Customer asks about order status → predicted intent is "order_status"
- **Bad:** Customer asks about order status → predicted intent is "refund_request"

The intent taxonomy will be derived from the selected brand's actual data (Phase 5).

### Reply Quality

The reply should:

- **Address the customer's actual problem** — not a generic or irrelevant response
- **Remain grounded in historical support behavior** — based on how the brand actually responded to similar issues
- **Avoid unsupported claims** — don't promise things the brand hasn't historically done
- **Avoid hallucinated policies** — don't invent refund policies, delivery timelines, etc.
- **Be concise and useful** — appropriate length for Twitter support
- **Maintain appropriate support tone** — professional, helpful, brand-consistent

### Escalation Decision

The agent should escalate (not auto-handle) when:

- **Evidence is insufficient** — no historical support data for this type of issue
- **The issue is ambiguous** — unclear intent or multiple possible interpretations
- **The request appears high-risk** — legal issues, safety concerns, large refunds
- **Historical evidence does not support a safe answer** — cannot confidently draft a reply

The exact escalation policy will be developed in Phase 6.

---

## What We Will NOT Build

The following are **intentionally excluded** from this project:

| Exclusion | Rationale |
|-----------|-----------|
| Twitter API integration | The assignment uses a static dataset, not live Twitter |
| Autonomous account actions | AI should not modify customer accounts without human oversight |
| Refund execution | Payment actions require human authorization |
| Payment changes | Financial operations are out of scope |
| Customer-account modifications | Account changes require human oversight |
| Real CRM integration | No production CRM is available for this assignment |
| Production ticket creation | No ticketing system is available |
| Full multi-brand support | The assignment explicitly requires one brand |
| Complete 3M-row processing | The assignment allows subsampling for practical development |
| Authentication infrastructure | No user authentication is needed for this assignment |

These exclusions keep the scope aligned with the assignment's focus: demonstrating a trustworthy support-agent pipeline.

---

## Assumptions

Based on the available dataset:

1. **Historical conversations are representative** — past support interactions reflect the types of issues customers bring
2. **Brand responses are ground truth** — the brand's historical replies are appropriate responses (even if templated)
3. **Conversation threads are coherent** — messages within a conversation are related
4. **Intent can be inferred** — customer messages contain enough signal to classify intent
5. **Resolution can be approximated** — while no explicit labels exist, heuristic signals (thank-you, conversation termination) provide rough resolution indicators

---

## Risks

Based on the selected-brand data:

1. **Templated responses** — if the brand uses many template replies, the agent may learn to generate repetitive responses
2. **Noisy social-media text** — URLs, mentions, hashtags, and emojis require preprocessing
3. **Short conversations** — some conversations may be too short to provide meaningful context
4. **Imbalanced intents** — some intent categories may be much larger than others
5. **No ground-truth resolution labels** — we cannot directly measure resolution rate
6. **Historical data only** — the agent learns from past data, which may not reflect current policies

---

## Evaluation Philosophy

Success will be established through:

1. **Golden evaluation set** — 150–250 hand-labelled examples for reliable evaluation
2. **Baseline comparison** — comparing against trivial and simple baselines to ensure the AI system adds value
3. **Automated metrics** — intent accuracy, retrieval recall, escalation precision/recall
4. **Reply quality evaluation** — LLM-as-judge for groundedness, relevance, helpfulness
5. **Human-LLM agreement** — measuring how well the LLM judge agrees with human ratings
6. **Failure analysis** — identifying the top five failure modes with real examples
7. **Honest reporting** — documenting what is misleading about headline metrics

No actual results are claimed here. These evaluation methods will be implemented in Phase 7.
