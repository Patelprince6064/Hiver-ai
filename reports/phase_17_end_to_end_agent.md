# Phase 17 — End-to-End AI Support Agent

## 1. Objective

Combine all completed components (Phases 1-16) into a single end-to-end AI support agent pipeline that processes customer messages and produces either AUTO_HANDLE responses or ESCALATE_TO_HUMAN decisions.

## 2. Architecture

```
Customer Message
       |
       v
+----------------------+
| Input Validation     |
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
```

## 3. Component Integration

| Component | Module | Phase |
|-----------|--------|-------|
| Intent Classification | `src/intents/semantic_classifier.py` | 8 |
| Retrieval | `src/retrieval/retriever.py` | 10 |
| Evidence Selection | `src/generation/evidence_selector.py` | 12 |
| Grounded Generation | `src/generation/grounded_reply_generator.py` | 12 |
| Grounding Verification | `src/evaluation/grounding_checks.py` | 13 |
| Escalation | `src/escalation/decision_engine.py` | 15-16 |

## 4. Input/Output Schema

### Input (AgentRequest)
```json
{
  "message": "Where is my order?",
  "conversation_id": "conv_001",
  "message_id": "msg_001",
  "conversation_context": []
}
```

### Output (AUTO_HANDLE)
```json
{
  "decision": "AUTO_HANDLE",
  "reply": "Your order is on the way.",
  "intent": "order_status",
  "intent_confidence": 0.85,
  "grounding_status": "pass",
  "escalation": {
    "decision": "AUTO_HANDLE",
    "reason_codes": [],
    "policy_version": "v1.1"
  },
  "trace_id": "abc-123"
}
```

### Output (ESCALATE_TO_HUMAN)
```json
{
  "decision": "ESCALATE_TO_HUMAN",
  "reply": null,
  "intent": "order_status",
  "intent_confidence": 0.48,
  "escalation": {
    "decision": "ESCALATE_TO_HUMAN",
    "reason_codes": ["LOW_INTENT_CONFIDENCE"],
    "policy_version": "v1.1"
  },
  "human_review": {
    "customer_message": "...",
    "predicted_intent": "order_status",
    "intent_confidence": 0.48,
    "escalation_reasons": ["LOW_INTENT_CONFIDENCE"],
    "recommended_action": "Review conversation and respond manually."
  },
  "trace_id": "abc-123"
}
```

## 5. Failure-Safe Behavior

| Component Failure | Action |
|-------------------|--------|
| Intent classifier failure | ESCALATE_TO_HUMAN |
| Retrieval failure | ESCALATE_TO_HUMAN |
| LLM provider failure | ESCALATE_TO_HUMAN |
| Invalid LLM output | ESCALATE_TO_HUMAN |
| Grounding failure | ESCALATE_TO_HUMAN |
| Insufficient evidence | ESCALATE_TO_HUMAN |
| Escalation engine failure | ESCALATE_TO_HUMAN |

## 6. Mock Mode

The agent supports mock mode for testing without external APIs:

```bash
python scripts/run_agent.py --message "test" --mock
```

## 7. Evaluation Results

### Component Metrics (Mock Mode)
- Intent accuracy: 100% (mock responses)
- Grounding pass rate: 100% (mock responses)
- AUTO_HANDLE rate: 100% (mock responses)
- ESCALATE rate: 0% (mock responses)
- System failure rate: 0%

### Runtime Performance
- Throughput: ~5,000 requests/second (mock mode)
- Average latency: <1ms per request (mock mode)

## 8. Limitations

- Does not perform external actions (refunds, account changes)
- Does not access real customer accounts
- Does not send emails or post tweets
- Requires trained models from previous phases
- Evaluation uses synthetic data (real dataset not downloaded)

## 9. What the System Does NOT Do

- Issue refunds or cancel orders
- Modify customer accounts
- Access private customer data
- Send emails or notifications
- Post to social media
- Make phone calls
- Process payments
