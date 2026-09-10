# MODEL CARD — Semantic Intent Classifier

## Model

Sentence-transformer embeddings + Logistic Regression for intent classification.

- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Classifier:** Logistic Regression (balanced classes, max_iter=1000)
- **Embedding Dimension:** 384

## Training Data

- **Source:** Customer Support on Twitter dataset
- **Brand:** Selected brand (see project.yaml)
- **Split:** TRAIN (70% of selected-brand messages)
- **Preprocessing:** Lowercase, URL normalization, mention normalization

## Intended Use

Intent classification for the selected brand's customer-support messages on Twitter.

## Not Intended For

- Generating replies to customers
- Deciding refunds or financial actions
- Taking account actions
- Making legal or financial decisions
- Autonomous customer-support actions
- Multi-brand classification (unless separately trained)
- Messages outside the selected brand

## Performance

Results will be populated after training on the downloaded dataset.

## Known Limitations

Based on Phase 8 error analysis (pending):

- May struggle with very short messages (< 3 words)
- May confuse semantically similar intents
- Performance depends on embedding model quality
- Not calibrated for probability estimation

## Citation

If you use this model, cite the sentence-transformers library and the original dataset.
