# Phase 15: Escalation Error Analysis

## Objective
Analyze escalation errors to improve the policy and understand failure modes.

## Error Categories

### 1. False Auto-Handles (CRITICAL)
System auto-handles a query that should be escalated.

**Root Causes:**
- Intent confidence too high for ambiguous queries
- Retrieval evidence present but irrelevant
- Grounding status "pass" but claims are actually unsupported
- High-risk reason not triggered

**Impact:** Customer receives incorrect or incomplete response on sensitive topic.

### 2. False Escalations
System escalates a query that could be auto-handled.

**Root Causes:**
- Intent confidence threshold too conservative
- Retrieval evidence missing but query is standard
- High-risk reasons triggered for low-risk content

**Impact:** Unnecessary human workload, slower response times.

### 3. Grounding False Positives
Grounding status "pass" but reply contains unsupported claims.

**Root Causes:**
- Claim extraction misses implicit claims
- Evidence matching too permissive
- Semantic similarity scoring artifacts

### 4. Reason Code Misclassification
Wrong reason code assigned to escalation.

**Root Causes:**
- Overlapping rule triggers
- Threshold boundaries
- Multi-signal interactions

## Analysis Results

### Auto-Handle vs Escalate Distribution
- **Auto-Handle:** ~40% (placeholder — pending dataset)
- **Escalate:** ~60% (placeholder — pending dataset)

### Risk Level Distribution
- **LOW:** Standard queries (product info, how-to)
- **MEDIUM:** Moderate complexity (returns, exchanges)
- **HIGH:** Sensitive (billing, legal, threats)

### Signal Patterns
- Cases with retrieval evidence but still escalated:主要原因通常是意图信心低或高风险触发器
- Cases without retrieval but auto-handled: 标准查询无需知识库

## Recommendations

1. **Keep confidence threshold at 0.70** — conservative default
2. **Always escalate high-risk** — no exceptions
3. **Monitor false auto-handle rate** in production
4. **A/B test threshold changes** before deployment
5. **Review escalation patterns monthly** — adjust rules as needed

## Next Steps
- Download dataset and run real evaluation
- Establish baseline false auto-handle rate
- Set up monitoring for escalation patterns
