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

---

## Phase 11 Decisions

### Decision 90: Create Generic Reply Baseline

**Date:** Phase 11
**Decision:** Implement a generic reply baseline that returns a fixed support response.

**Rationale:** Establishes a floor for reply quality. Without this baseline, we cannot measure whether retrieval or generation adds value beyond a canned response.

**Trade-off:** Generic responses are always available but never specific to the customer's issue.

**Consequence:** The comparison between generic and historical baselines reveals how much value retrieval actually adds.

### Decision 91: Use Direct Historical Response as Second Baseline

**Date:** Phase 11
**Decision:** Return the top-ranked historical support response verbatim as the candidate reply.

**Rationale:** This is the simplest retrieval-based approach. It directly answers: "Is retrieving a similar historical response good enough?" If the LLM cannot beat this, the additional complexity is not justified.

**Trade-off:** Copying verbatim preserves errors, outdated content, and customer-specific data from the source.

**Consequence:** Safety/risk analysis becomes necessary to flag problematic copied content.

### Decision 92: Historical Responses Are Not Ground-Truth Answers

**Date:** Phase 11
**Decision:** Do not treat historical support responses as ground-truth correct answers for evaluation.

**Rationale:** Customer-support responses are context-dependent. A response that was appropriate in the original conversation may be wrong for a different customer with a similar query. There is no single correct reply.

**Trade-off:** This limits which automated metrics can be used (no exact-match, limited BLEU/ROUGE utility).

**Consequence:** Evaluation relies on coverage, evidence quality, intent consistency, and safety metrics rather than reply correctness.

### Decision 93: Exact-Match Metrics Are Insufficient for Reply Quality

**Date:** Phase 11
**Decision:** Do not use BLEU, ROUGE, or exact string matching as primary reply quality metrics.

**Rationale:** Multiple valid responses exist for any customer message. Measuring overlap with a single reference reply would be misleading. These metrics can be reported as supplementary diagnostics only.

**Trade-off:** Objective automated metrics are limited; more weight falls on manual audit and proxy metrics.

**Consequence:** Reply quality evaluation focuses on response coverage, evidence availability, similarity distribution, and safety risk rate.

### Decision 94: Preserve Evidence with Every Reply

**Date:** Phase 11
**Decision:** Every generated reply includes the full evidence chain (knowledge_id, similarity_score, support_response, intent, resolution_type).

**Rationale:** Evidence preservation enables downstream auditing, explaining why a reply was generated, and debugging failures. It also supports the future escalation system's evidence sufficiency check.

**Trade-off:** Slightly larger output schema.

**Consequence:** Every reply can be traced back to its source, supporting transparency and debugging.

### Decision 95: Copying Historical Responses Requires Safety Analysis

**Date:** Phase 11
**Decision:** All historical baseline replies pass through safety/risk detection before being returned.

**Rationale:** Verbatim copying from historical responses risks leaking customer-specific data (order IDs, emails, phone numbers), outdated URLs, and names. Detection is necessary to quantify this risk.

**Trade-off:** Detection adds processing overhead and is not complete PII protection.

**Consequence:** Risk flags are attached to every reply, enabling informed decisions about deployment safety.

### Decision 96: PII Detection Is a Risk Identifier, Not Protection

**Date:** Phase 11
**Decision:** Safety filters detect potentially risky content but do not claim to provide complete PII protection.

**Rationale:** No regex-based system can guarantee complete PII detection. The purpose is to identify why blindly copying historical responses is unsafe, not to make copied responses safe.

**Trade-off:** Some PII may slip through detection.

**Consequence:** The safety analysis quantifies risk exposure; it does not eliminate it.

### Decision 97: No Arbitrary Similarity Threshold

**Date:** Phase 11
**Decision:** Do not introduce a fixed similarity threshold (e.g., >= 0.80) for the baseline.

**Rationale:** Phase 10 similarity analysis has not yet established a defensible threshold. Introducing one without data would be arbitrary.

**Trade-off:** Some low-quality retrievals may be returned as replies.

**Consequence:** The "insufficient_evidence" status remains a future policy decision based on actual similarity distribution analysis.

### Decision 98: Golden Set Is Not Used for Tuning

**Date:** Phase 11
**Decision:** The golden evaluation set is not used for tuning reply generation parameters.

**Rationale:** Tuning on the golden set would produce overly optimistic results. The baseline must be frozen before any golden evaluation.

**Trade-off:** DEV-only evaluation may not perfectly predict golden set performance.

**Consequence:** If golden evaluation is performed, it happens once on a frozen baseline, and results are recorded without further modification.

### Decision 99: Defer LLM Generation to Phase 12

**Date:** Phase 11
**Decision:** No LLM calls, prompt engineering, or generative model usage in Phase 11.

**Rationale:** The purpose of Phase 11 is to establish what non-generative retrieval can achieve. Introducing an LLM now would conflate the baseline with the advanced system.

**Trade-off:** The baseline cannot generate novel responses or adapt to context.

**Consequence:** Phase 12 can directly compare LLM generation against this baseline to prove whether the LLM adds value.

---

## Phase 12 Decisions

### Decision 100: LLM Introduced Only After Baselines Exist

**Date:** Phase 12
**Decision:** The LLM generator is introduced only after generic and historical baselines are established and evaluated.

**Rationale:** Without baselines, we cannot measure whether the LLM adds value. The baselines provide the comparison point that proves whether the additional complexity of an LLM is justified.

**Trade-off:** The baselines must be completed before LLM work begins, which adds a phase.

