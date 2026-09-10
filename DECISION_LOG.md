# Decision Log

This log records non-obvious engineering decisions and their rationale.

> **Note:** Decisions are organized by phase. Later phases may add more decisions or revise these.

---

## Phase 1 Decisions

### Decision 1: Evaluation-First Development

**Date:** Phase 1
**Decision:** Build the evaluation harness and golden set before (or alongside) the agent pipeline.

**Rationale:** The assignment emphasizes proving that the system works, not merely producing a demo. By establishing evaluation infrastructure early, we ensure that every subsequent component can be measured immediately upon implementation. This also prevents the common trap of optimizing for vibes rather than metrics.

---

## Decision 2: Use the Twitter Support Dataset as the Primary Source

**Date:** Phase 1
**Decision:** Use the `thoughtvector/customer-support-on-twitter` dataset as the sole data source.

**Rationale:** The assignment explicitly requires this dataset. It contains real customer-support conversations with brand responses, which provides the historical grounding needed for the reply generation component.

---

## Decision 3: Select One Brand Instead of Building a Multi-Brand System

**Date:** Phase 1
**Decision:** Select a single brand from the dataset and build the entire system around it.

**Rationale:** The assignment explicitly asks for one brand. A single-brand system allows deeper specialization: the intent taxonomy is derived from that brand's actual issues, the retrieval corpus is focused, and the escalation logic can account for brand-specific policies. A multi-brand system would dilute the signal and increase complexity without corresponding benefit for this assignment.

---

## Decision 4: Define Intents from the Selected Brand's Actual Data

**Date:** Phase 1
**Decision:** Derive the intent taxonomy by analyzing the selected brand's messages, rather than imposing a pre-defined taxonomy.

**Rationale:** Different brands have different support patterns. An intent taxonomy derived from the actual data will capture the real distribution of customer issues, avoiding wasted effort on intents that never appear and missing intents that frequently appear.

---

## Decision 5: Use Conversation-Level Train/Test Separation

**Date:** Phase 1
**Decision:** Split data at the conversation level, not the message level.

**Rationale:** Messages within the same conversation are highly correlated. A message-level split would leak information from the same conversation into both train and test sets, producing overly optimistic evaluation results. Conversation-level separation gives a more honest estimate of generalization.

---

## Decision 6: Create a Separate Hand-Labelled Golden Set

**Date:** Phase 1
**Decision:** Create a dedicated 150–250 example golden set that is separate from the training data and any automatic labels.

**Rationale:** Automatic labels (e.g., from heuristic rules or weak supervision) are noisy. A small, high-quality hand-labelled set provides a reliable evaluation target. Keeping it separate from training data ensures no contamination.

---

## Decision 7: Include Both Trivial and Simple Baselines

**Date:** Phase 1
**Decision:** Implement two baselines: a trivial baseline (majority class, generic responses) and a simple baseline (TF-IDF + logistic regression, rule-based escalation).

**Rationale:** Without baselines, it is impossible to determine whether the AI system actually improves over simple approaches. The trivial baseline establishes the floor; the simple baseline establishes whether the added complexity of an LLM-based system is justified.

---

## Decision 8: Use Historical Support Resolutions as Evidence

**Date:** Phase 1
**Decision:** Ground reply generation in how the brand historically resolved similar issues, rather than generating replies from scratch.

**Rationale:** This is required by the assignment and is also good engineering practice. Grounding in historical evidence reduces hallucination, ensures brand consistency, and makes the system auditable.

---

## Decision 9: Add an Evidence-Sufficiency Check

**Date:** Phase 1
**Decision:** Include a step that checks whether sufficient historical evidence exists before generating a reply.

**Rationale:** If the retrieval component returns weak or irrelevant evidence, the generation component should not attempt to fabricate a reply. Instead, insufficient evidence should trigger escalation to a human. This is a key safety mechanism that prevents confident but incorrect responses.

---

## Decision 10: Evaluate the LLM Judge Against Human Ratings

