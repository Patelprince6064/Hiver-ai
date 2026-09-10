# Architecture

This document describes the planned architecture for the Hiver AI Support Agent.

> **Status:** All components below are PLANNED FOR LATER unless explicitly marked as IMPLEMENTED NOW.

---

## Data Layer

The data pipeline follows a four-stage progression:

```
Raw → Interim → Processed → Golden
```

| Stage | Description | Status |
|-------|-------------|--------|
| Raw | Direct download from dataset source | PLANNED |
| Interim | Cleaning, deduplication, initial filtering | PLANNED |
| Processed | Final format ready for training and evaluation | PLANNED |
| Golden | Hand-labelled evaluation set (150–250 examples) | PLANNED |

**Key decision:** Conversation-level separation between train/test splits to prevent leakage.

---

## ML Layer

The ML pipeline consists of five sequential components:

```
Preprocessing → Intent Classifier → Retrieval → Generation → Escalation
```

| Component | Input | Output | Status |
|-----------|-------|--------|--------|
| Preprocessing | Raw tweet text | Cleaned text | PLANNED |
| Intent Classifier | Cleaned text | Intent label + confidence | PLANNED |
| Retrieval | Intent + cleaned text | Top-K historical support threads | PLANED |
| Evidence Sufficiency | Retrieved threads | Sufficient / Insufficient | PLANNED |
| Grounded Reply Generation | Evidence + customer message | Draft reply | PLANNED |
| Escalation Decision | Confidence + evidence sufficiency | Auto-handle / Escalate + reason | PLANNED |

**Key decisions:**
- Intent taxonomy derived from the selected brand's actual data.
- Reply generation grounded in historical support resolutions.
- Evidence-sufficiency check prevents generation without adequate support.

---

## Evaluation Layer

The evaluation system is designed to measure both individual components and end-to-end behavior:

```
Golden Set → Baselines → Agent → Metrics → LLM Judge → Human Agreement
```

| Component | Description | Status |
|-----------|-------------|--------|
| Golden Set | Hand-labelled examples for ground truth | PLANNED |
| Baselines | Trivial (majority class) and simple (TF-IDF + LR) | PLANNED |
| Metrics | Intent, retrieval, reply quality, escalation metrics | PLANNED |
| LLM Judge | Automated reply quality assessment | PLANNED |
| Human Agreement | Inter-rater reliability and judge calibration | PLANNED |

**Key decision:** LLM judge is evaluated against human ratings, not treated as ground truth.

---

## Reproducibility Layer

Every experiment should be reproducible from a clean environment:

```
Configuration → Deterministic Seeds → Scripts → README Commands
```

| Component | Description | Status |
|-----------|-------------|--------|
| Configuration | YAML files for all tunable parameters | IMPLEMENTED NOW |
| Deterministic Seeds | Fixed random seeds for reproducibility | PLANNED |
| Scripts | Automated pipeline execution | PLANNED |
| README Commands | Documented steps to reproduce results | PLANNED |

**Target:** Full headline results reproducible from clean environment in under 15 minutes.

---

## Implementation Roadmap

### Phase 1 — Project Foundation (Current)

- Repository structure
- Configuration system
- Architecture documentation
- Decision log
- Basic tests

### Phase 2 — Data & Preprocessing

- Download and explore dataset
- Select brand
- Build preprocessing pipeline
- Derive intent taxonomy

### Phase 3 — Core Agent

- Intent classifier
- Retrieval system
- Reply generation
- Escalation logic
- Agent orchestration

### Phase 4 — Evaluation

- Golden set creation
- Baseline implementation
- Metric computation
- LLM judge
- Human agreement study

### Phase 5 — Analysis & Polish

- Failure analysis
- Headline metric analysis
- Reproducibility validation
- Documentation
