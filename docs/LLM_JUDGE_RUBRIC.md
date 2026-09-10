# LLM Judge Rubric

## Overview

This document defines the evaluation rubric for the LLM-as-judge system.

**Important:** Human evaluation remains the primary reference for reply quality. The LLM judge is a supplementary automated evaluator for scalable evaluation.

## Evaluation Dimensions

The LLM judge evaluates replies on six dimensions, each scored 1-5:

### 1. Relevance (1-5)

Does the reply address the customer's actual request?

- **5**: Directly and completely addresses the customer's specific request
- **4**: Addresses the main request with minor tangential content
- **3**: Partially addresses the request but misses key aspects
- **2**: Tangentially related but doesn't address the core request
- **1**: Completely irrelevant to the customer's request

### 2. Groundedness (1-5)

Are claims supported by the supplied evidence?

- **5**: All claims are directly supported by provided evidence
- **4**: Most claims are supported; minor unsupported statements
- **3**: Some claims are supported, some are unsupported
- **2**: Most claims are unsupported by evidence
- **1**: Claims are fabricated or contradicted by evidence

### 3. Correctness (1-5)

Is the reply consistent with the evidence and conversation?

- **5**: Factually accurate and consistent with all provided information
- **4**: Mostly accurate with minor inconsistencies
- **3**: Some factual errors or inconsistencies
- **2**: Significant factual errors
- **1**: Completely incorrect or contradicts evidence

### 4. Helpfulness (1-5)

Does the reply provide useful assistance?

- **5**: Provides clear, actionable assistance that solves the problem
- **4**: Helpful but could be more actionable or complete
- **3**: Somewhat helpful but doesn't fully resolve the issue
- **2**: Minimal helpfulness; doesn't address the core need
- **1**: Not helpful at all; wastes the customer's time

### 5. Completeness (1-5)

Does it address important parts of the request?

- **5**: Addresses all aspects of the request thoroughly
- **4**: Addresses most aspects with minor omissions
- **3**: Addresses some aspects but misses important parts
- **2**: Addresses only minor aspects of the request
- **1**: Barely addresses the request at all

### 6. Style (1-5)

Is it clear, professional, concise, and appropriate?

- **5**: Excellent clarity, tone, and professionalism
- **4**: Good style with minor issues
- **3**: Acceptable but could be clearer or more professional
- **2**: Poor style; confusing, too verbose, or inappropriate tone
- **1**: Very poor style; unprofessional or incomprehensible

## Overall Score

The overall score is the mean of the six dimension scores:

```
overall = (relevance + groundedness + correctness + helpfulness + completeness + style) / 6
```

The overall score is calculated locally, not from LLM output, to ensure accuracy.

## Failure Tags

The judge may apply failure tags when issues are detected:

- `unsupported_claim`: Reply contains claims not supported by evidence
- `wrong_intent`: Reply addresses wrong customer intent
- `wrong_resolution`: Reply provides incorrect resolution
- `missing_context`: Reply ignores important context
- `too_generic`: Reply is too generic and not personalized
- `unhelpful`: Reply does not help the customer
- `incomplete`: Reply misses important parts of the request
- `historical_customer_info`: Reply assumes historical info is current
- `unsupported_timeline`: Reply makes timeline claims without evidence
- `unsupported_price`: Reply makes price claims without evidence
- `unsupported_policy`: Reply cites policies without evidence
- `awkward_style`: Reply has awkward phrasing or tone
- `too_verbose`: Reply is unnecessarily long
- `too_short`: Reply is too brief to be helpful
- `retrieval_error`: Evidence retrieval appears to have failed
- `insufficient_evidence`: Available evidence is insufficient
- `other`: Other issue not covered above

## Evidence Boundary

The judge must only use supplied evidence. It must NOT:

- Browse the internet
- Invent policies
- Infer current prices
- Infer current delivery times
- Assume historical responses are still valid
- Assume an account action occurred
- Assume an order status
- Assume a refund was completed

Historical support responses are reference material, not authoritative current policy.

## Blind Evaluation

To prevent bias, the judge receives:

- Customer message
- Conversation context
- Intent and confidence
- Evidence
- Candidate reply

The judge does NOT receive:

- System name/model identity
- Provider information
- Human scores
- Expected scores
- Whether reply came from baseline or final system

## Comparison with Human Evaluation

Human evaluation remains the primary reference. The LLM judge complements human evaluation by providing:

- Scalable evaluation of many examples
- Consistent scoring across examples
- Rapid feedback for iteration

However, the LLM judge:

- May not capture subtle nuances that humans notice
- Can be biased by confident-sounding text
- May not understand domain-specific context
- Should not replace human evaluation for final decisions

## Scoring Rules

1. Do NOT reward a reply merely because it sounds confident
2. Do NOT assume unsupported business policies
3. Do NOT infer facts not present in the evidence
4. If evidence is insufficient, penalize unsupported claims
5. Historical responses are reference material, not current policy
6. Score based only on provided evidence