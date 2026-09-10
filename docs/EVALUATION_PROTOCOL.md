# Evaluation Protocol

This document defines the dataset split policy and evaluation methodology for intent classification.

---

## 1. Dataset Splits

### TRAIN

- Used for model fitting
- Contains the majority of labeled data
- Must NOT be used for any development decisions

### DEV

- Used for development decisions and hyperparameter selection
- Used for error analysis during development
- Used to compare different approaches before final evaluation

### TEST

- Optional internal test split for development analysis
- Provides a final internal check before golden evaluation
- Not used for model training or tuning

### GOLDEN

- Locked external evaluation set (Phase 6)
- NOT used for model training, hyperparameter tuning, prompt tuning, feature selection, threshold tuning, or model selection
- Used ONLY for final evaluation reporting

---

## 2. Golden Set Prohibition

The golden set must NOT be used for:

- Model training
- Hyperparameter tuning
- Prompt tuning
- Feature selection
- Threshold tuning
- Model selection
- Error analysis that leads to model changes

Unless explicitly documented as a final evaluation.

---

## 3. Split Strategy

### Conversation-Level Splitting

Messages from the same conversation must stay together. Splitting individual messages from the same conversation across splits causes leakage because:

- Messages within a conversation share context
- A model could learn conversation-specific patterns
- Evaluation results would be artificially inflated

### Ratios

| Split | Percentage | Purpose |
|-------|-----------|---------|
| TRAIN | 70% | Model fitting |
| DEV | 15% | Development decisions |
| TEST | 15% | Internal final check |
| GOLDEN | External | Locked evaluation |

### Seed

All splits use `random_seed = 42` for reproducibility.

---

## 4. Leakage Prevention

Checks performed:

- Conversation ID overlap between splits
- Message ID overlap between splits
- Exact customer-message text overlap between splits

Expected: ZERO overlap between TRAIN/DEV/TEST and GOLDEN.

If overlap is found:

- Report it
- Stop the pipeline
- Do not silently remove it
- Do not fabricate a zero-overlap result

---

## 5. Evaluation Metrics

### Primary Candidate

Macro F1 is the current candidate headline metric. Final reporting will consider the full evaluation suite.

### Full Metric Suite

| Metric | Description |
|--------|-------------|
| Accuracy | Overall correctness |
| Macro Precision | Average precision across intents |
| Macro Recall | Average recall across intents |
| Macro F1 | Average F1 across intents (candidate headline) |
| Weighted F1 | F1 weighted by class frequency |
| Per-Intent F1 | F1 for each individual intent |

### Why Macro F1

Accuracy alone can be misleading when intent classes are imbalanced. Macro F1 gives each intent equal weight, which is important because a model can achieve high overall accuracy while performing poorly on rare intents.

---

## 6. Evaluation Workflow

1. Create splits (`create_model_splits.py`)
2. Verify isolation (`verify_split_isolation.py`)
3. Train on TRAIN
4. Evaluate on DEV for development decisions
5. When frozen, evaluate on GOLDEN for reporting only
6. Never modify the model based on golden results

---

## 7. Golden-Set Protection

- Golden data is loaded via read-only functions
- Training functions reject golden dataset names
- Scripts explicitly distinguish `--dev` and `--golden`
- Warnings are printed when evaluating on golden data
