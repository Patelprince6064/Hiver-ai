# Phase 11 — Reply Generation Baseline

## Objective

Establish a strong, measurable, non-LLM reply-generation baseline using generic responses and historical support responses, so Phase 12 can prove whether grounded LLM generation actually improves reply quality.

## Why a Baseline Is Necessary

The final report must compare the advanced system against simple baselines. Do not jump directly from "no system" to "LLM + RAG". Instead establish:

- **Baseline 1:** Generic response
- **Baseline 2:** Historical response retrieval
- **Baseline 3:** Future grounded LLM

This allows the final report to answer: "Does the LLM actually improve reply quality beyond simply retrieving a historical support response?"

## Generic Baseline

Returns a fixed generic support response for every query. No retrieval, no evidence. Intentionally simple to establish a floor for reply quality.

## Historical Response Baseline

Retrieves the top-ranked historical support response via the Phase 10 semantic retriever and returns it directly as the candidate reply. No rewriting, summarization, or improvement. If the historical response is poor, the baseline remains poor — that is useful for evaluation.

## Architecture

```
Incoming Customer Message
          ↓
Intent Classification (Phase 8)
          ↓
Historical Retrieval (Phase 10)
          ↓
Top Historical Support Response
          ↓
Simple Reply Selection
          ↓
Safety/Risk Detection
          ↓
Baseline Reply
```

## Evaluation Method

Evaluated on DEV split using:
- Response coverage
- Evidence availability
- Similarity score distribution
- Intent consistency
- Resolution consistency
- Safety risk rate
- Reply length distribution

BLEU/ROUGE are intentionally not used as primary metrics because there is no single correct reply for a customer message.

## Results

*Pending dataset download — requires actual knowledge base and retrieval index.*

## Copying Risks

Historical responses may contain:
- Outdated wording
- Customer-specific references (order IDs, names)
- URLs, email addresses, phone numbers
- Context-dependent responses

Safety detection flags these risks without modifying the response.

## Failure Analysis

Eight failure categories identified:
1. Correct historical response
2. Relevant issue but wrong resolution
3. Semantically similar but contextually wrong
4. Customer-specific information copied
5. Incomplete response
6. Outdated/uncertain historical behavior
7. No useful historical evidence
8. Generic response is safer than historical response

## Important Observations

**Retrieval ≠ Generation.** A highly similar historical response may still contain stale information, refer to a different customer, require missing context, suggest an inappropriate action, or be incomplete.

**Similarity ≠ Correctness.** High semantic similarity does not guarantee the response is correct or appropriate for the current query.

## What This Baseline Cannot Do

- Rewrite or improve historical responses
- Handle multi-turn conversations
- Generate novel responses
- Ensure factual accuracy of copied content
- Adapt historical responses to current context

## Implications for the LLM Generator

The LLM generator (Phase 12) should:
- Use retrieved evidence as context, not as verbatim reply
- Synthesize multiple evidence sources
- Adapt responses to the current conversation
- Flag uncertain information
- Escalate when evidence is insufficient

## Decision

Semantic retrieval baseline is the recommended comparison point for the LLM generator. If the LLM cannot outperform simply returning the most similar historical response, the additional complexity is not justified.
