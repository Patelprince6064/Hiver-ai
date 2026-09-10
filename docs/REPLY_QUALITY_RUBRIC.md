# Reply Quality Evaluation Rubric

Version: 1.0
Phase: 14

---

## Overview

This rubric defines six quality dimensions for evaluating customer-support replies.
Each dimension is scored on a 1–5 integer scale.

The **overall score** is the mean of all six dimensions.

---

## Dimension 1 — Relevance

Does the reply address the customer's actual issue?

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Unrelated | Reply does not address the customer's issue at all |
| 2 | Mostly unrelated | Reply tangentially relates but misses the core issue |
| 3 | Partially relevant | Reply addresses part of the issue but not the main concern |
| 4 | Relevant | Reply addresses the customer's issue with minor gaps |
| 5 | Directly addresses | Reply clearly and directly addresses the customer's issue |

### Examples

**Customer:** "My order hasn't arrived yet."

| Reply | Score | Reason |
|-------|-------|--------|
| "Thanks for reaching out!" | 1 | No acknowledgment of the issue |
| "We offer free shipping on orders over $50." | 2 | Mentions shipping but not the specific issue |
| "We're sorry for the delay." | 3 | Acknowledges but provides no next step |
| "We're sorry for the delay. Please DM us your order number." | 4 | Acknowledges + actionable step |
| "We understand your concern about the delayed order. Please DM us your order number so we can check the status immediately." | 5 | Full acknowledgment + specific action + urgency |

---

## Dimension 2 — Groundedness

Is the response supported by the supplied historical evidence?

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Largely unsupported | Most claims have no basis in evidence |
| 2 | Multiple unsupported claims | Contains several claims not found in evidence |
| 3 | Mixed support | Some claims supported, some unsupported |
| 4 | Mostly supported | Nearly all claims traceable to evidence |
| 5 | Fully supported | Every claim in the reply is supported by evidence |

### Important Notes

- A reply that says "Please contact support" with no evidence is still grounded if the evidence shows this is a standard resolution pattern.
- A reply that invents a specific timeline ("within 2 days") when evidence says "within 24 hours" loses groundedness points.
- Generic replies ("Thanks for reaching out!") are scored as "fully supported" only if evidence shows this is an appropriate first response.

---

## Dimension 3 — Correctness

Does the reply avoid incorrect or misleading claims given the supplied evidence?

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Clearly incorrect | Contains factually wrong information relative to evidence |
| 2 | Major issue | Significant incorrect claim that could mislead the customer |
| 3 | Partially correct | Some correct information mixed with minor inaccuracies |
| 4 | Mostly correct | Minor inaccuracies that don't materially affect the reply |
| 5 | Correct | All claims are accurate relative to available evidence |

### Important Notes

- Correctness is measured **relative to available evidence**, not real-world truth.
- If evidence is insufficient, the reply is correct if it doesn't claim things unsupported by evidence.
- A reply that says "Your refund was processed" when evidence shows no refund information = score 1.
- A reply that says "We'll look into this" when evidence is insufficient = score 5 (correctly acknowledges limitations).

---

## Dimension 4 — Helpfulness

Does the reply provide a useful next step or answer?

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Not useful | Reply provides no actionable information |
| 2 | Minimally useful | Reply acknowledges but provides no path forward |
| 3 | Somewhat useful | Reply provides a general direction but lacks specificity |
| 4 | Useful | Reply provides clear, actionable next steps |
| 5 | Clearly useful | Reply provides specific, actionable steps with context |

### Examples

**Customer:** "I was charged twice for my order."

| Reply | Score | Reason |
|-------|-------|--------|
| "Thank you for contacting us." | 1 | No useful information |
| "We're sorry to hear that." | 2 | Acknowledges but no action |
| "Please contact our billing team." | 3 | Direction but vague |
| "Please DM us your order number and we'll investigate the duplicate charge." | 4 | Specific action |
| "We understand how concerning a double charge can be. Please DM us your order number and we'll investigate immediately. If confirmed, we'll process a refund within 3-5 business days." | 5 | Empathy + specific action + expected outcome |

---

## Dimension 5 — Completeness

Does the response address the important parts of the issue without unnecessary content?

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Missing core information | Reply omits the most critical part of the response |
| 2 | Major omissions | Missing an important element (e.g., no next step) |
| 3 | Partial | Addresses the main point but missing secondary elements |
| 4 | Mostly complete | Covers key points with minor gaps |
| 5 | Appropriate | Addresses all important aspects concisely |

### Important Notes

- "Appropriate" does not mean "longest possible." Concise replies can be complete.
- A reply that answers the question but omits the next step scores lower.
- A reply that includes unnecessary filler or repeated information also loses points.

---

## Dimension 6 — Style

Is the response concise, professional, polite, natural, and customer-facing?

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Poor | Unprofessional, confusing, or inappropriate tone |
| 2 | Awkward | Understandable but stilted, robotic, or rude |
| 3 | Acceptable | Clear and professional but not polished |
| 4 | Good | Professional, clear, and natural-sounding |
| 5 | Excellent | Polished, empathetic, and perfectly suited for customer communication |

### Style Criteria

- **Concise:** No unnecessary words or repetition
- **Professional:** No slang, jargon, or inappropriate language
- **Polite:** Uses courtesy language without being excessive
- **Natural:** Sounds like a human wrote it, not a template
- **Customer-facing:** Appropriate for public customer communication

---

## Overall Score

```
overall_score = mean(relevance, groundedness, correctness, helpfulness, completeness, style)
```

The overall score is always reported alongside individual dimension scores.
Do not report only the overall score.

---

## Score Ranges

| Range | Label | Interpretation |
|-------|-------|----------------|
| 4.5–5.0 | Excellent | Ready for production use |
| 3.5–4.4 | Good | Minor improvements needed |
| 2.5–3.4 | Acceptable | Noticeable issues, needs work |
| 1.5–2.4 | Poor | Significant problems |
| 1.0–1.4 | Unacceptable | Not suitable for customer use |

---

## Edge Cases

### Insufficient Evidence

When the system returns `INSUFFICIENT_EVIDENCE` or no reply:
- Relevance: 1 (no reply cannot address the issue)
- Groundedness: 5 (correctly identified insufficient evidence)
- Correctness: 5 (correctly declined to make claims)
- Helpfulness: 1 (customer gets no help)
- Completeness: 1 (no content)
- Style: N/A (no reply to evaluate) — use the score of the other 5 dimensions

### Generic Replies

A reply like "Thanks for reaching out! We'll look into this." should be scored based on what the evidence supports. If evidence shows this is a standard first response, it may score:
- Relevance: 3–4 (addresses the issue generally)
- Groundedness: 4–5 (if supported by evidence patterns)
- Correctness: 5 (no incorrect claims)
- Helpfulness: 2–3 (no specific next step)
- Completeness: 2–3 (missing specifics)
- Style: 4–5 (professional)

### Multiple Valid Answers

Customer support often has multiple valid responses. Score each reply on its own merits, not relative to other possible replies. Two replies can both score 5 on relevance if they both address the issue, even if they use different approaches.
