# Failure 010

## Customer Message

Can you check my order status?

## Context

Conversation ID: conv_eval_0003
Message ID: msg_eval_0003

## Expected Behavior

Response should address customer inquiry accurately and safely.

## Actual Behavior

Low confidence in intent prediction

## Intent

- Predicted: order_status
- Confidence: 0.358

## Retrieval

{
  "count": 3,
  "best_score": 0.514
}

## Evidence

No evidence data available.

## Generated Reply



## Grounding

- Status: PASS
- Failure Tags: low_intent_confidence

## Escalation

- Decision: ESCALATE_TO_HUMAN

## Human Evaluation

- Score: None

## LLM Judge Evaluation

- Score: None

## Root Cause

Low confidence in intent prediction

## Root Cause Confidence

HIGH

## Hypothesis

Input lacked clear signal for intent classification

## Recommended Improvement

Implement confidence-based routing
