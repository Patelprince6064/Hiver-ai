# Golden Metric Limitations & Audit

This document explains the role and boundaries of the golden test set within the project evaluation lifecycle.

---

## 1. Golden Set Status in This Repository

In accordance with the frozen project setup and Phase 2–6 specifications:
- The external raw dataset (`thoughtvector/customer-support-on-twitter`) was **not downloaded** to local disk due to API/environment constraints.
- Consequently, the physical golden set directory (`data/golden/`) is **empty (`NOT_AVAILABLE`)**.
- All benchmark numbers reported in Phases 18–21 rely on the frozen synthetic test cohort (`evaluation/results/final_agent_outputs.jsonl`, N=200).

---

## 2. Theoretical vs. Practical Golden Limitations

Even when a golden dataset is fully populated and verified, standard engineering discipline requires recognizing that a golden set does **not** prove production readiness:

### A. Sample Size Limitations
A typical golden benchmark of 100–500 examples yields substantial statistical uncertainty. For example, a 95% binomial confidence interval for an 85% accuracy metric with N=200 spans $[80.1\%, 89.8\%]$. Rare intent failure modes occurring at a 1% frequency can easily be completely missed in a 200-sample draw.

### B. Selected Brand & Domain Shift
The system is scoped around a single selected retail/support brand. Real customer service environments feature multiple brands, evolving catalog schemas, localized terminology, and seasonal surges. A golden set collected at a single point in time cannot represent distribution shifts.

### C. Annotation Subjectivity
Customer support quality has inherent subjective variance:
- What one annotator rates as "concise and polite", another rates as "incomplete".
- Single-annotator golden sets embed individual human preferences directly into the ground truth.
- Without measuring inter-annotator agreement (Krippendorff's $\alpha \ge 0.80$), a golden label reflects a single person's interpretation.

### D. Multi-Turn Dialogue Truncation
Most golden benchmarks evaluate isolated customer turns or short two-turn exchanges. They fail to test long multi-turn conversations where customer frustration accumulates, requirements change mid-stream, or complex back-and-forth debugging is required.

---

## 3. Strict Rule on Golden Set Usage

- The golden dataset must remain **completely frozen**.
- Golden failures identified in Phase 21/22 are documented as empirical findings; they are **never** used to re-tune classifier weights, adjust prompt templates, or tweak escalation thresholds.
- Using golden failures to iteratively patch prompts destroys the statistical validity of the evaluation.
