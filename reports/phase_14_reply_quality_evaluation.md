# Phase 14 — Reply Quality Evaluation

## Objective

Build a rigorous, blinded, human-centered reply-quality evaluation framework that determines whether the grounded LLM actually improves customer-support replies over simple baselines.

## Evaluation Design

### Blind Evaluation

Replies are anonymized as System A/B/C/D. Evaluators do not know which system produced which reply. System labels are randomized per query using a deterministic seed (42).

### Multidimensional Rubric

Six quality dimensions on a 1–5 integer scale:

1. **Relevance** — Does the reply address the customer's issue?
2. **Groundedness** — Is the reply supported by evidence?
3. **Correctness** — Does the reply avoid incorrect claims?
4. **Helpfulness** — Does the reply provide useful next steps?
5. **Completeness** — Does the reply address important parts?
6. **Style** — Is the reply professional and natural?

Overall score = mean of all six dimensions.

### Systems Compared

| System | Method | Description |
|--------|--------|-------------|
| Generic Baseline | Static | Fixed support response |
| Historical Baseline | Retrieval | Top-1 historical response verbatim |
| Grounded LLM | LLM + Retrieval | LLM with retrieved evidence |
| Grounded + Verified | LLM + Retrieval + Verification | LLM with grounding verification and repair |

### Paired Comparison

All systems are evaluated on the identical set of queries. This enables:
- Win/tie/loss analysis per query
- Paired statistical tests
- Direct system-to-system comparison

## Evaluation Dataset

### Preparation

```bash
python scripts/prepare_reply_evaluation.py --n-queries 150 --split dev --seed 42
```

Creates `data/interim/reply_eval/evaluation_manifest.jsonl` with queries sampled from the dev split.

### Sampling Strategy

- Deterministic sampling (seed 42)
- Stratified by intent when possible
- Includes common, rare, and ambiguous intents
- No selection based on model performance

## Human Annotation

### Annotation Tool

```bash
python scripts/annotate_replies.py --annotator-id annotator_1
```

Interactive CLI that:
1. Presents customer message
2. Shows 4 anonymized replies (System A/B/C/D) in random order
3. Collects 6-dimension scores (1–5) per reply
4. Collects failure tags and free-text reasons
5. Saves incrementally to `evaluation/results/human_reply_scores.jsonl`

### Failure Tags

17 predefined tags: `unsupported_claim`, `wrong_intent`, `wrong_resolution`, `missing_context`, `too_generic`, `unhelpful`, `incomplete`, `historical_customer_info`, `unsupported_timeline`, `unsupported_price`, `unsupported_policy`, `awkward_style`, `too_verbose`, `too_short`, `retrieval_error`, `insufficient_evidence`, `other`

### Inter-Annotator Agreement

If multiple annotators are available:
- 20–30% overlap subset
- Weighted Cohen's kappa for ordinal ratings
- Krippendorff's alpha where appropriate
- Spearman correlation as supplementary measure

If single annotator: reported as "single-annotator evaluation" without claiming agreement.

## System Comparison

```bash
python scripts/compare_reply_systems.py
```

Outputs:
- `pairwise_comparison.json` — Win/tie/loss for each system pair
- `reply_quality_by_intent.json` — Per-intent quality breakdown
- `system_comparison_summary.json` — Aggregate system means

### Pairwise Comparisons

| Comparison | Purpose |
|-----------|---------|
| Generic vs Historical | Which simple baseline is stronger? |
| Historical vs Grounded LLM | Does LLM add value over retrieval? |
| Grounded LLM vs Grounded + Verified | Does verification improve quality? |
| Grounded + Verified vs Historical | Is the full system better than the simple baseline? |

## Quality Analysis

```bash
python scripts/analyze_reply_quality.py
```

Outputs:
- `retrieval_vs_reply_quality.json` — Correlation between retrieval and reply quality
- `grounding_vs_helpfulness.json` — Trade-off analysis
- `top_failure_modes.json` — Top 5 failure modes with examples

## Files Created

### Documentation
- `docs/REPLY_QUALITY_RUBRIC.md` — Six-dimension scoring rubric
- `docs/REPLY_ANNOTATION_GUIDE.md` — Annotator instructions and examples

### Source Modules
- `src/evaluation/reply_evaluation_schema.py` — Pydantic schemas for evaluation records
- `src/evaluation/automated_reply_metrics.py` — Supplementary automated diagnostics

### Scripts
- `scripts/prepare_reply_evaluation.py` — Prepare evaluation dataset
- `scripts/run_reply_evaluation.py` — Run all systems on evaluation queries
- `scripts/annotate_replies.py` — Interactive annotation tool
- `scripts/compare_reply_systems.py` — System comparison and pairwise analysis
- `scripts/analyze_reply_quality.py` — Quality analysis and failure identification

### Tests (71 new, 520 total)
- `tests/test_reply_evaluation_schema.py` — 17 tests
- `tests/test_automated_reply_metrics.py` — 20 tests
- `tests/test_pairwise_comparison.py` — 9 tests
- `tests/test_evaluation_sampling.py` — 11 tests
- `tests/test_annotation_validation.py` — 13 tests

## Current Status

### Before Human Annotation

All automated components are functional:
- Evaluation manifest can be prepared (requires dataset download)
- All systems can run on same queries (requires dataset + index)
- Blind labels and randomization work correctly
- Annotation tool is ready for human use
- Comparison and analysis scripts handle missing scores gracefully

### Pending

- Dataset download (Phase 2 prerequisite)
- Human annotation (requires annotator)
- Real evaluation scores
- Actual system comparison results

## Decisions Logged

- Decision 121: Human Evaluation Is Necessary for Reply Quality
- Decision 122: Reply Quality Is Multidimensional
- Decision 123: Exact-Match Metrics Are Not Primary
- Decision 124: Blind Evaluation Prevents Evaluator Bias
- Decision 125: Reply Order Is Randomized Per Query
- Decision 126: Same Queries for All Systems
- Decision 127: Fixed Rubric Ensures Consistency
- Decision 128: Grounding and Helpfulness Are Evaluated Separately
- Decision 129: Automated Metrics Are Supplementary
- Decision 130: Paired Comparisons Over Independent Rankings
- Decision 131: Golden Data Is Not Used for Tuning
- Decision 132: Single Annotator Results Are Reported Honestly

## Test Results

```
520 passed, 1 warning in 12.84s
```

All 71 new Phase 14 tests pass. All 449 existing tests continue to pass.
