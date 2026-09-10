# Final File Inventory & Repository Taxonomy

A structured index of all core components, evaluation results, documentation, and source code comprising the Hiver AI Support Agent project.

---

### 1. Essential Submission Files
- [`README.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/README.md): Primary project landing page with overview, quickstart, headline metrics, architecture, and baseline comparisons.
- [`DECISION_LOG.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/DECISION_LOG.md): Cleaned repository of 14 non-obvious engineering decisions, backed by the full historical log.
- [`requirements.txt`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/requirements.txt): Minimal Python dependencies for local execution.
- [`.env.example`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/.env.example): Environment variable template (no live API keys).
- [`.gitignore`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/.gitignore): Exclusion rules for virtual environments, raw datasets, caches, and secrets.
- [`run_pipeline.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/run_pipeline.py): Unified phase pipeline runner supporting individual phase execution.

---

### 2. Evaluation Files
- [`evaluation/results/headline_metric.json`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/headline_metric.json): Primary headline metric schema, bootstrap confidence intervals, and baseline deltas.
- [`evaluation/results/final_report_summary.json`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/final_report_summary.json): Complete machine-readable synthesis across all pipeline components.
- [`evaluation/results/final_report_metrics.csv`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/final_report_metrics.csv): Audited tabular metric comparisons against baselines.
- [`evaluation/results/final_metric_table.csv`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/final_metric_table.csv): 9-metric comprehensive benchmarking table.
- [`evaluation/results/denominator_audit.json`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/denominator_audit.json): Exact numerators and denominators for all reported percentages.
- [`evaluation/results/top_5_failure_modes.json`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/top_5_failure_modes.json): Structured breakdown of top 5 failure modes with real examples.
- [`evaluation/results/judge_agreement_summary.json`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/evaluation/results/judge_agreement_summary.json): Dual-annotated human vs LLM judge agreement metrics ($N=10$).

---

### 3. Documentation & Reports
- [`reports/final_hiver_report.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/final_hiver_report.md): Formal 11-section take-home report (~2,350 words, <= 6 pages).
- [`reports/what_is_misleading_about_my_headline_number.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/what_is_misleading_about_my_headline_number.md): Deep-dive into headline metric honesty and caveats.
- [`reports/interview_defensibility.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/interview_defensibility.md): 20 direct answers to critical interviewer challenges.
- [`reports/final_interview_cheatsheet.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/final_interview_cheatsheet.md): 18 concise topic summaries for interview revision.
- [`reports/final_claim_audit.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/final_claim_audit.md): Evidence source and confidence matrix for all report claims.
- [`reports/final_project_readiness.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/final_project_readiness.md): 15-point technical audit and submission scorecard.
- [`reports/final_submission_checklist.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/final_submission_checklist.md): Complete verification checklist for assignment requirements.
- [`reports/notion_submission_notes.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/reports/notion_submission_notes.md): Copy-paste templates for Notion form submission.
- [`demo/README.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/demo/README.md): Dedicated guide for CLI interactive demo execution.
- [`docs/HEADLINE_METRIC_SELECTION.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/docs/HEADLINE_METRIC_SELECTION.md): Analytical selection framework for primary metric.
- [`docs/GOLDEN_METRIC_LIMITATIONS.md`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/docs/GOLDEN_METRIC_LIMITATIONS.md): Golden set boundaries and unpolluted status.

---

### 4. Source Code (`src/`)
- `src/agent/`: End-to-end agent orchestrator (`support_agent.py`), input validation, trace logging, and schema definitions.
- `src/intents/`: Dense bi-encoder semantic intent classifier (`semantic_classifier.py`) and TF-IDF baseline.
- `src/retrieval/`: Historical support knowledge base builder and FAISS semantic retriever (`retriever.py`).
- `src/generation/`: Grounded reply generator (`grounded_reply_generator.py`), evidence selector, context budgeting, and output validation.
- `src/escalation/`: Risk-aware escalation policy engine (`decision_engine.py`, `rule_based_policy.py`), reason codes, and risk signal extractor.
- `src/evaluation/`: Grounding verification checks (`grounding_checks.py`), claim extractor, rubric metrics, and headline metric calculations.

---

### 5. Scripts (`scripts/`)
- [`scripts/quickstart.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/scripts/quickstart.py): Under-2-second headline reproduction script.
- [`scripts/run_agent.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/scripts/run_agent.py): CLI interactive runner and `--demo` execution.
- [`scripts/final_smoke_test.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/scripts/final_smoke_test.py): Fast end-to-end smoke verification command.
- [`scripts/final_assignment_audit.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/scripts/final_assignment_audit.py): Automated audit of all assignment requirements.
- [`scripts/validate_final_report.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/scripts/validate_final_report.py): Consistency and placeholder validator.
- [`scripts/audit_headline_metric.py`](file:///c:/Alpha/hiver%20ai/hiver-ai-support-agent/scripts/audit_headline_metric.py): Denominator and cherry-picking audit.

---

### 6. Tests (`tests/`)
- 869 unit and integration test cases covering:
  - Agent schema, batch processing, traces, and input validation
  - Intent classification and TF-IDF baselines
  - Retrieval recall and leakage isolation
  - Grounding verifiers, numeric checkers, and claim extraction
  - Escalation policies, cost optimization, and reason codes
  - LLM judge reliability, blindness, and agreement
  - Final report validation, denominator audit, and headline sensitivity

---

### 7. Optional / Historical Artifacts
- `docs/DECISION_LOG_FULL_HISTORY.md`: Full archive of all 202+ decisions across phases 1–22.
- `reports/failures/`: 15 individual case reports for detailed failure investigations.
- `evaluation/results/plots/`: Diagnostic PNG plots for calibration curves, scatter distributions, and risk-coverage tradeoffs.

---

### 8. Ignored Local Files
- `.venv/`: Virtual environment binaries and site-packages.
- `**/__pycache__/`, `*.pyc`: Compiled Python bytecode.
- `data/raw/*.csv`: Full 3M-row raw Twitter customer support dataset (excluded to keep repository lightweight).
- `.pytest_cache/`: Temporary test caching directory.
