# Escalation Annotation Guide

## Task

You are deciding whether the AI system should **auto-handle** a customer support query or **escalate it to a human agent**.

## Decision Labels

- **AUTO_HANDLE**: The AI can safely and effectively handle this query end-to-end.
- **ESCALATE_TO_HUMAN**: A human agent should handle this query.

## When to ESCALATE

Escalate if ANY of the following apply:

1. **Billing / Financial claims**: Customer mentions prices, charges, amounts, invoices
2. **Account-specific issues**: Requires login, account verification, or personal data
3. **Legal threats**: Customer mentions lawyers, legal action, complaints
4. **Emotional / Distressed**: Customer is visibly upset, threatening, or in distress
5. **Complex multi-step**: Requires actions across multiple systems
6. **Uncertain**: You are not confident the AI can handle this correctly

## When to AUTO_HANDLE

Auto-handle ONLY if ALL of the following apply:

1. **Factual question**: Product info, how-to, specifications
2. **Supported by evidence**: Knowledge base contains relevant information
3. **Low risk**: No financial, legal, or account implications
4. **Clear intent**: Single, unambiguous request
5. **Standard process**: Follows a known, documented procedure

## Practice Examples

### Example 1
**Query**: "How do I reset my password?"
**Decision**: AUTO_HANDLE
**Reason**: Standard procedure, no account access needed, clear intent

### Example 2
**Query**: "You charged me twice for my order!"
**Decision**: ESCALATE_TO_HUMAN
**Reason**: BILLING_CLAIM — requires account verification and financial investigation

### Example 3
**Query**: "I'm going to sue you if this isn't fixed"
**Decision**: ESCALATE_TO_HUMAN
**Reason**: LEGAL_THREATS — always escalate

### Example 4
**Query**: "What's the difference between Product A and Product B?"
**Decision**: AUTO_HANDLE (if evidence available)
**Reason**: Factual comparison, no risk

### Example 5
**Query**: "I want to cancel my subscription and get a refund"
**Decision**: ESCALATE_TO_HUMAN
**Reason**: Multi-intent (cancellation + refund), both high-risk

## Rules of Thumb

1. **When in doubt, escalate.** False auto-handles are worse than false escalations.
2. **Billing = always escalate.** Even if you think the AI can answer, escalate.
3. **Emotional = escalate.** Human agents handle tone and empathy better.
4. **Multi-step = escalate.** If it requires 3+ steps, escalate.
5. **Legal/Threats = always escalate.** No exceptions.

## Quality Control

- Annotate each query independently
- Record your confidence level (high/medium/low)
- Add notes for edge cases
- Inter-annotator agreement target: Cohen's κ ≥ 0.80