**Date:** Phase 1
**Decision:** Measure the agreement between the LLM-as-judge and human evaluation, rather than treating the LLM judge as ground truth.

**Rationale:** LLM judges are convenient but not infallible. They can have systematic biases (e.g., preferring longer responses, being lenient on grounding). Measuring human-LLM agreement tells us how much to trust the automated evaluation and identifies where the judge disagrees with humans.

---

## Decision 11: Prefer Interpretable Components Where Possible

**Date:** Phase 1
**Decision:** Use interpretable models (e.g., logistic regression for baselines) and simple, transparent logic where feasible.

**Rationale:** The assignment requires that I can explain and modify the code during a live interview. A black-box system that I cannot explain will fail the interview even if it performs well on metrics.

---

## Decision 12: Optimize for a Reproducible Subsample

**Date:** Phase 1
**Decision:** Use a subsample of the dataset rather than attempting to process all ~3M tweets locally.

**Rationale:** The assignment explicitly allows and encourages subsampling. Processing the full dataset locally would be slow, expensive, and fragile. A well-chosen subsample that represents the brand's support distribution is sufficient for demonstrating the system.

---

## Decision 13: Avoid Unnecessary Product Features

**Date:** Phase 1
**Decision:** Do not build a frontend, authentication system, or production CRM integration in Phase 1.

**Rationale:** The assignment focuses on demonstrating a trustworthy support-agent pipeline. Building UI or integration features before the evaluation pipeline is validated wastes effort on the wrong problems. These can be added later if time permits and only after the core system is validated.

---

## Decision 14: Configuration Separated from Implementation

**Date:** Phase 1
**Decision:** Use YAML configuration files for all tunable parameters, with sensible placeholders.

**Rationale:** Separating configuration from code makes it easy to change hyperparameters, thresholds, and paths without modifying source code. This also supports reproducibility — the configuration file documents exactly what settings produced a given result.

---

## Decision 15: No Hardcoded API Keys or Secrets

**Date:** Phase 1
**Decision:** All secrets (API keys, etc.) go in `.env` files which are gitignored.

**Rationale:** Hardcoded secrets in a repository are a security risk and would be caught in any code review. Using environment variables is the standard practice and makes the code portable.

---

## Phase 2 Decisions

### Decision 16: Use Conversation-Level Sampling

**Date:** Phase 2
**Decision:** Sample at the conversation level rather than the row level when creating the development subsample.

**Rationale:** The dataset contains multi-turn conversations where messages within the same thread are highly correlated. Random row-level sampling would split conversations, losing the threading context that is essential for intent classification and reply generation. Conversation-level sampling preserves all messages from each sampled conversation, maintaining the natural structure of support interactions.

### Decision 17: Use Deterministic Seed 42

**Date:** Phase 2
**Decision:** Use `random_seed=42` for the development subsample.

**Rationale:** A fixed seed ensures reproducibility — anyone running the same script with the same parameters will get the identical subsample. The value 42 is conventional and easy to remember. This makes it possible to share and compare results across different environments.

### Decision 18: Development Subsample Instead of Full Dataset

**Date:** Phase 2
**Decision:** Create a development subsample of ~25,000 messages rather than attempting to process the full ~3M tweet dataset locally.

**Rationale:** The assignment explicitly allows and encourages subsampling. Processing the full dataset locally would be slow, memory-intensive, and fragile. A well-chosen subsample that preserves conversation structure and brand distribution is sufficient for development and evaluation. The subsample can be increased later if needed.

### Decision 19: Separate Raw and Interim Data

**Date:** Phase 2
**Decision:** Keep raw dataset files in `data/raw/` (gitignored) and derived subsamples in `data/interim/` (commitable).

**Rationale:** Raw data files are large and should not be committed to version control. The interim directory contains small, reproducible derived files (subsample, metadata, statistics) that document the data pipeline without bloating the repository. This separation also prevents accidental modification of original data.

