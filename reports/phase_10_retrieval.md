# Phase 10 — Semantic Retrieval

## Objective

Build a semantic retrieval system that finds relevant historical support examples for incoming customer messages.

## Retrieval Architecture

```
Incoming Customer Message
            ↓
Text Preprocessing
            ↓
Query Embedding (all-MiniLM-L6-v2)
            ↓
FAISS Vector Search (IndexFlatIP)
            ↓
Candidate Historical Records
            ↓
Quality Filtering
            ↓
Top-K Historical Evidence
```

## Knowledge Base Used

Historical customer-support message pairs from Phase 9 knowledge base.

## Retrieval Baselines

**TF-IDF Retrieval (Baseline)**
- Lexical similarity using TF-IDF vectors
- Fast but limited to word overlap

**Semantic Retrieval (Primary)**
- Sentence-transformer embeddings
- Captures meaning, not just words

## Evaluation Method

Retrieval evaluation using proxy relevance labels from DEV split.

## Results

*Pending (requires dataset download)*

## Similarity Analysis

*Pending*

## Intent-Aware Retrieval

Optional intent-based reranking is supported but disabled by default.

Reason: Low-confidence intent predictions should not eliminate candidates.

## Failure Analysis

*Pending*

## Leakage Checks

Golden set conversations are excluded from the retrieval index.

## What Worked?

*Pending*

## What Did Not Work?

*Pending*

## Limitations

- Semantic similarity does not guarantee resolution relevance
- Historical responses may be outdated
- Twitter conversations are noisy
- Similarity score is not correctness

## Decision

Semantic retrieval is the recommended approach if it outperforms TF-IDF on DEV.

## Interview Question: Why Retrieval?

Intent classifier: "What kind of problem is this?"
Retriever: "How has this brand historically handled similar problems?"

## Interview Question: Why Not Just Similar Tweet?

- Semantic similarity does not guarantee resolution relevance
- Similar wording may represent different outcomes
- Historical support responses may be outdated
- Noisy social-media conversations may be incomplete
- Similarity score is not correctness
- Context may matter
