# Phase 3 — Exploratory Data Analysis

> **Status:** Template — statistics will be populated after dataset download and notebook execution.

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Messages | *pending* |
| Conversations | *pending* |
| Brands | *pending* |
| Unique users | *pending* |
| Date range | *pending* |
| Median conversation length | *pending* |
| Maximum conversation length | *pending* |
| Single-message conversations | *pending* |
| Multi-message conversations | *pending* |

---

## 2. Brand Distribution

*Top brands by message count and conversation count will be listed here after EDA execution.*

**Observations:**
- *To be filled after analysis*

---

## 3. Conversation Structure

| Metric | Value |
|--------|-------|
| Mean length | *pending* |
| Median length | *pending* |
| P75 | *pending* |
| P90 | *pending* |
| P95 | *pending* |
| Maximum | *pending* |

**Observations:**
- *To be filled after analysis*

---

## 4. Customer vs Support Behavior

| Metric | Customer | Support |
|--------|----------|---------|
| Message count | *pending* | *pending* |
| Mean length | *pending* | *pending* |
| Median length | *pending* | *pending* |
| URL usage | *pending* | *pending* |

**Observations:**
- *To be filled after analysis*

---

## 5. Response Time

| Metric | Value |
|--------|-------|
| Sample size | *pending* |
| Median | *pending* |
| Mean | *pending* |
| P75 | *pending* |
| P90 | *pending* |
| P95 | *pending* |

**Note:** Historical response times are exploratory only and should not be interpreted as SLAs.

---

## 6. Resolution Signals

> **Important:** These are HEURISTIC signals inferred from text patterns, not ground-truth labels.

| Signal | Value |
|--------|-------|
| Conversations with thank-you | *pending* |
| Conversations with resolution language | *pending* |
| Conversations ending with support response | *pending* |

**Distinction:**
- **ACTUAL DATA LABEL:** *None available in this dataset*
- **HEURISTIC / INFERRED SIGNAL:** Thank-you detection, resolution keyword detection

---

## 7. Text Noise

| Feature | Prevalence |
|---------|------------|
| URLs | *pending* |
| @mentions | *pending* |
| #hashtags | *pending* |
| Repeated punctuation | *pending* |
| ALL CAPS | *pending* |

**Observations:**
- *To be filled after analysis*

---

## 8. Duplicate Analysis

| Metric | Value |
|--------|-------|
| Exact row duplicates | *pending* |
| Duplicate tweet IDs | *pending* |
| Duplicate texts | *pending* |

**Observations:**
- *To be filled after analysis*

---

## 9. Conversation Integrity

*Results from `scripts/analyze_conversation_integrity.py` will be summarized here.*

**Checks performed:**
- Chronological ordering within conversations
- Message ID uniqueness
- Parent message reference validity
- Conversation membership consistency
- Timestamp sanity
- Empty conversation detection

**Overall status:** *pending*

---

## 10. Dataset Quality Findings

*Key quality issues identified during EDA will be listed here.*

---

## 11. Implications for the AI Agent

1. **Brand Selection:** Use candidate table to select brands with sufficient multi-turn conversations and response coverage.
2. **Intent Definition:** Social-media noise (URLs, mentions, emojis) requires preprocessing. Intent taxonomy should account for platform-specific issues.
3. **Retrieval:** Conversation-length distribution informs context window sizing.
4. **Escalation:** No explicit resolution labels available. Escalation logic must infer resolution from conversation signals.
5. **Evaluation:** Focus on intent accuracy and reply groundedness rather than resolution rate.

---

## 12. Limitations

1. **No ground-truth resolution labels:** Cannot directly measure resolution rate.
2. **Historical data only:** Response times reflect past behavior, not current SLAs.
3. **No language field (if absent):** Cannot filter by language without additional detection.
4. **Template responses:** Some support responses may be templated, affecting reply diversity.
5. **Conversation completeness:** Some conversations may be truncated or missing messages.
6. **No intent labels:** Intent taxonomy must be derived in Phase 4, not available in raw data.