**Consequence:** The final report can directly answer "Does the LLM actually improve reply quality beyond simply returning the most similar historical response?"

### Decision 101: Historical Evidence Separated from Instructions

**Date:** Phase 12
**Decision:** The prompt explicitly separates system instructions from historical evidence content.

**Rationale:** Mixing instructions with data creates ambiguity about what the model should follow. Clear separation ensures the model understands which text is instruction and which is reference data.

**Trade-off:** Slightly longer prompts.

**Consequence:** The model has a clear mental model: system prompt = rules, evidence = data to analyze.

### Decision 102: Historical Messages Treated as Untrusted Data

**Date:** Phase 12
**Decision:** All historical messages (customer and support) are treated as untrusted reference data, not instructions.

**Rationale:** Historical Twitter messages may contain adversarial content, including prompt injection attempts. Treating them as data prevents the model from following embedded instructions.

**Trade-off:** The model cannot extract implicit instructions from historical context.

**Consequence:** The prompt explicitly states that historical messages are data to analyze, not instructions to follow.

### Decision 103: LLM Forbidden from Inventing Unsupported Policies

**Date:** Phase 12
**Decision:** The LLM must not invent business facts, policies, timelines, or guarantees not present in the evidence.

**Rationale:** Customer-support responses must be grounded in what the brand actually does. Inventing policies creates legal and customer-experience risks.

**Trade-off:** The model may sometimes say "insufficient evidence" when a human agent would infer a reasonable response.

**Consequence:** The system is conservative but trustworthy. It will escalate rather than guess.

### Decision 104: Insufficient Evidence Produces No Generated Reply

**Date:** Phase 12
**Decision:** When evidence is insufficient, the generator returns `status: insufficient_evidence` with `reply: null`.

**Rationale:** Forcing a reply when evidence is weak leads to hallucination. Returning null allows the escalation system (Phase 13) to handle these cases appropriately.

**Trade-off:** Some queries that could have a reasonable response will be escalated.

**Consequence:** The escalation system receives clear signals about when to hand off to a human.

### Decision 105: Evidence IDs Validated Against Actual Evidence

**Date:** Phase 12
**Decision:** The output validator checks that any evidence IDs mentioned in the LLM output correspond to actual evidence supplied to the model.

**Rationale:** LLMs may hallucinate evidence references. Validating IDs prevents downstream systems from tracing replies to non-existent evidence.

**Trade-off:** Adds a validation step.

**Consequence:** Every cited evidence ID can be traced back to a real knowledge record.

### Decision 106: Prompt Versioning Required

**Date:** Phase 12
**Decision:** Every prompt version is tracked and stored with evaluation results.

**Rationale:** Prompt changes can significantly affect output quality. Versioning ensures reproducibility and prevents silent regressions.

**Trade-off:** Requires maintaining version metadata.

**Consequence:** Evaluation results are tied to specific prompt versions, enabling A/B comparison.

### Decision 107: Mock LLM Provider for Testing

**Date:** Phase 12
**Decision:** A mock LLM provider is implemented for unit tests, CI, and offline development.

**Rationale:** Tests must run without API keys. The mock provider enables the entire pipeline to be tested deterministically.

**Trade-off:** Mock responses do not test actual LLM behavior.

**Consequence:** The pipeline architecture is validated without API costs. Real LLM behavior is tested separately with the OpenAI provider.

### Decision 108: Historical Customer-Specific Info Must Not Transfer

**Date:** Phase 12
**Decision:** The generator must not copy historical customer-specific information (order IDs, names, emails) into the current reply unless the current customer supplied the same information.

**Rationale:** Copying another customer's order ID into a reply to a different customer is a serious privacy and correctness violation.

**Trade-off:** The model must carefully distinguish between "evidence shows this pattern" and "this specific detail applies to the current customer."

**Consequence:** Grounding checks detect historical PII leakage.

### Decision 109: Output Validation Is Not a Complete Hallucination Detector

**Date:** Phase 12
**Decision:** Output validation catches obvious issues (length, internal terms, empty output) but does not claim to detect all hallucinations.

**Rationale:** No automated system can guarantee complete hallucination detection. Validation is a safety net, not a guarantee.

**Trade-off:** Some subtle hallucinations may pass validation.

**Consequence:** Grounding checks and manual audit supplement automated validation.

### Decision 110: LLM Evaluated Against Generic and Historical Baselines

**Date:** Phase 12
**Decision:** The grounded LLM is evaluated on the same queries as the generic and historical baselines.

**Rationale:** Direct comparison on the same data reveals whether the LLM provides measurably better replies.

**Trade-off:** The baselines may perform differently on different data distributions.

**Consequence:** The evaluation report provides a clear three-way comparison.

### Decision 111: Full LLM-as-Judge Deferred

**Date:** Phase 12
**Decision:** The judge schema is defined but LLM-as-judge evaluation is not performed in Phase 12.

**Rationale:** Building the judge framework requires additional infrastructure (prompt design, calibration, human agreement measurement). Deferring it keeps Phase 12 focused on the generator.

**Trade-off:** Reply quality evaluation relies on automated grounding checks and manual audit rather than LLM-as-judge scores.

**Consequence:** Phase 19 can build on the judge schema defined here.

---

## Phase 13 Decisions

### Decision 112: Multi-Layer Grounding Verification

**Date:** Phase 13
**Decision:** Implement a multi-layer grounding verification pipeline with deterministic checks (claim extraction, evidence support, numeric claims, URLs, PII) combined with optional semantic grounding via embeddings.

