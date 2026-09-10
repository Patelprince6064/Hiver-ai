# End-to-End AI Support Agent Architecture

## Overview

Phase 17 integrates all completed components (Phases 1-16) into a single end-to-end AI support agent pipeline. The agent processes incoming customer messages and produces either an AUTO_HANDLE response or an ESCALATE_TO_HUMAN decision.

## Architecture Diagram

```
Incoming Customer Message
            |
            v
+----------------------+
| Input Validation     |
+----------------------+
            |
            v
+----------------------+
| Text Preprocessing   |
+----------------------+
            |
            v
+----------------------+
| Intent Classifier    |
| (Phase 8)            |
+----------------------+
            |
            v
+----------------------+
| Semantic Retrieval   |
| (Phase 10)           |
+----------------------+
            |
            v
+----------------------+
| Evidence Selector    |
| (Phase 12)           |
+----------------------+
            |
            v
+----------------------+
| Grounded Reply LLM   |
| (Phase 12)           |
+----------------------+
            |
            v
+----------------------+
| Grounding Verifier   |
| (Phase 13)           |
+----------------------+
            |
            v
+----------------------+
| Escalation Policy    |
| (Phase 15-16)        |
+----------------------+
            |
            +--------------------+
            |                    |
            v                    v
     AUTO_HANDLE          ESCALATE_TO_HUMAN
            |                    |
            v                    v
     Final Reply          Human Review Package
```

## Component Integration

### 1. Input Validation (`src/agent/input_validation.py`)
- Validates message exists and is a string
- Checks message length is reasonable
- Handles optional conversation_id, message_id, conversation_context
- Returns structured validation errors

### 2. Intent Classification (`src/intents/semantic_classifier.py`)
- Uses Phase 8 SemanticIntentClassifier
- Returns predicted intent, confidence, probabilities
- On failure: ESCALATE_TO_HUMAN with appropriate reason code

### 3. Retrieval (`src/retrieval/retriever.py`)
- Uses Phase 10 HistoricalSupportRetriever
- Retrieves relevant historical support examples
- Returns evidence with similarity scores and metadata
- On failure: ESCALATE_TO_HUMAN

### 4. Evidence Selection (`src/generation/evidence_selector.py`)
- Uses Phase 12 EvidenceSelector
- Selects top 3 most relevant evidence items
- Filters by quality criteria

### 5. Grounded Reply Generation (`src/generation/grounded_reply_generator.py`)
- Uses Phase 12 GroundedReplyGenerator
- Generates reply using LLM + historical evidence
- Returns ReplyOutput with status and metadata

### 6. Grounding Verification (`src/evaluation/grounding_checks.py`)
- Uses Phase 13 grounding verification
- Checks evidence presence, PII leakage, unsupported claims
- Returns pass/review/fail status

### 7. Escalation Decision (`src/escalation/decision_engine.py`)
- Uses Phase 15-16 EscalationDecisionEngine
- Applies risk-aware policy (v1.1)
- Returns AUTO_HANDLE or ESCALATE_TO_HUMAN

## Data Flow

### AUTO_HANDLE Response
```json
{
  "decision": "AUTO_HANDLE",
  "reply": "Generated reply text",
  "intent": "order_status",
  "intent_confidence": 0.84,
  "evidence": [...],
  "grounding_status": "pass",
  "escalation": {
    "decision": "AUTO_HANDLE",
    "reason_codes": [],
    "policy_version": "v1.1"
  },
  "trace_id": "abc123"
}
```

### ESCALATE_TO_HUMAN Response
```json
{
  "decision": "ESCALATE_TO_HUMAN",
  "reply": null,
  "intent": "order_status",
  "intent_confidence": 0.48,
  "evidence": [...],
  "grounding_status": "fail",
  "escalation": {
    "decision": "ESCALATE_TO_HUMAN",
    "reason_codes": ["LOW_INTENT_CONFIDENCE", "INSUFFICIENT_EVIDENCE"],
    "risk_level": "MEDIUM",
    "policy_version": "v1.1"
  },
  "human_review": {
    "customer_message": "...",
    "predicted_intent": "...",
    "intent_confidence": 0.48,
    "escalation_reasons": ["LOW_INTENT_CONFIDENCE"],
    "recommended_action": "Review conversation and respond manually."
  },
  "trace_id": "abc123"
}
```

## Failure-Safe Behavior

The agent follows a fail-closed principle:

| Component Failure | Action |
|-------------------|--------|
| Intent classifier failure | ESCALATE_TO_HUMAN |
| Retrieval failure | ESCALATE_TO_HUMAN |
| LLM provider failure | ESCALATE_TO_HUMAN |
| Invalid LLM output | ESCALATE_TO_HUMAN |
| Grounding failure | ESCALATE_TO_HUMAN |
| Insufficient evidence | ESCALATE_TO_HUMAN |
| Escalation engine failure | ESCALATE_TO_HUMAN |

## Safety Principles

1. **No external actions**: Agent only recommends responses, never executes account changes, refunds, etc.
2. **Grounding mandatory**: All generated replies must pass grounding verification
3. **Historical evidence is reference material**: Not authoritative policy
4. **Fail-closed**: Any uncertainty or failure defaults to escalation
5. **No secrets in logs**: API keys, prompts, and sensitive data excluded from traces

## Mock Mode

The agent supports mock mode for testing without external LLM APIs:

```bash
AGENT_MODE=mock python scripts/run_agent.py --message "test"
```

Mock mode uses deterministic responses and requires no API keys or internet connection.

## Evaluation

The evaluation harness measures:

- Intent prediction accuracy
- Retrieval recall
- Grounding pass/fail rates
- AUTO_HANDLE vs ESCALATE_TO_HUMAN distribution
- Component-level failure rates
- Runtime performance

## Limitations

- Does not perform external actions (refunds, account changes)
- Does not access real customer accounts
- Does not send emails or post tweets
- Requires trained models from previous phases
- Evaluation uses synthetic data (real dataset not downloaded)

## Related Documentation

- [Architecture](./ARCHITECTURE.md)
- [Escalation Policy](./ESCALATION_POLICY.md)
- [Escalation Optimization](./ESCALATION_OPTIMIZATION.md)
- [Evaluation Protocol](./EVALUATION_PROTOCOL.md)