### Decision 20: Support Both API and Manual Download

**Date:** Phase 2
**Decision:** The download script supports both Kaggle API download and manual download with verification.

**Rationale:** Not all environments have Kaggle credentials configured. Supporting manual download with clear instructions and verification makes the project accessible to anyone. The verification step ensures the correct files are in place before proceeding.

### Decision 21: Chunked Reading for Large CSV Files

**Date:** Phase 2
**Decision:** Use chunked pandas reading (`chunksize` parameter) when inspecting or processing the full dataset.

**Rationale:** The main dataset file may contain millions of rows. Loading it entirely into memory could cause out-of-memory errors on machines with limited RAM. Chunked reading allows processing the data in manageable pieces while still computing aggregate statistics.

---

## Phase 3 Decisions

### Decision 22: Perform EDA Before Brand Selection

**Date:** Phase 3
**Decision:** Conduct comprehensive exploratory data analysis before selecting the final brand.

**Rationale:** The assignment requires selecting one brand and building an agent around it. Selecting a brand without understanding the dataset would risk choosing a brand with insufficient data, poor response coverage, or other quality issues. EDA first ensures the selection is informed by actual data characteristics.

### Decision 23: Treat Resolution as Inferred Signal

**Date:** Phase 3
**Decision:** Treat conversation resolution as a heuristic/inferred signal rather than a ground-truth label.

**Rationale:** The dataset does not contain explicit resolution labels. Any resolution metric must be derived from heuristics (thank-you detection, resolution keywords, conversation termination). These heuristics are noisy and should not be confused with actual resolution status. Clearly distinguishing inferred signals from actual labels prevents misleading evaluation later.

### Decision 24: Preserve Noisy Social-Media Text

**Date:** Phase 3
**Decision:** Analyze but do not aggressively clean noisy social-media text during EDA.

**Rationale:** The goal of Phase 3 is to understand the data, not to produce a clean dataset. Removing URLs, mentions, hashtags, or emojis would destroy information that might be useful for intent classification or escalation decisions. Aggressive cleaning should happen only after understanding what is being removed and why.

### Decision 25: Use Conversation-Level Analysis

**Date:** Phase 3
**Decision:** Perform analysis at the conversation level where possible, not just the message level.

**Rationale:** The assignment requires a support agent that handles multi-turn conversations. Message-level analysis alone would miss conversation-level patterns such as thread length, response coverage, and resolution signals. Conversation-level analysis provides the insights needed for later phases.

### Decision 26: Avoid Interpreting Response Time as SLA

**Date:** Phase 3
**Decision:** Report response time statistics as exploratory findings only, not as performance guarantees.

**Rationale:** Historical response times reflect past behavior under specific conditions. They should not be treated as current SLAs or as targets for the AI agent. Presenting them as exploratory findings prevents misinterpretation.

### Decision 27: Separate Dataset Labels from Heuristic Metrics

**Date:** Phase 3
**Decision:** Clearly distinguish between actual data fields and heuristic-derived metrics in all reports and statistics.

**Rationale:** Confusing actual labels with inferred signals would undermine evaluation validity. For example, if we later evaluate "resolution rate," we must be clear whether we are measuring actual resolution (not available) or heuristic resolution signals (noisy). This distinction is critical for honest evaluation.

---

## Phase 4 Decisions

### Decision 28: Select One Brand for Deep Specialization

**Date:** Phase 4
**Decision:** Select a single brand and build the entire system around it, rather than building a multi-brand system.

**Rationale:** The assignment explicitly requires a single-brand support agent. A single-brand system allows deeper specialization: the intent taxonomy is derived from that brand's actual issues, the retrieval corpus is focused on that brand's historical responses, and the escalation logic can account for brand-specific policies. Multi-brand dilution would increase complexity without corresponding benefit.

### Decision 29: Use Data Suitability Instead of Model Performance

**Date:** Phase 4
**Decision:** Select the brand based on data suitability metrics (conversation volume, multi-turn coverage, response coverage) rather than model performance.