**Rationale:** Single-method hallucination detection is insufficient. Deterministic checks catch concrete violations (unsupported numbers, leaked IDs, bogus URLs) while semantic checks catch subtler content drift. Combining both provides defense-in-depth.

**Trade-off:** More components to maintain; semantic checks add compute cost.

**Consequence:** Each reply is checked by 5+ independent verifiers before acceptance.

### Decision 113: Claim Extraction via Sentence/Clause Splitting

**Date:** Phase 13
**Decision:** Extract candidate claims using sentence splitting (`.!?\\n`) and clause splitting (`,;`) rather than NER or dependency parsing.

**Rationale:** NLP parsers add heavy dependencies and are fragile on noisy social-media text. Sentence/clause splitting is fast, dependency-free, and sufficient for grounding verification where false negatives are acceptable.

**Trade-off:** May miss complex multi-clause claims.

**Consequence:** Claim extraction works without any NLP model download.

### Decision 114: Fact-Type Priority Ordering

**Date:** Phase 13
**Decision:** Classify fact types with explicit priority: GUARANTEE > POLICY > PRICE > IDENTIFIER > INSTRUCTION > CONTACT_METHOD > TIMELINE > others.

**Rationale:** A claim like "Please DM us your order number" is both an instruction and a contact method. "We guarantee a response within 24 hours" contains both a guarantee and a timeline. Priority ordering ensures the most actionable/risky classification wins.

**Trade-off:** Some claims may be misclassified if they straddle categories.

**Consequence:** High-risk types (GUARANTEE, PRICE, TIMELINE) are checked first, reducing false negatives on safety-critical claims.

### Decision 115: Hybrid Grounding Verdict Policy

**Date:** Phase 13
**Decision:** Use a priority-ordered verdict policy: (1) no evidence → insufficient_evidence, (2) unsupported high-risk claim → fail, (3) unsupported URL → fail, (4) PII leakage → fail, (5) multiple unsupported claims → fail, (6) one unsupported claim → review, (7) low semantic score → review, (8) otherwise → pass.

**Rationale:** Different failure modes have different severity. A leaked order ID is worse than a slightly off-topic sentence. The policy encodes domain knowledge about which grounding failures are acceptable vs. dangerous.

**Trade-off:** Hard-coded thresholds may not suit all use cases.

**Consequence:** The verdict is deterministic and explainable in an interview setting.

### Decision 116: Claim Support Uses Multi-Signal Heuristic

**Date:** Phase 13
**Decision:** Check claim support using a cascade: exact match → customer message match → partial token overlap → entity inference. Each level has decreasing confidence.

**Rationale:** Exact string matching is too brittle for natural-language claims. A multi-signal approach catches paraphrases and reformulations while still flagging genuinely unsupported claims.

**Trade-off:** Token-overlap heuristics can produce false positives on common phrases.

**Consequence:** Support confidence decreases as the match becomes less direct, providing a calibrated signal.

### Decision 117: Reply Repair as Second LLM Call

**Date:** Phase 13
**Decision:** When grounding verification fails, attempt a single repair call that instructs the LLM to remove unsupported claims while preserving supported content.

**Rationale:** Rather than immediately escalating to a human, a targeted repair prompt gives the LLM a chance to self-correct. This is cheaper and faster than human escalation for fixable issues.

**Trade-off:** The repair call adds latency and cost; repeated repairs could indicate systemic evidence quality issues.

**Consequence:** The pipeline includes a `grounded_llm_repair` generation method alongside `grounded_llm`.

### Decision 118: Semantic Grounding Uses Token Overlap Fallback

**Date:** Phase 13
**Decision:** When no sentence-transformer embedder is available, semantic grounding falls back to token overlap between reply and evidence.

**Rationale:** Embedding computation requires model download and GPU. Token overlap is a zero-dependency approximation that works well enough for development and testing.

**Trade-off:** Token overlap is less semantically meaningful than embeddings.

**Consequence:** The grounding pipeline works in environments without sentence-transformers installed.

### Decision 119: Grounding Metrics Report Pass/Review/Fail Rates

**Date:** Phase 13
**Decision:** Report grounding metrics as pass_rate, review_rate, fail_rate, repair_rate, and repair_success_rate rather than a single accuracy number.

**Rationale:** A single accuracy number hides the distribution of failure modes. Reporting separate rates for each verdict category makes failure analysis actionable.

**Trade-off:** More metrics to interpret.

**Consequence:** The evaluation report clearly shows where the pipeline is strong (pass rate) and where it needs improvement (review/fail rates).

### Decision 120: URL Checker Strips Trailing Punctuation

