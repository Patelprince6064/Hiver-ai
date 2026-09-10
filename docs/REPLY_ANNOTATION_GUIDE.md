# Reply Annotation Guide

Version: 1.0
Phase: 14

---

## Purpose

This guide instructs human evaluators on how to score customer-support replies using the six-dimension quality rubric.

---

## Before You Begin

1. Read the **Reply Quality Rubric** (`docs/REPLY_QUALITY_RUBRIC.md`) completely.
2. Practice on the example annotations below before scoring evaluation data.
3. Do NOT look at which system produced each reply. All replies are anonymized.

---

## Evaluation Process

For each evaluation query, you will see:

```
Customer Message: [the customer's message]

Reply A: [anonymized reply]
Reply B: [anonymized reply]
Reply C: [anonymized reply]
Reply D: [anonymized reply]
```

For each reply, score all six dimensions:

1. **Relevance** (1–5)
2. **Groundedness** (1–5)
3. **Correctness** (1–5)
4. **Helpfulness** (1–5)
5. **Completeness** (1–5)
6. **Style** (1–5)

Then provide:

7. **Overall** (1–5) — your overall quality assessment
8. **Failure Tags** — select all that apply (see list below)
9. **Free-text Reason** — brief explanation of your scoring

---

## Scoring Rules

### Rule 1: Score Independently

Score each reply independently. Do not compare replies to each other while scoring. A reply that looks poor next to a great reply might still be a 3 on its own merits.

### Rule 2: Use the Full Scale

Use the full 1–5 range. Do not cluster around 3. If a reply is genuinely excellent, give it a 5. If it is genuinely poor, give it a 1.

### Rule 3: Groundedness Is About Evidence

Groundedness asks: "Is this reply supported by the evidence shown?" not "Is this reply factually correct in the real world?" You may not know the real-world facts. Score based on what the evidence shows.

### Rule 4: Correctness Is Relative to Evidence

A reply is "correct" if it does not make claims unsupported by the evidence. If the evidence is insufficient and the reply says "We'll look into this," that is correct. If the reply says "Your refund was processed" when evidence shows nothing about refunds, that is incorrect.

### Rule 5: Consider the Customer Perspective

Ask: "If I were the customer, would this reply help me?" A reply that is technically correct but unhelpful should score low on helpfulness.

### Rule 6: Style Is Not About Personal Preference

Style is about professionalism, clarity, and naturalness. A reply can be concise and score 5 on style. A reply can be long and also score 5 if it is well-written. Do not penalize length itself.

---

## Failure Tags

Select all tags that apply:

| Tag | Description |
|-----|-------------|
| `unsupported_claim` | Reply makes a claim not supported by evidence |
| `wrong_intent` | Reply addresses a different issue than the customer's |
| `wrong_resolution` | Reply suggests an inappropriate resolution |
| `missing_context` | Reply ignores important context from the conversation |
| `too_generic` | Reply is so generic it provides no specific help |
| `unhelpful` | Reply does not help the customer |
| `incomplete` | Reply is missing important information |
| `historical_customer_info` | Reply leaks another customer's information |
| `unsupported_timeline` | Reply promises a specific timeline not in evidence |
| `unsupported_price` | Reply states a price not in evidence |
| `unsupported_policy` | Reply states a policy not in evidence |
| `awkward_style` | Reply is poorly written or unnatural |
| `too_verbose` | Reply is unnecessarily long |
| `too_short` | Reply is too brief to be useful |
| `retrieval_error` | The wrong evidence was retrieved |
| `insufficient_evidence` | Evidence was not available for this query |
| `other` | Other issue not covered by above tags |

---

## Practice Examples

### Example 1

**Customer:** "I can't log in to my account."

**Evidence:**
- KB-001: "Please reset your password using the forgot password link."
- KB-002: "If you're still having trouble, please DM us your email address."

**Reply A:** "Please reset your password using the forgot password link on the login page. If that doesn't work, DM us your email address and we'll help you further."