**Rationale:** Using model performance would create circular selection — we would be choosing the brand that works best with a model that hasn't been built yet. Data suitability metrics are available before any model development and provide an objective, reproducible basis for selection.

### Decision 30: Use Weighted Brand Scoring

**Date:** Phase 4
**Decision:** Use a transparent weighted scoring methodology for brand selection.

**Rationale:** A weighted score makes the selection reproducible and defensible. The weights are documented and can be adjusted if needed. This is more principled than ad-hoc selection or picking the brand with the most tweets.

### Decision 31: Prioritize Multi-turn Conversations

**Date:** Phase 4
**Decision:** Give significant weight (0.20) to multi-turn conversation coverage in brand selection.

**Rationale:** The assignment requires a support agent that handles multi-turn conversations. Brands with mostly single-message conversations would not provide the threading context needed for intent classification and historically grounded reply generation. Multi-turn conversations are essential for the retrieval and generation components.

### Decision 32: Preserve Conversation Boundaries

**Date:** Phase 4
**Decision:** Preserve conversation boundaries when extracting selected-brand data.

**Rationale:** Conversation boundaries are required for later train/test separation (to prevent leakage) and for historical context retrieval. Splitting conversations would break the threading that the agent depends on.

### Decision 33: Explicitly Document Excluded Functionality

**Date:** Phase 4
**Decision:** Explicitly document what the agent will NOT do (refunds, account changes, Twitter API, etc.).

**Rationale:** The assignment focuses on demonstrating a trustworthy support-agent pipeline. Documenting exclusions keeps scope aligned with the assignment and prevents scope creep during implementation.

---

## Phase 5 Decisions

### Decision 34: Define Intents from Selected-Brand Data

**Date:** Phase 5
**Decision:** Derive the intent taxonomy from the selected brand's actual customer messages, rather than using an external or pre-defined taxonomy.

**Rationale:** Different brands have different support patterns. An intent taxonomy derived from the actual data will capture the real distribution of customer issues specific to this brand, avoiding wasted effort on intents that never appear and missing intents that frequently appear.

### Decision 35: Use Clustering as Discovery Tool

**Date:** Phase 5
**Decision:** Use TF-IDF + KMeans clustering as a discovery aid for identifying recurring themes, not as ground truth for the final taxonomy.

**Rationale:** Clustering reveals natural groupings in the data, but clusters do not directly map to intents. The final taxonomy must be manually designed based on semantic understanding of customer support patterns. Clustering is a tool for exploration, not a source of labels.

### Decision 36: Target a Small Taxonomy

**Date:** Phase 5
**Decision:** Target approximately 8-15 intents for the taxonomy.

**Rationale:** The assignment requires a "small set of intents." A small taxonomy is easier to label consistently, easier to classify accurately, and more practical for a support agent. Too few intents would be too coarse; too many would be hard to distinguish.

### Decision 37: Preserve Original Customer Text

**Date:** Phase 5
**Decision:** Preserve the original customer text without aggressive cleaning during intent discovery.

**Rationale:** Aggressive cleaning (removing emojis, punctuation, slang) would destroy information that might be relevant for intent classification. Normalization is applied for analysis, but the original text is preserved for labeling and later use.

### Decision 38: Create Explicit Inclusion/Exclusion Rules

**Date:** Phase 5
**Decision:** Define explicit inclusion and exclusion criteria for each intent.

**Rationale:** Without clear boundaries, annotators will disagree on edge cases. Explicit rules ensure consistent labeling across annotators and make the taxonomy defensible during evaluation.

### Decision 39: Establish Primary-Intent Policy

**Date:** Phase 5
**Decision:** Label each message with exactly one primary intent, selecting the root cause or blocking issue.

**Rationale:** Single-label classification is simpler and more practical than multi-label. Selecting the root cause ensures the agent addresses the most important issue first. Multi-intent handling can be added later if needed.