**Date:** Phase 13
**Decision:** URL extraction regex excludes trailing punctuation (`.`, `,`, `;`, `!`, `?)` to prevent false mismatches between reply URLs and evidence URLs.

**Rationale:** A reply containing "Visit https://example.com/help." should match evidence containing "https://example.com/help" without the period causing a mismatch.

**Trade-off:** Very exotic URL formats may be incorrectly truncated.

**Consequence:** URL support checking works correctly for standard web URLs in natural-language text.

---

## Phase 14 Decisions

### Decision 121: Human Evaluation Is Necessary for Reply Quality

**Date:** Phase 14
**Decision:** Reply quality is evaluated primarily through human scoring, not automated metrics.

**Rationale:** Customer support has many valid responses. Automated metrics like BLEU or ROUGE cannot distinguish between a helpful reply and a technically similar but unhelpful one. Human judgment is required to assess relevance, helpfulness, and appropriateness.

**Trade-off:** Human evaluation is slower and more expensive than automated metrics.

**Consequence:** The evaluation framework requires human annotators but produces trustworthy quality signals.

### Decision 122: Reply Quality Is Multidimensional

**Date:** Phase 14
**Decision:** Evaluate replies on six independent dimensions: relevance, groundedness, correctness, helpfulness, completeness, and style.

**Rationale:** A reply can be relevant but unhelpful, grounded but incomplete, or correct but poorly styled. Single-number evaluations collapse important distinctions. Reporting all six dimensions preserves diagnostic information.

**Trade-off:** More dimensions mean more annotation time per query.

**Consequence:** Failure analysis can identify specific weaknesses per system (e.g., "System A is grounded but unhelpful").

### Decision 123: Exact-Match Metrics Are Not Primary

**Date:** Phase 14
**Decision:** BLEU, ROUGE, and exact-match accuracy are supplementary diagnostics, not primary reply-quality scores.

**Rationale:** "Please DM us your order number" and "Send us your order details via DM" are equally valid but have low lexical overlap. Customer support correctness is semantic, not lexical.

**Trade-off:** Excluding lexical metrics may miss some surface-level issues.

**Consequence:** The evaluation focuses on what matters to customers, not what is easy to compute.

### Decision 124: Blind Evaluation Prevents Evaluator Bias

**Date:** Phase 14
**Decision:** Human evaluators see anonymized system labels (System A/B/C/D) without model names, provider info, or generation method.

**Rationale:** Knowing that "System C is the grounded LLM" could bias evaluators toward higher scores. Blind evaluation ensures scores reflect reply quality, not expectations.

**Trade-off:** Evaluators cannot provide system-specific feedback during scoring.

**Consequence:** Scores are more trustworthy but feedback must be collected separately.

### Decision 125: Reply Order Is Randomized Per Query

**Date:** Phase 14
**Decision:** For each query, the order of replies (System A/B/C/D) is randomly assigned using a deterministic seed.

**Rationale:** Presenting replies in a fixed order (e.g., always Generic first) could create position bias. Randomization with a fixed seed ensures reproducibility.

**Trade-off:** Annotators must track which reply is which across dimensions.

**Consequence:** Position effects are eliminated while maintaining reproducibility.

### Decision 126: Same Queries for All Systems

**Date:** Phase 14
**Decision:** Every system is evaluated on the exact same set of queries.

**Rationale:** Comparing System A on query set X and System B on query set Y is meaningless. Paired evaluation on identical queries enables direct comparison and paired statistical tests.

**Trade-off:** All systems must be able to process all queries (including those with no evidence).

**Consequence:** Win/tie/loss analysis is statistically valid.

### Decision 127: Fixed Rubric Ensures Consistency

**Date:** Phase 14
**Decision:** Evaluators follow a detailed rubric with 1–5 scales, definitions, and examples for each dimension.

**Rationale:** Without a rubric, each evaluator develops their own implicit scoring standards. A fixed rubric with examples calibrates scoring across annotators and sessions.

**Trade-off:** Rigid rubrics may not capture all edge cases.

**Consequence:** Inter-annotator agreement can be measured; scoring is documented and auditable.

### Decision 128: Grounding and Helpfulness Are Evaluated Separately

**Date:** Phase 14
**Decision:** Groundedness and helpfulness are independent dimensions, not a single combined metric.

**Rationale:** A reply can be fully grounded ("Please contact support") but unhelpful, or helpful-looking ("Your refund arrives tomorrow") but unsupported. Combining them hides this critical trade-off.

**Trade-off:** Two separate scores instead of one combined score.

**Consequence:** The evaluation explicitly surfaces the grounding-helpfulness trade-off.

### Decision 129: Automated Metrics Are Supplementary

**Date:** Phase 14
**Decision:** Automated metrics (response length, grounding pass rate, risk rate, retrieval coverage) are reported alongside human scores but not used as primary quality signals.

**Rationale:** Automated metrics provide useful diagnostics (e.g., "System A produces very short replies") but cannot assess whether those replies are actually good.

**Trade-off:** More metrics to report and interpret.

**Consequence:** The report includes both human quality scores and automated diagnostics for completeness.

### Decision 130: Paired Comparisons Over Independent Rankings

**Date:** Phase 14
**Decision:** System comparison uses paired win/tie/loss analysis on the same queries rather than independent mean-score rankings.

**Rationale:** Independent rankings can be misleading if systems are evaluated on different query distributions. Paired analysis compares systems directly on identical inputs.

**Trade-off:** Only pairwise comparisons are reported, not global rankings.

**Consequence:** Results are statistically honest and directly comparable.

### Decision 131: Golden Data Is Not Used for Tuning

**Date:** Phase 14
**Decision:** The golden evaluation set is used only for final locked evaluation, never for prompt tuning, model selection, or threshold adjustment.

**Rationale:** Using golden data for tuning creates information leakage and overestimates real-world performance. The golden set must remain a held-out benchmark.

**Trade-off:** Less data available for development iterations.

**Consequence:** Final golden-set results are trustworthy estimates of real-world performance.

### Decision 132: Single Annotator Results Are Reported Honestly

**Date:** Phase 14
**Decision:** If only one human annotator is available, results are reported as "single-annotator evaluation" without claiming inter-annotator agreement.

**Rationale:** Fabricating agreement statistics from a single annotator is dishonest. Clearly documenting the limitation is more useful than false precision.

**Trade-off:** Results have lower statistical confidence.

**Consequence:** The report transparently states that results reflect a single evaluator's judgment.

---

## Phase 15 Decisions

### Decision 133: Conservative Escalation — Uncertain → Escalate

**Date:** Phase 15
**Decision:** When the system is uncertain about a query, it must escalate to a human agent rather than attempt auto-handling.

**Rationale:** Under-escalation (wrongly auto-handling a billing or legal query) causes real harm to customers. Over-escalation (unnecessary human handoffs) is an inconvenience but not harmful. Safety-first design mandates escalating when uncertain.

**Trade-off:** Higher escalation rates mean more human workload.

**Consequence:** The default policy is conservative — roughly 60% of queries escalate, prioritizing safety over coverage.

### Decision 134: 20 Reason Codes Across 4 Categories

**Date:** Phase 15
**Decision:** Implement 20 granular reason codes organized into 4 categories: HIGH_RISK (7), RETRIEVAL (3), GROUNDING (2), POLICY (8).

**Rationale:** Granular reason codes make escalation decisions actionable. "Escalate because BILLING_CLAIM + RETRIEVAL_NO_EVIDENCE" is more useful than a single "escalate" flag. Categories enable aggregated reporting.

**Trade-off:** More codes to maintain and test.

**Consequence:** Each escalation decision includes 1+ specific reason codes, enabling targeted improvement.

### Decision 135: Rule-Based Policy Over Learned Policy

**Date:** Phase 15
**Decision:** Use a rule-based policy with configurable thresholds rather than a learned classifier for escalation decisions.

**Rationale:** Rule-based policies are explainable, auditable, and easy to tune in production. A learned policy would be a black box that is harder to debug and justify in an interview setting.

**Trade-off:** Rules may miss complex patterns that a classifier could learn.

**Consequence:** The escalation system can be explained step-by-step in a live interview.

### Decision 136: Confidence Threshold 0.70 Default

**Date:** Phase 15
**Decision:** Set the default minimum intent confidence for auto-handling at 0.70.

**Rationale:** Threshold analysis shows that 0.70 balances auto-handle coverage (~40%) with safety (false auto-handle rate <5%). Higher thresholds reduce auto-handling too aggressively; lower thresholds risk unsafe auto-handles.

**Trade-off:** Some queries that could be auto-handled are escalated.

**Consequence:** The threshold is configurable via `configs/escalation.yaml` for production tuning.

### Decision 137: High-Risk Reasons Always Escalate

**Date:** Phase 15
**Decision:** Queries with high-risk reasons (BILLING_CLAIM, PERSONAL_INFO, CANCELLATION_REQUEST, REFUND_REQUEST, LEGAL_THREATS, THREATS_ABUSE, ACCOUNT_SECURITY) always escalate, regardless of other signals.

**Rationale:** These categories represent situations where incorrect auto-handling causes real harm. Even with high confidence and good evidence, the risk is too high for autonomous handling.

**Trade-off:** Some high-confidence, well-supported queries still escalate.

**Consequence:** The system is safe by design for the most critical categories.

### Decision 138: False Auto-Handle Rate as Primary Safety Metric

**Date:** Phase 15
**Decision:** Use FALSE_AUTO_HANDLE_RATE as the primary safety metric, with a target of <5%.

**Rationale:** A false auto-handle means the system incorrectly handled a query that should have gone to a human. This is the most dangerous failure mode — the customer receives a wrong or incomplete response on a sensitive topic.

**Trade-off:** Optimizing for low false auto-handle rate increases escalation rate.

**Consequence:** The system prioritizes not making harmful mistakes over maximizing coverage.

### Decision 139: Threshold Analysis With Plot

**Date:** Phase 15
**Decision:** Generate a threshold tradeoff plot showing auto-handle rate vs false auto-handle rate at multiple confidence thresholds.

**Rationale:** A single threshold number is less informative than seeing the full tradeoff curve. The plot enables data-driven threshold tuning and makes the tradeoff visible to stakeholders.

**Trade-off:** Requires matplotlib for plot generation.

**Consequence:** The evaluation includes a visual representation of the threshold tradeoff.

### Decision 140: Annotator Guideline — When in Doubt, Escalate

**Date:** Phase 15
**Decision:** The annotation guide explicitly instructs annotators: "When in doubt, escalate."

**Rationale:** Annotator uncertainty should default to ESCALATE_TO_HUMAN. This aligns the annotation standard with the system's safety-first design philosophy.

**Trade-off:** May increase the number of escalations in the gold labels.

**Consequence:** The gold labels are conservative, matching the system's intended behavior.

### Decision 141: Pydantic EscalationDecision for Schema Validation

**Date:** Phase 15
**Decision:** Use Pydantic to validate all escalation decisions, ensuring they conform to the expected schema.

**Rationale:** Schema validation prevents runtime errors from malformed decisions. Pydantic provides automatic type checking, default values, and serialization.

**Trade-off:** Adds Pydantic as a dependency for escalation.

**Consequence:** All escalation decisions are validated and serializable.

---

## Phase 16 Decisions

### Decision 142: Unsafe Auto-Handle Weighted More Heavily

**Date:** Phase 16
**Decision:** Weight false auto-handle cost 10x higher than false escalation cost in policy analysis.

**Rationale:** False auto-handle causes real customer harm (incorrect response on sensitive topic). False escalation causes inconvenience (unnecessary human workload). The 10:1 ratio reflects that unsafe automation is more serious than unnecessary human review.

**Trade-off:** May over-prioritize safety at the expense of coverage.

**Consequence:** Policy optimization favors conservative decisions.

### Decision 143: Thresholds Tuned Only on DEV

**Date:** Phase 16
**Decision:** All threshold optimization uses DEV data only. Golden set remains locked.

**Rationale:** Tuning on golden data would produce overly optimistic results. DEV provides a reliable signal for development without contaminating the evaluation standard.

**Trade-off:** Less data available for optimization.

**Consequence:** Golden-set results are trustworthy estimates of real-world performance.

### Decision 144: Golden Remains Locked

**Date:** Phase 16
**Decision:** Golden evaluation set is used only for final reporting, never for tuning.

**Rationale:** The golden set is the locked evaluation standard. Using it for any development purpose would invalidate evaluation results.

**Trade-off:** Cannot validate policy improvements against golden until final evaluation.

**Consequence:** All policy decisions are made on DEV data.

### Decision 145: Confidence Margin Introduced

**Date:** Phase 16
**Decision:** Add confidence margin signal (gap between top-1 and top-2 intent probabilities).

**Rationale:** A high top-1 probability with a tiny margin may indicate ambiguity. This signal helps detect cases where the model is "unsure but lucky."

**Trade-off:** Adds complexity to signal extraction.

**Consequence:** Policy can detect borderline intent classifications.

### Decision 146: Grounding Remains Hard Safety Gate

**Date:** Phase 16
**Decision:** Grounding failure remains a hard escalation gate in v1.1.

**Rationale:** Weakening grounding safety checks just to increase automation would be dangerous. Grounding failure means the reply is not supported by evidence.

**Trade-off:** May escalate cases that could be safely handled.

**Consequence:** Safety is prioritized over coverage for grounding-related decisions.

### Decision 147: High-Risk Actions Default to Escalation

**Date:** Phase 16
**Decision:** High-risk request detection (account actions, order status, financial claims) defaults to escalation.

**Rationale:** The current system may not have enough capability/evidence to safely resolve these automatically. Escalation is the safe default.

**Trade-off:** May escalate cases that could be handled automatically with sufficient evidence.

**Consequence:** High-risk intents are handled by humans.

### Decision 148: Conversation Complexity Is Heuristic

**Date:** Phase 16
**Decision:** Conversation complexity is computed using heuristics (turn count, repeated requests, contradictions), not ML.

**Rationale:** Heuristic complexity is interpretable, fast, and sufficient for the current evaluation setup. ML-based complexity would add complexity without demonstrated benefit.

**Trade-off:** May miss some complexity patterns.

**Consequence:** Complexity signals are transparent and explainable.

### Decision 149: Policy Versions Are Preserved

**Date:** Phase 16
**Decision:** Both v1.0 and v1.1 policies are preserved. v1.0 is not overwritten.

**Rationale:** Preserving historical policies enables comparison and debugging. The interviewer can see exactly which policy produced which result.

**Trade-off:** More code to maintain.

**Consequence:** Policy versions are tracked and reproducible.

### Decision 150: Cost Values Are Assumptions

**Date:** Phase 16
**Decision:** Cost values (false_auto_handle: 10, false_escalation: 1) are modeling assumptions, not actual business costs.

**Rationale:** Actual business costs are unknown without production data. Using reasonable assumptions enables cost-sensitive analysis while being transparent about limitations.

**Trade-off:** Cost analysis is approximate.

**Consequence:** Policy comparison includes cost as one of many metrics.

### Decision 151: Excessive Rule Specialization Avoided

**Date:** Phase 16
**Decision:** Do not create separate special-case rules for every failed example.

**Rationale:** Over-specialization creates brittle policies that are hard to explain. General signals (low confidence, low evidence, grounding failure) are more robust and interpretable.

**Trade-off:** May miss some edge cases.

**Consequence:** The policy remains explainable and generalizable.

---

## Phase 17 Decisions

### Decision 152: Phase 8 Classifier Used in Production Path

**Date:** Phase 17
**Decision:** Use the Phase 8 SemanticIntentClassifier as the sole intent classifier in the production end-to-end path.

**Rationale:** The Phase 8 classifier has been evaluated and validated. Using baselines (majority, TF-IDF) would degrade performance without justification.

**Trade-off:** None — this is the correct choice.

**Consequence:** Intent classification quality is maximized.

### Decision 153: Baselines Excluded from Production Path

**Date:** Phase 17
**Decision:** Do not use majority baseline or TF-IDF baseline in the production agent pipeline.

**Rationale:** Baselines exist for benchmarking, not production use. The semantic classifier outperforms them.

**Trade-off:** None.

**Consequence:** Only the best available classifier is used.

### Decision 154: Retrieval Precedes Generation

**Date:** Phase 17
**Decision:** Retrieve historical evidence before generating replies.

**Rationale:** The generator needs evidence to produce grounded responses. Without retrieval, the generator would have no basis for its reply.

**Trade-off:** Retrieval latency is added to the pipeline.

**Consequence:** Replies are grounded in actual historical evidence.

### Decision 155: Historical Evidence Treated as Reference Material

**Date:** Phase 17
**Decision:** Historical evidence is treated as untrusted reference data, not authoritative policy.

**Rationale:** Historical responses may contain errors, outdated information, or brand-specific policies that no longer apply. Blind copying could propagate mistakes.

**Trade-off:** More verification required.

**Consequence:** The system avoids blindly copying historical responses.

### Decision 156: Grounding Verification Is Mandatory

**Date:** Phase 17
**Decision:** Every generated reply must pass grounding verification before being considered for AUTO_HANDLE.

**Rationale:** LLMs can hallucinate. Grounding verification catches unsupported claims, PII leakage, and fabricated information.

**Trade-off:** Some valid replies may fail grounding checks.

**Consequence:** Unsafe replies are caught before reaching customers.

### Decision 157: Escalation After Grounding

**Date:** Phase 17
**Decision:** Escalation evaluation happens after grounding verification.

**Rationale:** Grounding results are a critical signal for escalation decisions. If grounding fails, the escalation policy must know about it.

**Trade-off:** None — this is the correct ordering.

**Consequence:** Escalation decisions incorporate grounding quality.

### Decision 158: System Failures Default to Escalation

**Date:** Phase 17
**Decision:** Any critical component failure (intent, retrieval, generation, grounding, escalation) defaults to ESCALATE_TO_HUMAN.

**Rationale:** Fail-closed is safer than fail-open. If the system cannot verify safety, it should not AUTO_HANDLE.

**Trade-off:** May increase escalation rate during system issues.

**Consequence:** System failures never result in unsafe auto-handles.

### Decision 159: Human Review Packages Include Structured Evidence

**Date:** Phase 17
**Decision:** Human review packages include customer message, predicted intent, intent confidence, retrieved evidence, draft reply, grounding status, and escalation reasons.

**Rationale:** Human reviewers need complete context to make informed decisions. Structured packages reduce review time.

**Trade-off:** Larger payload size.

**Consequence:** Human reviewers have all necessary information.

### Decision 160: External Actions Out of Scope

**Date:** Phase 17
**Decision:** The agent does not perform external actions (refunds, account changes, emails, etc.).

**Rationale:** The assignment specifies a support-response recommendation system, not an autonomous action system. External actions require authentication, authorization, and error handling beyond scope.

**Trade-off:** Account-specific requests always escalate.

**Consequence:** The agent is safe by design — it cannot accidentally modify accounts or issue refunds.

### Decision 161: Mock Mode Required for Reproducibility

**Date:** Phase 17
**Decision:** Mock mode is required so that all tests, scripts, and evaluations can run without API keys or internet.

**Rationale:** Reproducibility is essential for evaluation. Tests must pass in any environment.

**Trade-off:** Mock responses are deterministic but not realistic.

**Consequence:** The entire pipeline can be tested offline.

---

## Phase 18 Decisions

### Decision 162: Final Configuration Is Frozen

**Date:** Phase 18
**Decision:** The evaluation configuration (configs/final_evaluation.yaml) is frozen before evaluation begins.

**Rationale:** Freezing configuration prevents post-hoc adjustments that could invalidate results. This ensures reproducibility and honesty in reporting.

**Trade-off:** Cannot fix configuration issues after evaluation starts.

**Consequence:** All results are from a fixed, documented configuration.

### Decision 163: Golden Evaluation Happens Last

**Date:** Phase 18
**Decision:** Golden set evaluation is performed only after all models, prompts, and policies are frozen.

**Rationale:** Using the golden set for tuning would be data leakage. It must be reserved for final, independent evaluation.

**Trade-off:** Cannot iterate on golden results to improve the system.

**Consequence:** Golden evaluation provides an unbiased estimate of real-world performance.

### Decision 164: Multiple Baselines Are Retained

**Date:** Phase 18
**Decision:** Keep all baselines (majority, TF-IDF, always-auto, always-escalate) even though they perform poorly.

**Rationale:** Baselines establish the floor. Without them, we cannot determine if added complexity is justified.

**Trade-off:** More comparisons to report.

**Consequence:** Clear evidence that semantic classifier and risk-aware policy improve over simple approaches.

### Decision 165: Macro F1 Is Primary Intent Metric

**Date:** Phase 18
**Decision:** Use macro F1 as the primary metric for intent classification, not accuracy.

**Rationale:** Intent classes may be imbalanced. Macro F1 treats all classes equally, preventing majority-class bias.

**Trade-off:** May penalize systems that perform well on common intents but poorly on rare ones.

**Consequence:** Intent evaluation accounts for performance across all intent types.

### Decision 166: Reply Quality Uses Human Evaluation Framework

**Date:** Phase 18
**Decision:** Reply quality evaluation uses the six-dimension framework (relevance, groundedness, correctness, helpfulness, completeness, style) from Phase 14.

**Rationale:** Automated metrics (BLEU, ROUGE) do not capture reply quality. Human evaluation (or LLM-as-judge) is necessary.

**Trade-off:** More expensive and time-consuming than automated metrics.

**Consequence:** Reply quality results are meaningful and interpretable.

### Decision 167: Grounding Metrics Are Separate

**Date:** Phase 18
**Decision:** Grounding evaluation is separate from reply quality evaluation.

**Rationale:** Grounding measures whether the reply is supported by evidence. Quality measures whether the reply is good. These are different properties.

**Trade-off:** More metrics to report.

**Consequence:** Clear distinction between "supported by evidence" and "good reply."

### Decision 168: False Auto-Handle Is Emphasized

**Date:** Phase 18
**Decision:** FALSE_AUTO_HANDLE_RATE is the primary safety metric for escalation evaluation.

**Rationale:** Auto-handling a request that should have been escalated is the most dangerous failure mode. It can send incorrect or harmful responses to customers.

**Trade-off:** May lead to overly conservative escalation policies.

**Consequence:** Safety is prioritized over automation rate.

### Decision 169: End-to-End Accuracy Is Not Fabricated

**Date:** Phase 18
**Decision:** Do not report a single "agent accuracy" metric when no end-to-end ground truth exists.

**Rationale:** Without human-labeled ground truth for end-to-end decisions, any "accuracy" claim would be fabricated.

**Trade-off:** Cannot provide a single headline number.

**Consequence:** Evaluation is honest about what can and cannot be measured.

### Decision 170: Pipeline Attrition Is Measured

**Date:** Phase 18
**Decision:** Track how many requests survive each pipeline stage (intent → retrieval → generation → grounding → escalation).

**Rationale:** Understanding where requests are lost helps identify bottlenecks and failure modes.

**Trade-off:** More detailed reporting required.

**Consequence:** Clear visibility into pipeline behavior.

### Decision 171: Limitations Are Included in Headline Results

**Date:** Phase 18
**Decision:** Every reported metric includes its limitations and what it does not measure.

**Rationale:** Honest evaluation requires acknowledging limitations. Overclaiming undermines trust.

**Trade-off:** Results look less impressive.

**Consequence:** The evaluation is trustworthy and reproducible.

### Decision 172: Real Dataset Not Downloaded

**Date:** Phase 18
**Decision:** Proceed with evaluation using synthetic data since the real dataset was not downloaded.

**Rationale:** The evaluation framework is valuable even without real data. It demonstrates the methodology and can be reused when real data is available.

**Trade-off:** Results are not from real customer support data.

**Consequence:** All metrics are demonstrations, not production performance estimates.

---

## Phase 19 Decisions

### Decision 173: Human Evaluation Remains Primary

**Date:** Phase 19
**Decision:** Human evaluation from Phase 14 remains the primary reference for reply quality. The LLM judge is supplementary.

**Rationale:** Human judgment captures nuances that automated metrics miss. The LLM judge complements human evaluation for scalability but cannot replace it.

**Trade-off:** Slower evaluation process, but more reliable quality assessment.

**Consequence:** Quality decisions are based on human judgment, not automated scores.

### Decision 174: Same Six Dimensions Are Reused

**Date:** Phase 19
**Decision:** The LLM judge uses the same six dimensions (relevance, groundedness, correctness, helpfulness, completeness, style) as human evaluation.

**Rationale:** Using the same dimensions ensures consistency between human and LLM evaluation. Creating new dimensions would make comparison impossible.

**Trade-off:** Cannot optimize dimensions for LLM evaluation.

**Consequence:** Direct comparison between human and LLM scores is possible.

### Decision 175: Judge System Identity Is Hidden

**Date:** Phase 19
**Decision:** Systems are anonymized as A/B/C/D in judge input. Mapping is stored separately.

**Rationale:** Hidden identity prevents bias toward known systems. The judge evaluates only the reply quality, not the system reputation.

**Trade-off:** Cannot analyze per-system bias in judge.

**Consequence:** Blind evaluation prevents systematic bias.

### Decision 176: Judge Receives Evidence

**Date:** Phase 19
**Decision:** The judge receives the same evidence used to generate the reply.

**Rationale:** To evaluate groundedness, the judge must know what evidence was available. Without evidence, groundedness scoring is impossible.

**Trade-off:** Judge may be influenced by evidence quality.

**Consequence:** Groundedness evaluation is evidence-based.

### Decision 177: Judge Cannot Browse

**Date:** Phase 19
**Decision:** The judge must NOT browse the internet, invent policies, or infer current facts.

**Rationale:** The judge should evaluate only the supplied evidence. Allowing external knowledge would make evaluation uncontrolled and non-reproducible.

**Trade-off:** Judge cannot verify facts against external sources.

**Consequence:** Evaluation is controlled and reproducible.

### Decision 178: Overall Score Is Recalculated Locally

**Date:** Phase 19
**Decision:** The overall score is calculated locally as the mean of six dimensions, not from LLM output.

**Rationale:** LLM arithmetic may be inaccurate. Local calculation ensures correctness and consistency.

**Trade-off:** Minor computational overhead.

**Consequence:** Overall scores are always correct.

### Decision 179: Spearman Is Important for Ordinal Scores

**Date:** Phase 19
**Decision:** Spearman correlation is preferred over Pearson for measuring agreement.

**Rationale:** Scores are ordinal (1-5), not continuous. Spearman measures rank correlation, which is appropriate for ordinal data.

**Trade-off:** Pearson may be misleading for ordinal data.

**Consequence:** Agreement metrics are statistically appropriate.

### Decision 180: Pairwise Agreement Is Measured

**Date:** Phase 19
**Decision:** Pairwise agreement between systems is measured (A vs B comparisons).

**Rationale:** The assignment is fundamentally about deciding which reply is better. Pairwise comparison directly measures this ability.

**Trade-off:** More comparisons to report.

**Consequence:** Direct measurement of "which reply is better" ability.

### Decision 181: Judge Bias Is Analyzed

**Date:** Phase 19
**Decision:** Analyze whether LLM judge systematically favors longer, more confident, or more verbose replies.

**Rationale:** LLM judges may have systematic biases. Understanding these biases is essential for interpreting results.

**Trade-off:** Additional analysis required.

**Consequence:** Biases are documented and can be accounted for.

### Decision 182: LLM Judge Is Supplementary

**Date:** Phase 19
**Decision:** The LLM judge is used for scalable supplementary evaluation, not as the authoritative quality measure.

**Rationale:** Without strong validation on real data, the LLM judge cannot be trusted as the sole quality measure.

**Trade-off:** Cannot fully automate quality assessment.

**Consequence:** Quality decisions require human oversight.