**Scoring:**
- Relevance: 5 — directly addresses the login issue
- Groundedness: 5 — both suggestions come from evidence
- Correctness: 5 — all claims supported
- Helpfulness: 5 — provides two clear next steps
- Completeness: 5 — covers both common and escalated scenarios
- Style: 5 — professional, clear, actionable
- Overall: 5
- Failure Tags: none

---

### Example 2

**Customer:** "Where is my order?"

**Evidence:**
- KB-003: "Please DM us your order number so we can track it for you."

**Reply B:** "Your order will arrive within 3 business days. It was shipped yesterday via FedEx."

**Scoring:**
- Relevance: 4 — addresses the order question
- Groundedness: 1 — evidence says nothing about 3 days, FedEx, or shipping date
- Correctness: 1 — claims specific details not in evidence
- Helpfulness: 3 — would be helpful if true, but may be wrong
- Completeness: 4 — provides specific information
- Style: 4 — professional and clear
- Overall: 3
- Failure Tags: `unsupported_claim`, `unsupported_timeline`

---

### Example 3

**Customer:** "This is the worst service I've ever experienced."

**Evidence:**
- KB-004: "We're sorry to hear about your experience. Please DM us your order number so we can look into this."

**Reply C:** "Thank you for reaching out!"

**Scoring:**
- Relevance: 2 — does not acknowledge the complaint
- Groundedness: 3 — "thank you" is a common support pattern but doesn't address the evidence
- Correctness: 4 — no incorrect claims
- Helpfulness: 1 — provides no help for the complaint
- Completeness: 1 — missing acknowledgment of the issue and next steps
- Style: 3 — polite but incomplete
- Overall: 2
- Failure Tags: `too_generic`, `unhelpful`, `missing_context`

---

### Example 4

**Customer:** "How do I reset my password?"

**Evidence:** (none available)

**Reply D:** "INSUFFICIENT_EVIDENCE"

**Scoring:**
- Relevance: 1 — no reply provided
- Groundedness: 5 — correctly identified no evidence
- Correctness: 5 — did not make unsupported claims
- Helpfulness: 1 — customer gets no help
- Completeness: 1 — no content
- Style: N/A — no reply to evaluate
- Overall: 3 (mean of 1, 5, 5, 1, 1)
- Failure Tags: `insufficient_evidence`

---

## Borderline Cases

### Q: What if the reply is technically correct but boring?

**A:** Score Style as 3 (acceptable). Score Helpfulness based on whether it actually helps.

### Q: What if evidence is low quality?

**A:** Score Groundedness based on whether the reply is supported by the evidence as it exists. If evidence is poor, the reply may still be grounded in what little evidence is available.

### Q: What if two replies are equally good but different?

**A:** Score each on its own merits. Both can score 5 on Relevance if they both address the issue.

### Q: What if the reply uses different words than the evidence?

**A:** Paraphrasing is acceptable. If the meaning is preserved and no new claims are added, Groundedness should be high.

### Q: What about replies that say "I'm an AI"?

**A:** This is a meta-statement, not a customer-facing reply. Score Style as 1–2 (unprofessional for customer communication).

---

## Quality Control

### Consistency Checks

- If you score the same reply twice, your scores should be within 1 point on each dimension.
- If you find yourself giving everything a 3, recalibrate using the rubric examples.

### Time Per Query

- Expect to spend 2–5 minutes per query (4 replies × 6 dimensions + tags + reason).
- Do not rush. Accuracy is more important than speed.

### When Uncertain

- If you are unsure about a score, use the midpoint (3) and note your uncertainty in the free-text reason.
- If the evidence is unclear, score Groundedness based on your best interpretation and note the ambiguity.

---

## Anonymization

- Replies are labeled System A, System B, System C, System D.
- Do NOT try to guess which system produced which reply.
- Do NOT share your guesses with other annotators.
- The system labels are randomized per query to prevent pattern guessing.