### Decision 40: Version the Taxonomy

**Date:** Phase 5
**Decision:** Use semantic versioning (1.0, 1.1, 2.0) for the intent taxonomy.

**Rationale:** Versioning allows tracking changes to the taxonomy over time. If intents are added, merged, or split, the version number documents the change and prevents confusion about which taxonomy was used for which experiments.

---

## Phase 6 Decisions

### Decision 41: Target 200 Golden Examples

**Date:** Phase 6
**Decision:** Target 200 examples for the golden evaluation set, within the assignment's 150-250 range.

**Rationale:** 200 examples provides enough data for meaningful evaluation while remaining manageable for hand-labeling. It allows approximately 20 examples per intent (with 10 intents), providing sufficient coverage for each category.

### Decision 42: Use Stratified Sampling

**Date:** Phase 6
**Decision:** Use stratified sampling rather than purely random sampling for the golden set.

**Rationale:** Purely random sampling might over-represent common intents and under-represent rare ones. Stratified sampling ensures representation across different message types (representative, short, difficult, noisy) and intent categories.

### Decision 43: Include Difficult and Confusable Examples

**Date:** Phase 6
**Decision:** Deliberately include difficult examples (short, noisy, ambiguous) and confusable-intent examples in the golden set.

**Rationale:** A realistic evaluation set should include challenging cases, not just easy ones. Including difficult examples ensures the evaluation measures real-world performance, not just performance on clean data.

### Decision 44: Human Labels as Ground Truth

**Date:** Phase 6
**Decision:** Use human annotation as the gold standard for labels, not LLM-generated labels.

**Rationale:** The assignment explicitly requires hand-labelled examples. Human labels capture nuanced understanding that LLMs may miss. If LLM assistance is used during annotation, it must be documented and the human label takes precedence.

### Decision 45: Keep Golden Set Separate from Training Data

**Date:** Phase 6
**Decision:** Maintain strict separation between golden set and training/development data at the conversation level.

**Rationale:** Data leakage would produce overly optimistic evaluation results. Conversation-level separation ensures no information from the golden set leaks into training, providing an honest estimate of generalization.

### Decision 46: Conversation-Level Leakage Checks

**Date:** Phase 6
**Decision:** Check for data leakage at the conversation level, not just message level.

**Rationale:** Messages within the same conversation are highly correlated. Even if individual messages don't overlap, having the same conversation in both training and golden set would cause leakage through contextual similarity.

### Decision 47: Add Explicit Annotation Confidence

**Date:** Phase 6
**Decision:** Collect annotation confidence (HIGH/MEDIUM/LOW) for each golden example.

**Rationale:** Confidence levels allow downstream analysis to distinguish between clear-cut cases and borderline cases. This enables more nuanced evaluation and helps identify areas where the taxonomy may need refinement.

### Decision 48: Lock the Golden Set After Review

**Date:** Phase 6
**Decision:** Lock the golden set after annotation and review, preventing silent modifications.

**Rationale:** The golden set is the evaluation standard. Silently changing labels based on model performance would invalidate evaluation results. If genuine errors are discovered, they must be documented and versioned.

---

## Phase 7 Decisions

### Decision 49: Use Majority-Class Classifier as Trivial Baseline

**Date:** Phase 7
**Decision:** Implement a majority-class classifier as the trivial baseline.

**Rationale:** The majority-class classifier establishes the lowest possible bar. Any useful model must exceed this baseline. It also reveals the class imbalance in the dataset.

### Decision 50: Use TF-IDF + Logistic Regression as Simple Baseline

**Date:** Phase 7
**Decision:** Implement TF-IDF vectorization + Logistic Regression as the simple baseline.

**Rationale:** TF-IDF + Logistic Regression is a well-understood, fast, and competitive text classification baseline. It requires no embeddings or LLMs, making it a fair comparison point for more complex systems.

### Decision 51: Use Conversation-Level Splitting

**Date:** Phase 7
**Decision:** Split data by conversation, not by individual message.

