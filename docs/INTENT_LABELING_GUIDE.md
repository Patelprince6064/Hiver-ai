# Intent Labeling Guide

## Purpose

This guide defines how to label customer messages with intents for the selected brand. It ensures consistent, reproducible labeling across annotators.

## Selected Brand

*To be filled after brand selection.*

## Labeling Unit

One customer message / one customer turn.

Each customer message receives exactly **one primary intent** label.

---

## Primary Intent Rule

Select the customer's **main support request** — the issue that most directly explains why they are contacting support.

**Examples:**

| Message | Primary Intent | Rationale |
|---------|----------------|-----------|
| "I was charged twice and want one payment refunded" | `duplicate_charge` | The immediate problem is the duplicate charge, not the refund |
| "My order hasn't arrived and I want a refund" | `order_not_received` | The root cause is the missing order |
| "I can't login and I need to cancel my subscription" | `account_access` | The blocking issue is the login failure |

**Rule:** If a message contains multiple issues, select the one that is the **root cause** or **blocking issue**.

---

## Multi-Intent Rule

When a message contains multiple distinct support requests:

1. Identify the **primary actionable issue** — the one that must be resolved first
2. Prefer the issue that explains the customer's **immediate problem**
3. If ambiguity remains, label based on the **first mentioned** issue
4. Escalation will handle genuinely ambiguous cases in later phases

**Example:**

Message: "My order hasn't arrived and I want a refund"

- `order_not_received` (primary) — the root cause
- `refund_request` (secondary, if tracked)

**Policy:** For single-label classification, use the primary intent only.

---

## Ambiguous Message Rule

Some messages are genuinely ambiguous and cannot be clearly assigned to one intent.

**Examples:**

- "Please help"
- "What's happening?"
- "This isn't working"

**Policy:**

- Do NOT create a broad "general_help" intent to absorb ambiguous messages
- Ambiguous messages should be labeled as `ambiguous` if they cannot be reasonably classified
- In evaluation, ambiguous messages may be excluded or scored separately
- Document examples of ambiguous messages for future reference

**Threshold:** If two annotators would disagree on the intent label, the message is ambiguous.

---

## Out-of-Scope Rule

Some messages may not belong to any defined intent.

**Criteria for out-of-scope:**

- Non-support conversation (e.g., general chat, compliments without request)
- Spam or automated messages
- Unrelated discussion not involving the brand
- Unsupported topic (e.g., asking about a different company)

**Policy:**

- Do NOT allow `out_of_scope` to become a dumping ground for difficult messages
- Only use when the message genuinely cannot fit any defined intent
- Limit `out_of_scope` to < 5% of labeled data
- If `out_of_scope` is frequent, consider expanding the taxonomy

---

## Intent Definitions

*To be filled after taxonomy creation.*

For each intent:

### intent_name

**Definition:**
What this intent represents.

**Include:**
- Messages that should receive this label

**Exclude:**
- Messages that should receive a different label

**Examples:**
- Representative customer messages

**Confusable with:**
- Other intents that might be confused with this one

---

## Quality Checklist

Before finalizing labels:

- [ ] Every message has exactly one primary intent
- [ ] Intent names follow snake_case convention
- [ ] No intent is used for < 1% of messages (too rare)
- [ ] No intent is used for > 30% of messages (too broad)
- [ ] Ambiguous messages are consistently handled
- [ ] Out-of-scope is rare (< 5%)
- [ ] Confusable pairs are documented
