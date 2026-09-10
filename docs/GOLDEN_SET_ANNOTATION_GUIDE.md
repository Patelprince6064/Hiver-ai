# Golden Set Annotation Guide

## Purpose

This guide defines how to annotate customer messages for the golden evaluation set. The golden set is the **locked evaluation dataset** — it must NOT be used for model training or tuning.

## Annotation Unit

One incoming customer message.

## Available Intents

The intent taxonomy is defined in `data/interim/selected_brand/intent_taxonomy.json`.

## Primary Intent Rule

Choose ONE primary intent — the customer's **main support request**.

If multiple issues exist:
1. Select the **root cause** or **blocking issue**
2. Prefer the issue that explains the customer's **immediate problem**
3. If ambiguity remains, label based on the **first mentioned** issue

## Multi-Intent Rule

For single-label classification, use the primary intent only.

Example:
- Message: "My order hasn't arrived and I want a refund"
- Primary: `order_not_received` (root cause)

## Ambiguous Examples

Mark as ambiguous when:
- Two annotators would disagree on the intent
- The message is too vague to determine intent
- The message contains multiple equal-priority issues

## Confidence Levels

| Level | Definition |
|-------|------------|
| HIGH | Clear intent, no doubt about label |
| MEDIUM | Reasonable intent, some ambiguity possible |
| LOW | Uncertain intent, could reasonably be another label |

## Difficult Cases

### Short messages
- "refund?"
- "where is it?"
- Consider context if available

### Noisy messages
- "@Brand help!!! #broken"
- Preserve noise in original text
- Label based on underlying intent

### Spelling errors
- "I cant loggin"
- Infer intended meaning
- Don't penalize for typos

### Multiple issues
- Select root cause
- Document secondary issues in notes

## Quality Rules

1. Do not infer information not present in the message/context
2. Do not create new labels
3. Do not change labels to improve future model accuracy
4. Record uncertainty explicitly
5. Use notes field for reasoning on difficult cases