**Rationale:** Messages within the same conversation share context. Splitting messages from the same conversation across train/dev would cause leakage through contextual similarity.

### Decision 52: Use Macro F1 as Candidate Headline Metric

**Date:** Phase 7
**Decision:** Use macro F1 as the candidate headline metric for intent classification.

**Rationale:** Macro F1 gives each intent equal weight, which is important when classes are imbalanced. A model can achieve high accuracy while performing poorly on rare intents. Final reporting will consider the full evaluation suite.

### Decision 53: Use DEV for Development Decisions

**Date:** Phase 7
**Decision:** Use the DEV split for all development decisions, including hyperparameter selection and error analysis.

**Rationale:** The DEV split provides a reliable signal for development without contaminating the golden evaluation set. Using golden for development would invalidate evaluation results.

### Decision 54: Keep GOLDEN Strictly Evaluation-Only

**Date:** Phase 7
**Decision:** Golden set is used ONLY for final evaluation reporting, never for tuning or model selection.

**Rationale:** The golden set is the locked evaluation standard. Using it for any development purpose would produce overly optimistic results.

### Decision 55: Use Fixed Random Seed

**Date:** Phase 7
**Decision:** Use random_state=42 for all splits and model training.

**Rationale:** Fixed seeds ensure reproducibility. All baseline results can be regenerated from scratch with the same outputs.

### Decision 56: Use Class Balancing in Logistic Regression

**Date:** Phase 7
**Decision:** Use class_weight="balanced" in Logistic Regression.

**Rationale:** The dataset likely has class imbalance. Balanced class weights help the model avoid biasing toward majority classes.

### Decision 57: Avoid Large Hyperparameter Search

**Date:** Phase 7
**Decision:** Use reasonable default hyperparameters without extensive tuning.

**Rationale:** These are baselines, not optimized models. Extensive tuning would defeat the purpose of establishing a comparison point. Tuning belongs to the next phase.

---

## Phase 8 Decisions

### Decision 58: Introduce Sentence-Transformer Embeddings

**Date:** Phase 8
**Decision:** Use sentence-transformer embeddings instead of TF-IDF for the stronger intent classifier.

**Rationale:** TF-IDF captures lexical overlap but misses semantic similarity. Sentence-transformers encode meaning, allowing the model to understand paraphrases, synonyms, and semantic equivalence. This is essential for a production-quality intent classifier.

### Decision 59: Use all-MiniLM-L6-v2 as Default Embedding Model

