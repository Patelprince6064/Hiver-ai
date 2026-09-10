# Hiver Submission Checklist

Complete audit verification of all assignment deliverables, repository standards, and evaluation integrity constraints for the Hiver SDE Intern Take-Home.

---

## Assignment Requirements

- [x] **Runnable repository:** Fully self-contained local execution with mock mode support (`python scripts/run_agent.py --demo`).
- [x] **README:** Concise, reviewer-friendly documentation with quickstart, architecture, and baseline comparisons.
- [x] **Reproducible headline result:** Verified Grounded Reply Quality Score (0.767) reproducible in < 2 seconds via `python scripts/quickstart.py`.
- [x] **Golden evaluation set:** Dedicated hand-labeled benchmark architecture defined; locked and unpolluted during development.
- [x] **Sampling/labeling note:** Clear documentation of conversation-level splitting and synthetic data notes where real raw data was not downloaded.
- [x] **Evaluation harness:** Multi-stage evaluation scripts covering intent, retrieval, reply quality, grounding, and escalation.
- [x] **Automated metrics:** Macro F1, Recall@5, Grounding Pass Rate, Expected Escalation Cost, and Rubric Quality Scores.
- [x] **LLM-as-judge:** Blinded (A/B/C/D) evaluation engine scoring 6 dimensions on a 1–5 scale.
- [x] **Human-vs-LLM agreement evidence:** Dual-annotated benchmark ($N=10$) analyzing MAE, exact agreement, within-1 agreement, and rank correlation.
- [x] **Final report <= 6 pages:** `reports/final_hiver_report.md` (~2,350 words across 11 structured sections).
- [x] **Problem framing:** Clear input, output, architecture diagram, what was built, and what was intentionally NOT built.
- [x] **Baseline comparison:** Measured against majority class, TF-IDF, lexical BM25, generic templates, historical human replies, and always-auto policies.
- [x] **Top 5 failure modes:** Ranked by severity-weighted risk score with pipeline stage breakdown.
- [x] **Real failure examples:** Verbatim customer queries from evaluation outputs (e.g., Query `q_final_005`, `eval_0007`).
- [x] **Hypotheses:** Clear hypotheses for each failure mode explicitly marked as hypotheses.
- [x] **Misleading headline metric section:** Comprehensive explanation of why 0.767 does NOT mean 77% resolution or CSAT.
- [x] **Next-week plan:** Prioritized P0–P4 engineering improvement table with expected impact and effort.
- [x] **10–15 decision log entries:** 14 foundational non-obvious engineering decisions formatted with Context, Options considered, Decision, Reason, Consequence.

---

## Repository Standards

- [x] **No secrets:** Repository scanned; zero API keys, tokens, or credentials in tracked files; `.env.example` provided.
- [x] **No unnecessary raw dataset:** Full 3M-row raw CSV not committed; lightweight evaluation samples stored cleanly.
- [x] **No temporary files:** Clean working tree with zero debug logs or scratch dumps.
- [x] **No debug files:** Removed ad-hoc print scripts and temporary artifacts.
- [x] **README commands verified:** All listed commands tested and verified to exit with code 0.
- [x] **Tests pass:** 869 unit and integration tests passing (`pytest -q`).
- [x] **Quickstart verified:** `python scripts/quickstart.py` verified to execute in < 2 seconds.
- [x] **Demo verified:** `python scripts/run_agent.py --demo` runs interactive scenarios with clean ASCII formatting.
- [x] **Git status reviewed:** Clean git tree without unstaged surprises or broken merge commits.

---

## Evaluation Integrity

- [x] **Golden set frozen:** Golden set directory unpolluted; no model tuning against golden evaluations.
- [x] **No golden tuning:** System tuned strictly against training and validation partitions.
- [x] **Train/test leakage checked:** Conversation-level hash splitting verified; zero cross-split thread leakage.
- [x] **Metrics traceable:** All reported numbers backed by deterministic JSON artifacts in `evaluation/results/`.
- [x] **Baselines included:** Every component benchmarked against at least one trivial/simple baseline.
- [x] **Limitations documented:** Offline proxy limitations, single-brand constraints, and single-annotator constraints documented.
- [x] **Proxy labels identified:** Escalation and risk ground truth explicitly identified as rule-derived heuristic labels rather than live enterprise logs.

---

## Submission Preparation

- [x] **GitHub repository is accessible:** Ready for candidate push to submission remote.
- [x] **README is polished:** Clear 2-minute overview for technical evaluators.
- [x] **Final report is ready:** `reports/final_hiver_report.md` formatted and audited.
- [x] **Report link/path is clear:** Prominently linked at top of README and submission notes.
- [x] **Notion submission fields ready:** `reports/notion_submission_notes.md` prepared with copy-paste fields.
- [x] **No sensitive information exposed:** Verified through automated keyword scans.
