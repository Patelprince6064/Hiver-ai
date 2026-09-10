# Phase 4 — Brand Selection

> **Status:** Template — actual values will be populated after running `scripts/compute_brand_statistics.py`.

---

## 1. Objective

The Hiver assignment requires selecting ONE brand from the Customer Support on Twitter dataset and building an AI support agent around it. This report documents the selection methodology, candidate analysis, and final decision.

---

## 2. Selection Criteria

The brand selection is based on **data suitability** — not model performance. This avoids circular selection (where we would choose a brand based on how well a model works on it, which hasn't been built yet).

### Scoring Dimensions

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Conversation Volume | 0.20 | More conversations provide richer historical grounding and more training data. |
| Multi-turn Coverage | 0.20 | Multi-turn conversations are essential for understanding customer intent and support resolution patterns. |
| Support Response Coverage | 0.20 | We need actual brand responses to ground reply generation. |
| Conversation Quality | 0.15 | Brands with better-structured conversations are easier to work with. |
| Customer-Support Density | 0.10 | Higher density means more actual support interactions vs. noise. |
| Issue Diversity Proxy | 0.10 | Diverse customer issues lead to a richer intent taxonomy. |
| Evaluation Suitability | 0.05 | Must have enough data for train/val/test splits and a golden set. |

---

## 3. Scoring Method

### Normalization

Each dimension is min-max normalized to [0, 1]:

```
normalized = (value - min) / (max - min)
```

If max == min (all values identical), normalized value = 0.5.

### Weight Application

Total score = sum(normalized_value * weight) for each dimension.

### Handling Missing Metrics

If a metric cannot be calculated (e.g., no inbound column), the corresponding dimension is set to 0.5 (neutral) and the weight is redistributed proportionally.

---

## 4. Candidate Brands

*Top 10 candidates will be shown after running `scripts/compute_brand_statistics.py`.*

| Rank | Brand | Score | Conversations | Messages | Multi-turn % | Response Coverage |
|------|-------|-------|---------------|----------|--------------|-------------------|
| 1 | *pending* | *pending* | *pending* | *pending* | *pending* | *pending* |
| 2 | *pending* | *pending* | *pending* | *pending* | *pending* | *pending* |
| ... | ... | ... | ... | ... | ... | ... |

---

## 5. Final Selected Brand

**Selected brand:** *To be determined after running the scoring script.*

---

## 6. Why This Brand

*Evidence-based rationale will be provided after selection.*

Key factors to discuss:
- Conversation volume and coverage
- Multi-turn availability
- Response coverage for historical grounding
- Data quality and noise level
- Suitability for intent discovery

---

## 7. Alternatives Considered

*Top 2-3 alternatives and reasons for not selecting them will be discussed after selection.*

---

## 8. Risks

*Risks specific to the selected brand will be documented after selection.*

Potential risks to evaluate:
- Imbalanced intent distribution
- Templated or low-diversity support responses
- Missing metadata (timestamps, conversation IDs)
- Short conversations limiting context
- Social-media noise requiring preprocessing
- Sparse issue categories

---

## 9. Final Decision

**Selected brand:** *To be determined.*

**Rationale:** *To be determined.*

**Reproduction:**

```bash
python scripts/compute_brand_statistics.py
python scripts/extract_selected_brand.py
python scripts/analyze_selected_brand.py
```
