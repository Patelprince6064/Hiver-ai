# Failure 013

## Customer Message

Sample message about order_status

## Context

Conversation ID: 
Message ID: 

## Expected Behavior

Response should address customer inquiry accurately and safely.

## Actual Behavior

Escalation triggered due to borderline threshold or low intent confidence

## Intent

- Predicted: order_status
- Confidence: 0.6648092909100984

## Retrieval

No retrieval data available.

## Evidence

No evidence data available.

## Generated Reply



## Grounding

- Status: 
- Failure Tags: intent_uncertainty, unnecessary_escalation

## Escalation

- Decision: ESCALATE_TO_HUMAN

## Human Evaluation

- Score: None

## LLM Judge Evaluation

- Score: None

## Root Cause

Escalation triggered due to borderline threshold or low intent confidence

## Root Cause Confidence

HIGH

## Hypothesis

Heuristic threshold was sensitive to mild ambiguity

## Recommended Improvement

Calibrate escalation thresholds per intent on validation data
