# Hiver Assignment — Notion Submission Notes

Copy-paste fields prepared for the official Hiver take-home assignment Notion submission form.

---

### Repository:
`[PASTE FINAL GITHUB URL]`

*(e.g., `https://github.com/your-username/hiver-ai-support-agent`)*

---

### Report:
`[PASTE FINAL REPORT URL OR REPOSITORY PATH]`

- **Local Path:** `reports/final_hiver_report.md`
- **Direct GitHub Link:** `https://github.com/your-username/hiver-ai-support-agent/blob/main/reports/final_hiver_report.md`

---

### Demo:
`[PASTE DEMO URL IF AVAILABLE]`

- **CLI Demo Command:** `python scripts/run_agent.py --demo` (runs instantly in local terminal without API keys)
- **Demo Documentation:** `demo/README.md`

---

### One-line Project Description:
An evaluation-first, grounded AI customer-support agent featuring dense intent classification, FAISS historical evidence retrieval, deterministic grounding verification, and an asymmetric risk-aware escalation policy.

---

### Headline Result:
Verified Grounded Reply Quality Score of **0.767 / 1.000** (3.835 / 5.000 raw rubric average; 95% Bootstrap CI: $[0.7612, 0.7728]$), achieving a **+53.4% relative improvement** over historical human support responses (0.500) and **+189.4%** over generic template fallbacks (0.265) on a frozen multi-turn test set ($N=200$).

---

### Important Caveat:
The headline score measures structured adherence to an offline 6-dimension evaluation rubric (relevance, factual groundedness, correctness, completeness, helpfulness, and tone) on synthetic customer dialogues. It does **not** indicate 76.7% autonomous ticket resolution, does not execute live backend transactions, and does not replace human escalation: 2.0% of critical high-risk inquiries were auto-handled unsafely due to compound intent blindspots.
