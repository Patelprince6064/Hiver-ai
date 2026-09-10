# Phase 7 — Intent Classification Baselines

## 1. Evaluation Protocol

The evaluation protocol defines dataset splits and golden-set protection. See `docs/EVALUATION_PROTOCOL.md` for full details.

**Key principles:**
- TRAIN for model fitting only
- DEV for development decisions
- GOLDEN for final evaluation only (never for tuning)
- Conversation-level splitting to prevent leakage

## 2. Dataset Splits

| Split | Purpose | Method |
|-------|---------|--------|
| TRAIN (70%) | Model fitting | Conversation-level split |
| DEV (15%) | Development decisions | Conversation-level split |
| TEST (15%) | Internal final check | Conversation-level split |
| GOLDEN | Locked evaluation | External (Phase 6) |

Split sizes will be populated after dataset download.

## 3. Leakage Prevention

All splits are verified for zero overlap with the golden set:
- Conversation ID overlap
- Message ID overlap
- Exact text overlap

## 4. Baseline 1 — Majority Class

**Type:** Trivial baseline

**Method:**
- Inspects TRAIN labels
- Identifies most frequent intent
- Always predicts that intent

**Purpose:** Establishes a lower bound. Any useful model must exceed this baseline.

## 5. Baseline 2 — TF-IDF + Logistic Regression

**Type:** Simple ML baseline

**Pipeline:**
1. Text preprocessing (lowercase, URL/mention normalization)
2. TF-IDF vectorization (1-2 grams, min_df=2, max_df=0.95)
3. Logistic Regression (balanced classes, max_iter=1000)

**Configuration:** See `configs/baselines.yaml`

## 6. Development Results

Results will be populated after training on the downloaded dataset.

## 7. Golden Results

Results will be populated after golden-set evaluation.

## 8. Error Analysis

Error analysis will be populated after model training.

## 9. Confidence Analysis

Confidence analysis will be populated after model training.

## 10. Baseline Comparison

| Model | Accuracy | Macro F1 | Weighted F1 |
|-------|----------|----------|-------------|
| Majority Class | *pending* | *pending* | *pending* |
| TF-IDF + LogReg | *pending* | *pending* | *pending* |

## 11. Why Macro F1

Accuracy alone can be misleading when intent classes are imbalanced. Macro F1 gives each intent equal weight, which is important because a model can achieve high overall accuracy while performing poorly on rare intents.

**Candidate headline metric:** Macro F1 is the current candidate headline metric; final reporting will consider the full evaluation suite.

## 12. Golden-Set Protection

- Golden data is loaded via read-only functions
- Training functions reject golden dataset names
- Scripts explicitly distinguish `--dev` and `--golden`
- Warnings are printed when evaluating on golden data
