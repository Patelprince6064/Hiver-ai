# Final Metrics Definitions

This document defines every metric reported in the final evaluation.

## Intent Classification Metrics

### Accuracy

**Definition:** The proportion of correctly classified examples out of all examples.

**Formula:** `accuracy = correct_predictions / total_predictions`

**Dataset:** Final evaluation set (200 synthetic examples)

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Does not account for class imbalance
- May be misleading if classes are unevenly distributed
- Simulated results based on synthetic data

### Macro F1

**Definition:** The unweighted average of F1 scores across all intent classes.

**Formula:** `macro_f1 = mean(per_class_f1)`

**Dataset:** Final evaluation set (200 synthetic examples)

**Interpretation:** Higher is better. Range: 0.0 to 1.0. Primary metric for intent classification.

**Limitations:**
- Treats all classes equally regardless of size
- May penalize performance on rare intents
- Simulated results based on synthetic data

### Weighted F1

**Definition:** The weighted average of F1 scores, weighted by class support.

**Formula:** `weighted_f1 = sum(class_f1 * class_support) / total_examples`

**Dataset:** Final evaluation set (200 synthetic examples)

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- May be dominated by majority classes
- Simulated results based on synthetic data

## Retrieval Metrics

### Recall@K

**Definition:** The proportion of relevant documents retrieved in the top K results.

**Formula:** `recall@K = relevant_in_top_K / total_relevant`

**Dataset:** Final evaluation set with simulated relevance labels

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Relevance labels are simulated, not human-annotated
- Does not account for ranking quality

### MRR (Mean Reciprocal Rank)

**Definition:** The average reciprocal rank of the first relevant document.

**Formula:** `mrr = mean(1 / rank_of_first_relevant)`

**Dataset:** Final evaluation set with simulated relevance labels

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Only considers the first relevant document
- Relevance labels are simulated

## Reply Quality Metrics

### Mean Quality Score

**Definition:** The average overall quality score across all dimensions.

**Formula:** `mean_quality = mean(relevance, groundedness, correctness, helpfulness, completeness, style)`

**Dataset:** Final evaluation set with simulated quality scores

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Quality scores are simulated, not from real LLM outputs
- Does not capture subjective preferences
- Six dimensions may not cover all quality aspects

### Per-Dimension Scores

**Definition:** Individual scores for each quality dimension.

**Dimensions:**
- Relevance: Does the reply address the customer's issue?
- Groundedness: Is the reply supported by evidence?
- Correctness: Is the reply factually correct?
- Helpfulness: Does the reply help the customer?
- Completeness: Does the reply cover all necessary information?
- Style: Is the reply well-written and professional?

**Dataset:** Final evaluation set with simulated scores

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Scores are simulated, not from real evaluations
- May not reflect actual customer satisfaction

## Grounding Metrics

### Grounding Pass Rate

**Definition:** The proportion of replies that pass all grounding checks.

**Formula:** `pass_rate = passed_checks / total_replies`

**Dataset:** Final evaluation set with simulated grounding results

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Rule-based checks only, not semantic verification
- Passing checks does not guarantee factual correctness
- Simulated results

### Unsupported Claim Rate

**Definition:** The proportion of replies containing unsupported claims.

**Formula:** `unsupported_rate = replies_with_unsupported_claims / total_replies`

**Dataset:** Final evaluation set with simulated claim extraction

**Interpretation:** Lower is better. Range: 0.0 to 1.0

**Limitations:**
- Claim extraction is rule-based
- May miss some unsupported claims
- Simulated results

### High-Risk Claim Rate

**Definition:** The proportion of replies containing high-risk unsupported claims (price, refund, timeline guarantees).

**Formula:** `high_risk_rate = replies_with_high_risk_claims / total_replies`

**Dataset:** Final evaluation set with simulated claim extraction

**Interpretation:** Lower is better. Range: 0.0 to 1.0