**Date:** Phase 8
**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2` as the default embedding model.

**Trade-off:** This model offers a good balance between quality (384 dimensions, trained on semantic similarity) and efficiency (runs on CPU, fast inference). Larger models may offer marginal quality improvements but at higher computational cost.

### Decision 60: Use Logistic Regression on Embeddings

**Date:** Phase 8
**Decision:** Use Logistic Regression as the classifier on top of embeddings.

**Rationale:** Logistic Regression is simple, fast, interpretable, and competitive for text classification. More complex classifiers (SVM, neural networks) would add complexity without guaranteed improvement for this task size.

### Decision 61: Limit Configuration Comparison

**Date:** Phase 8
**Decision:** Compare only a small number of reasonable configurations (2-3 models).

**Rationale:** This is a take-home assignment, not a Kaggle competition. Extensive hyperparameter search would be time-consuming and unlikely to produce meaningful improvements. The goal is a reliable, explainable system.

### Decision 62: Use DEV for Model Selection

**Date:** Phase 8
**Decision:** Use the DEV split for all model selection decisions.

**Rationale:** DEV provides a reliable signal for comparing configurations without contaminating the golden evaluation set. Using golden for model selection would produce overly optimistic results.

### Decision 63: Keep TEST Untouched Until Model Freeze

**Date:** Phase 8
**Decision:** TEST is used only for final non-golden evaluation after model selection is complete.

**Rationale:** Repeated evaluation on TEST would lead to implicit tuning. Keeping TEST frozen until the end provides an unbiased internal evaluation.

### Decision 64: Keep GOLDEN Strictly Locked

**Date:** Phase 8
**Decision:** Golden set is used ONLY for final evaluation reporting, never for tuning or model selection.

**Rationale:** The golden set is the locked evaluation standard. Using it for any development purpose would invalidate evaluation results.

### Decision 65: Treat Confidence as Model Score

**Date:** Phase 8
**Decision:** Treat classifier probabilities as model scores, not calibrated probabilities.

**Rationale:** Logistic Regression probabilities are not automatically calibrated. A 90% confidence does not mean 90% chance of being correct. Calibration analysis is deferred to a later phase.

### Decision 66: Implement Embedding Caching

**Date:** Phase 8
**Decision:** Cache embeddings to avoid redundant computation.

**Rationale:** Sentence-transformer encoding is computationally expensive. Caching ensures that embeddings are computed once and reused across experiments. The cache is invalidated if the dataset, preprocessing, or embedding model changes.

### Decision 67: Preserve Social-Media Language

**Date:** Phase 8
**Decision:** Avoid aggressive text cleaning. Preserve punctuation, emojis, product names, and conversational wording.

**Rationale:** Social-media language contains useful signals for intent classification. Removing emojis, slang, or punctuation could remove discriminative features. The same preprocessing as Phase 7 is used for consistency.

---

## Phase 9 Decisions

### Decision 68: Use Historical Conversations as Knowledge Source

**Date:** Phase 9
**Decision:** Use the selected brand's historical Twitter conversations as the knowledge source.

**Rationale:** The dataset contains real customer-support interactions. These provide grounded evidence of how the brand historically handled similar issues. This is more reliable than synthetic or LLM-generated examples.

### Decision 69: Treat Support Responses as Evidence, Not Policy

**Date:** Phase 9
**Decision:** Historical support responses are treated as evidence, not guaranteed business policies.

**Rationale:** Historical responses may contain incorrect advice, outdated policies, inconsistent support, or incomplete resolutions. Treating them as policy would be misleading.

### Decision 70: Use Author-Based Message Pairing

**Date:** Phase 9
**Decision:** Pair customer messages with support responses using author/sender information where available.

**Rationale:** Author information provides the most reliable way to identify who sent each message. Without it, alternating patterns or other heuristics are used as fallback.

### Decision 71: Preserve Multi-Turn Conversation Structure

**Date:** Phase 9
**Decision:** Preserve multi-turn conversation structure rather than flattening to single pairs.

**Rationale:** Support responses depend on conversation context. Preserving the structure ensures that future retrieval can access the full context.

### Decision 72: Use Historical Action Categories for Resolution

**Date:** Phase 9
**Decision:** Resolution types are historical response categories, not business policy labels.

**Rationale:** These categories describe what the support agent did, not what the company policy is. This avoids misleading inferences.

### Decision 73: Retain Unresolved/Unclear Conversations

**Date:** Phase 9
**Decision:** Unresolved and unclear conversations are retained instead of being artificially labeled as resolved.

**Rationale:** Artificially labeling conversations as resolved would be misleading. The knowledge base should honestly represent what is visible in the data.

### Decision 74: Flag Rather Than Delete Noisy Records

**Date:** Phase 9
**Decision:** Noisy records are flagged with quality indicators rather than aggressively deleted.

**Rationale:** Even noisy records may contain useful evidence. Flagging allows the retrieval layer to filter as needed while preserving provenance.

### Decision 75: Store Intent Predictions with Provenance

**Date:** Phase 9
**Decision:** Semantic classifier predictions are stored with explicit `intent_source` field.

**Rationale:** Model predictions are not ground truth. Recording provenance prevents confusion between predicted and actual intent labels.

### Decision 76: Exclude Golden Conversations

**Date:** Phase 9
**Decision:** Golden set conversations are excluded from the knowledge base.

**Rationale:** The golden set is the evaluation standard. Including golden conversations in the knowledge base would cause retrieval leakage, producing overly optimistic results.

### Decision 77: Defer Vector Index to Next Phase

**Date:** Phase 9
**Decision:** The vector index/RAG system is not implemented in this phase.

**Rationale:** Phase 9 focuses on creating a clean, auditable corpus. The vector index requires embedding generation and semantic search, which belong to the retrieval phase.

---

## Phase 10 Decisions

### Decision 78: Use Semantic Embeddings for Retrieval

**Date:** Phase 10
**Decision:** Use sentence-transformer embeddings for semantic retrieval.

**Rationale:** Semantic embeddings capture meaning, not just word overlap. This allows retrieving historically similar support interactions even when the wording differs.

### Decision 79: Reuse Phase 8 Embedding Model

**Date:** Phase 10
**Decision:** Use the same `all-MiniLM-L6-v2` embedding model from Phase 8.

**Rationale:** Reusing the model simplifies the architecture and reduces unnecessary model diversity. The model is already proven effective for this domain.

### Decision 80: Use FAISS for Vector Index

**Date:** Phase 10
**Decision:** Use FAISS (IndexFlatIP) for vector indexing and search.

**Rationale:** FAISS is efficient, well-tested, and appropriate for the selected-brand corpus size. IndexFlatIP with normalized embeddings provides exact cosine similarity search.

### Decision 81: Use Normalized Embeddings + Inner Product

**Date:** Phase 10
**Decision:** Use L2-normalized embeddings with inner product for cosine similarity.

**Rationale:** When embeddings are normalized, inner product equals cosine similarity. This is more efficient than computing full cosine similarity.

### Decision 82: Implement TF-IDF Baseline

**Date:** Phase 10
**Decision:** Implement TF-IDF retrieval as a baseline for comparison.

**Rationale:** A lexical baseline provides an important comparison point. Do not assume semantic retrieval is better without measurement.

### Decision 83: Evaluate Retrieval Separately

**Date:** Phase 10
**Decision:** Evaluate retrieval independently from intent classification.

**Rationale:** Retrieval and classification are different tasks with different metrics. Separate evaluation provides clearer signals about each component's performance.

### Decision 84: Make Intent-Aware Reranking Optional

**Date:** Phase 10
**Decision:** Intent-aware reranking is optional and disabled by default.

**Rationale:** Low-confidence intent predictions should not eliminate candidates. Semantic retrieval first, then optional intent reranking, reduces the risk of incorrect predictions destroying recall.

### Decision 85: Don't Let Low-Confidence Intent Eliminate Candidates

**Date:** Phase 10
**Decision:** Low-confidence intent predictions do not completely filter candidates.

**Rationale:** Intent predictions are not ground truth. Aggressive filtering based on uncertain predictions would reduce retrieval recall.

### Decision 86: Exclude Golden Examples from Index

**Date:** Phase 10
**Decision:** Golden set conversations are excluded from the retrieval index.

**Rationale:** The golden set is the evaluation standard. Including golden conversations would cause retrieval leakage, producing overly optimistic results.

### Decision 87: Similarity Score is Not Relevance

**Date:** Phase 10
**Decision:** Treat similarity score as a model score, not a guarantee of relevance.

**Rationale:** High semantic similarity does not guarantee that a historical example is relevant for the current query. Similarity is one signal among many.

### Decision 88: Support Insufficient-Evidence Results

**Date:** Phase 10
**Decision:** The system supports returning no results when evidence is insufficient.

**Rationale:** Forcing the system to return a historical example when none is relevant would produce poor downstream replies. Supporting empty results enables proper escalation.

### Decision 89: Historical Responses Are Evidence, Not Policy

**Date:** Phase 10
**Decision:** Retrieved historical responses are treated as evidence, not official policy.

**Rationale:** Historical responses may contain incorrect advice, outdated policies, or inconsistent support. Treating them as policy would be misleading.
