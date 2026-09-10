# Phase 5 — Intent Discovery

> **Status:** Template — will be populated after running the intent discovery workflow.

---

## 1. Objective

Discover and define a small, meaningful set of customer-support intents from the selected brand's actual data. The taxonomy will be used for intent classification in later phases.

---

## 2. Data Used

| Metric | Value |
|--------|-------|
| Selected brand | *pending* |
| Total brand messages | *pending* |
| Customer messages | *pending* |
| Discovery sample size | *pending* |

---

## 3. Customer Message Extraction

**Method:** Used `inbound` column to identify customer vs support messages.

**Filtering rules:**
- Excluded empty or whitespace-only messages
- Excluded messages with < 2 characters
- Preserved original text (no aggressive cleaning)

---

## 4. Preprocessing

Applied normalization:
- Lowercase
- Whitespace normalization
- URL → `[URL]` placeholder
- @mention → `[MENTION]` placeholder

**Preserved:** Original text, emojis, punctuation, slang, informal language.

---

## 5. Discovery Method

**Primary:** TF-IDF + KMeans clustering

**Process:**
1. Vectorize messages using TF-IDF (unigrams + bigrams)
2. Cluster with KMeans for K = 6, 8, 10, 12, 15
3. Evaluate with silhouette score
4. Inspect cluster contents manually
5. Group into meaningful intents based on themes

---

## 6. Candidate Clusters

*Cluster inspection results will be shown after running the notebook.*

---

## 7. Manual Cluster Analysis

*Manual analysis of each cluster's theme will be documented here.*

---

## 8. Final Taxonomy

*The final intent taxonomy will be defined in `data/interim/selected_brand/intent_taxonomy.json`.*

| ID | Intent | Description |
|----|--------|-------------|
| *pending* | *pending* | *pending* |

---

## 9. Intent Distribution

*Estimated message counts per intent will be shown here.*

| Intent | Count | Percentage |
|--------|-------|------------|
| *pending* | *pending* | *pending* |

---

## 10. Confusable Intent Pairs

*Pairs of intents that are likely to be confused will be documented here.*

| Intent A | Intent B | Why Similar | How They Differ |
|----------|----------|-------------|-----------------|
| *pending* | *pending* | *pending* | *pending* |

---

## 11. Labeling Policy

**Primary Intent:** Select the customer's main support request (root cause).

**Multi-Intent:** If multiple issues exist, select the one that is the blocking issue.

**Ambiguous:** Label as `ambiguous` if intent cannot be determined.

**Out-of-Scope:** Use sparingly (< 5% of messages) for genuinely non-support content.

---

## 12. Taxonomy Risks

1. **Imbalanced intents** — some intents may be much larger than others
2. **Overlapping boundaries** — some messages may reasonably fit multiple intents
3. **Brand-specific patterns** — taxonomy may not transfer to other brands
4. **Temporal drift** — customer issues may change over time
5. **Template responses** — limited diversity in support behavior for some intents

---

## 13. Limitations

1. **No ground-truth labels** — intent taxonomy is derived from data exploration
2. **Single-brand scope** — taxonomy is specific to the selected brand
3. **Sample-based** — discovery used a sample, not the full dataset
4. **Subjective boundaries** — some intent boundaries are inherently subjective
5. **No validation yet** — taxonomy will be validated in later phases

---

## 14. Next Phase

Phase 6 will:
- Create the golden evaluation set using this taxonomy
- Establish the evaluation data protocol
- Lock the taxonomy for downstream tasks
