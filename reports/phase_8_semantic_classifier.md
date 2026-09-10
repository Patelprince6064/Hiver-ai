# Phase 8 — Semantic Intent Classifier

## Objective

Build a semantic intent classifier using sentence-transformer embeddings that understands meaning better than the purely lexical TF-IDF classifier from Phase 7.

## Approach

**Pipeline:**
1. Text preprocessing (lowercase, URL/mention normalization)
2. Sentence-transformer encoding (`all-MiniLM-L6-v2`)
3. Logistic Regression on embeddings

**Why sentence-transformers?**
- Captures semantic meaning, not just word overlap
- Handles paraphrases and synonyms
- Pre-trained on semantic similarity tasks
- Efficient and well-tested

## Model Configuration

```yaml
embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
normalize_embeddings: true
batch_size: 32
classifier: logistic_regression
max_iter: 1000
class_weight: "balanced"
random_state: 42
```

## Development Results

Results will be populated after training on the downloaded dataset.

## Baseline Comparison

| Model | Accuracy | Macro F1 | Weighted F1 |
|-------|----------|----------|-------------|
| Majority baseline | *pending* | *pending* | *pending* |
| TF-IDF + LogReg | *pending* | *pending* | *pending* |
| Semantic + LogReg | *pending* | *pending* | *pending* |

## Test Results

*Pending*

## Golden Results

*Pending*

## Confidence Analysis

*Pending*

## Top Confusion Pairs

*Pending*

## Failure Examples

*Pending*

## What Improved Over TF-IDF?

*Pending*

## What Did Not Improve?

*Pending*

## Limitations

- Requires sentence-transformer model download (internet access)
- Embedding computation is slower than TF-IDF
- Performance depends on embedding model quality
- Not calibrated for probability estimation

## Decision

Semantic classifier is the recommended approach if it outperforms TF-IDF on DEV.
