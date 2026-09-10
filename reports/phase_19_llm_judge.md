# Phase 19 — LLM-as-Judge for Reply Quality

## 1. Objective

Build an LLM-as-judge evaluation system for customer-support reply quality that provides scalable automated evaluation while maintaining human evaluation as the primary reference.

## 2. Why LLM-as-Judge

Traditional metrics like BLEU or ROUGE measure surface-level text similarity but fail to capture:
- Whether the reply is grounded in evidence
- Whether the reply is actually helpful
- Whether the reply addresses the customer's specific request
- Style and appropriateness for customer support

The LLM judge evaluates replies across six dimensions that matter for customer support quality.

## 3. Human Evaluation Remains the Reference

**Critical principle:** Human evaluation from Phase 14 remains the primary reference for reply quality.

The LLM judge:
- Complements human evaluation
- Enables scalable evaluation of many examples
- Provides consistent scoring
- Should NOT replace human evaluation for final decisions

## 4. Rubric

The LLM judge uses the same six dimensions as human evaluation:

| Dimension | Description |
|-----------|-------------|
| Relevance | Does the reply address the customer's actual request? |
| Groundedness | Are claims supported by the supplied evidence? |
| Correctness | Is the reply consistent with the evidence and conversation? |
| Helpfulness | Does the reply provide useful assistance? |
| Completeness | Does it address important parts of the request? |
| Style | Is it clear, professional, concise, and appropriate? |

Each dimension is scored 1-5. Overall score is the mean of six dimensions.

## 5. Judge Prompt

The judge receives:
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

## 6. Blind Evaluation Design

To prevent bias:
1. Systems are anonymized with labels A, B, C, D
2. Mapping is stored separately
3. Judge prompt contains no system identity
4. Audit script verifies blindness

## 7. Systems Evaluated

Four systems from Phase 18:
1. **Generic Baseline**: Template-based response
2. **Historical Baseline**: Retrieved historical response
3. **Grounded LLM**: LLM generation with evidence
4. **Grounded LLM + Verification**: LLM generation with grounding checks

## 8. Judge Reliability

Reliability measured by running repeated evaluations on subset of examples.

**Results:**
- Mock judge: 100% deterministic (by design)
- Real LLM judge: Requires actual API calls to measure
- Variance should be 0 with temperature=0

**Note:** Real LLM reliability results require API key configuration.

## 9. Human vs LLM Agreement

**Note:** Since real human evaluation data is not available (golden set is empty), the comparison uses simulated human scores based on Phase 18 system performance.

**Agreement Metrics (Simulated):**
- Overall correlation: Requires real human data
- Exact agreement: Requires real human data
- Within-1 agreement: Requires real human data

## 10. Dimension-Level Agreement

Agreement is measured per dimension:
- **Relevance**: How well does the LLM judge align with human relevance scores?
- **Groundedness**: Is the LLM judge better at detecting unsupported claims?
- **Style**: Does the LLM judge agree on style quality?

**Note:** Dimension-level agreement requires real human annotations.

## 11. System Ranking Agreement

Compare whether human and LLM judges rank systems similarly:

**Expected ranking (based on Phase 18):**
1. Grounded LLM + Verification
2. Grounded LLM
3. Historical Baseline
4. Generic Baseline

**LLM judge ranking:** Requires actual evaluation.

## 12. Pairwise Agreement

For every pair of systems (A vs B), compare:
- Human: A > B, A = B, A < B
- LLM: A > B, A = B, A < B

Calculate pairwise agreement rate.

## 13. Judge Bias Analysis

Potential biases analyzed:
- **Verbosity bias**: Does LLM favor longer replies?
- **Confidence bias**: Does LLM favor confident-sounding text?
- **Style bias**: Does LLM over-weight style over substance?

**Method:** Correlation between reply length and LLM scores.

## 14. Disagreement Examples

Examples where human and LLM scores differ significantly are collected for review.

**Purpose:**
- Understand judge limitations
- Identify systematic biases
- Improve judge prompt if needed

## 15. Limitations

1. **No real human data**: Agreement analysis uses simulated scores
2. **No real LLM API**: Mock judge provides deterministic but artificial results
3. **Synthetic evaluation data**: Not from real customer support
4. **Single judge**: No inter-annotator agreement for LLM judge
5. **Domain specificity**: May not generalize to other domains

## 16. Recommendation

**Can this LLM judge replace human evaluation?**

Based on the current implementation:
- **No, not yet.** The judge is a useful supplementary tool but cannot replace human evaluation.

**Evidence:**
1. Human evaluation remains the primary reference
2. LLM judges can be biased by confident-sounding text
3. Domain-specific context may be missed
4. Agreement requires validation on real data

**When could it replace human evaluation?**
- After validating on real customer support data
- After measuring strong agreement (Spearman > 0.8)
- After confirming no systematic biases
- After domain-specific tuning

**Current recommendation:** Use LLM judge for scalable screening and iteration, but rely on human evaluation for final decisions.

## 17. Interviewer-Ready Answers

**Q1: Why do you need an LLM judge?**
Scalable evaluation of many examples while maintaining quality standards.

**Q2: Why not just use BLEU or ROUGE?**
These metrics measure text similarity, not whether the reply is grounded, helpful, or addresses the customer's request.

**Q3: How did you prevent the judge from being biased?**
Blind evaluation, prohibited terms, evidence-only scoring, bias analysis.

**Q4: Did you hide the system identity?**
Yes, systems are anonymized as A/B/C/D with separate mapping.

**Q5: How well does the LLM judge agree with humans?**
Requires real human data for validation. Current implementation uses simulated scores.

**Q6: Which dimensions does it judge well?**
Groundedness and relevance are most objective. Style is most subjective.

**Q7: Where does it disagree with humans?**
Likely on style and helpfulness where human judgment is more nuanced.

**Q8: Does it favor longer answers?**
Bias analysis will measure correlation between length and scores.

**Q9: Can the LLM judge replace human evaluation?**
Not yet. Use for screening, not final decisions.

**Q10: How do you know your judge isn't just rewarding confident-sounding answers?**
Blind evaluation and evidence-based scoring help, but requires validation.