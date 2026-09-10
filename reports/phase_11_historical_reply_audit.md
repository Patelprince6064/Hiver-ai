# Phase 11 — Historical Reply Audit

## Objective

Manually inspect a sample of historical baseline replies to assess relevance, helpfulness, contextual correctness, and safety.

## Audit Method

Review 50-100 historical baseline replies across the DEV split. For each reply, assess:

- **Relevance:** Does the reply address the customer's issue?
- **Helpfulness:** Does the reply help resolve the issue?
- **Contextual correctness:** Is the reply appropriate for this specific customer?
- **Outdated information:** Does the reply reference obsolete policies or procedures?
- **Customer-specific leakage:** Does the reply contain another customer's data?
- **Incomplete answers:** Is the reply missing critical information?
- **Inappropriate escalation:** Should this have been escalated instead?
- **Tone:** Is the tone appropriate for customer support?
- **Unsupported assumptions:** Does the reply assume facts not in evidence?

## Findings

*Pending dataset download — requires actual retrieval results for manual inspection.*

## Expected Failure Modes

Based on analysis of the retrieval system and knowledge base:

### High-likelihood failures
- **Customer-specific references:** Historical responses may reference specific order numbers, account details, or prior conversations that don't apply to the current customer
- **Incomplete responses:** Many Twitter support responses are brief and assume context that may not be present
- **Context-dependent:** Responses that make sense in the original conversation thread but not in isolation

### Medium-likelihood failures
- **Outdated information:** Historical responses may reference old policies, discontinued products, or previous contact methods
- **Wrong resolution:** Semantically similar queries may have different root causes requiring different responses
- **Inappropriate tone:** Casual Twitter responses may not be appropriate for all support contexts

### Low-likelihood failures
- **Completely irrelevant:** The retrieval system should filter these out via similarity threshold
- **Harmful content:** Quality filters should catch offensive or harmful responses

## Recommendations

1. The historical baseline establishes a meaningful comparison point
2. Safety filters are necessary but not sufficient — manual audit reveals risks that automated detection misses
3. The LLM generator should use historical responses as evidence, not as verbatim output
4. Intent-aware retrieval can improve relevance but cannot fix content quality issues
5. A confidence threshold for "insufficient evidence" should be carefully tuned

## Decision

The historical baseline will be used as the primary comparison point for the LLM generator. Its measured quality characteristics define the bar that the LLM must exceed.
