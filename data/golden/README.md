# Golden Evaluation Set

This directory contains the golden evaluation set — a locked, hand-labelled dataset for evaluation.

## Contents

| File | Description |
|------|-------------|
| `golden_candidates.csv` | Candidate pool for annotation |
| `golden_set.jsonl` | Annotated golden examples |
| `golden_set_statistics.json` | Audit statistics |
| `metadata.json` | Golden set metadata |
| `leakage_report.json` | Leakage check results |

## Policy

The golden evaluation set is **evaluation-only**. It must NOT be used for model training or tuning.

## Workflow

1. `python scripts/build_golden_candidates.py` — Build candidate pool
2. `python scripts/annotate_golden.py` — Annotate examples
3. `python scripts/validate_golden_schema.py` — Validate schema
4. `python scripts/check_golden_leakage.py` — Check for leakage
5. `python scripts/audit_golden_set.py` — Audit statistics