**Limitations:**
- High-risk detection is rule-based
- May have false positives/negatives
- Simulated results

## Escalation Metrics

### AUTO_HANDLE_RATE

**Definition:** The proportion of requests that are auto-handled.

**Formula:** `auto_handle_rate = auto_handled_requests / total_requests`

**Dataset:** Final evaluation set with simulated escalation decisions

**Interpretation:** Higher is better (more automation), but must balance with safety. Range: 0.0 to 1.0

**Limitations:**
- Does not account for correctness of auto-handle decisions
- Simulated results

### FALSE_AUTO_HANDLE_RATE

**Definition:** The proportion of auto-handled requests that should have been escalated.

**Formula:** `false_auto_rate = incorrect_auto_handles / total_auto_handles`

**Dataset:** Final evaluation set with simulated ground truth labels

**Interpretation:** Lower is better. This is the primary safety metric. Range: 0.0 to 1.0

**Limitations:**
- Ground truth labels are simulated
- "Should have escalated" is based on synthetic rules
- Simulated results

### FALSE_ESCALATION_RATE

**Definition:** The proportion of escalated requests that could have been auto-handled.

**Formula:** `false_escalation_rate = unnecessary_escalations / total_escalations`

**Dataset:** Final evaluation set with simulated ground truth labels

**Interpretation:** Lower is better (less unnecessary human work). Range: 0.0 to 1.0

**Limitations:**
- Ground truth labels are simulated
- Simulated results

### Expected Cost

**Definition:** The expected cost of escalation decisions, weighted by error severity.

**Formula:** `expected_cost = (false_auto_rate * 10.0) + (false_escalation_rate * 1.0)`

**Dataset:** Final evaluation set with simulated decisions

**Interpretation:** Lower is better. Weights: false auto-handle = 10x, false escalation = 1x

**Limitations:**
- Cost weights are assumptions, not actual business costs
- Simulated results

## End-to-End Metrics

### System Failure Rate

**Definition:** The proportion of requests that fail due to system errors.

**Formula:** `failure_rate = failed_requests / total_requests`

**Dataset:** Final evaluation set with simulated agent processing

**Interpretation:** Lower is better. Range: 0.0 to 1.0

**Limitations:**
- Simulated failures, not real system errors
- Does not capture partial failures

### Evidence Coverage Rate

**Definition:** The proportion of requests where evidence was retrieved.

**Formula:** `evidence_rate = requests_with_evidence / total_requests`

**Dataset:** Final evaluation set with simulated retrieval

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Evidence retrieval is simulated
- Does not account for evidence quality

### Safe Auto-Handle Rate

**Definition:** The proportion of auto-handled requests that were correctly auto-handled.

**Formula:** `safe_auto_rate = correct_auto_handles / total_requests`

**Dataset:** Final evaluation set with simulated ground truth

**Interpretation:** Higher is better. Range: 0.0 to 1.0

**Limitations:**
- Ground truth is simulated
- Does not capture edge cases

### Unsafe Auto-Handle Rate

**Definition:** The proportion of auto-handled requests that should have been escalated.

**Formula:** `unsafe_auto_rate = incorrect_auto_handles / total_requests`

**Dataset:** Final evaluation set with simulated ground truth

**Interpretation:** Lower is better. This is a critical safety metric. Range: 0.0 to 1.0

**Limitations:**
- Ground truth is simulated
- May miss some unsafe cases

---

## Important Notes

1. **All metrics are simulated.** The real dataset was not downloaded, so all evaluation uses synthetic data.

2. **Golden set is empty.** No locked evaluation was performed.

3. **Quality scores are simulated.** Reply quality was not evaluated by humans or LLM judges.

4. **Ground truth is synthetic.** Escalation labels and intent labels are generated, not human-annotated.

5. **Do not overinterpret these metrics.** They demonstrate the evaluation framework, not actual system performance.
