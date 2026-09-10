# Headline Metric Selection & Evaluation Framework

This document details the multi-criteria analytical evaluation used to select the primary headline metric for the Hiver AI Customer Support Agent project.

---

## 1. Candidate Metrics Considered

1. **Verified Grounded Reply Quality Score (0.767 / 1.000)**
2. **Intent Classification Macro F1 (0.857)**
3. **Escalation Policy Expected Cost (2.14 vs 6.10 baseline)**
4. **Grounding Verification Pass Rate (56.0%)**
5. **Auto-Handle Rate (70.0%)**
6. **End-to-End Task Success Rate (Not selected due to lack of real ground truth)**

---

## 2. Metric Evaluation Criteria

Each candidate metric was evaluated across nine standardized criteria on a 1–10 scale:

| Evaluation Criterion | Description |
| :--- | :--- |
| **1. Relevance to Assignment** | How directly the metric reflects the primary objective of automated customer support. |
| **2. Interpretability** | How easily business stakeholders and engineering interviewers understand the scale. |
| **3. Ground-Truth Quality** | The reliability and validity of labels or reference rubrics supporting the metric. |
| **4. Sample Size & Power** | Statistical adequacy of the test cohort (N=200 instances, 800 judge pairs). |
| **5. Stability** | Resistance to minor random seed shifts or small outlier variations. |
| **6. Sensitivity to Failures** | Ability of the metric to drop when upstream or downstream defects occur. |
| **7. Risk of Misinterpretation** | Inherent potential for readers to mistake proxy numbers for real-world satisfaction. |
| **8. Reproducibility** | Determinism of evaluation script outputs across repeated runs. |
| **9. Interview Defensibility** | Ability to defend assumptions under adversarial questioning from senior engineers. |

---

## 3. Comparative Evaluation Matrix

| Metric Candidate | Relevance (1-10) | Interpretability (1-10) | Ground Truth (1-10) | Sensitivity (1-10) | Risk of Misinterpretation | Defensibility (1-10) | Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Verified Reply Quality Score** | **9** | **9** | **7** | **8** | Moderate | **9** | **SELECTED (Primary)** |
| **Intent Macro F1** | 7 | 8 | 9 | 5 | High | 8 | Supporting Metric |
| **Escalation Expected Cost** | 8 | 6 | 8 | 8 | High | 7 | Supporting Metric |
| **Grounding Pass Rate** | 8 | 7 | 7 | 7 | High | 7 | Supporting Metric |
| **Auto-Handle Rate** | 7 | 9 | 6 | 2 | Critical (Vulnerable to gaming) | 4 | Rejected as Headline |
| **Composite "AI Success" Score** | 6 | 4 | 5 | 6 | Severe | 3 | Rejected |

---

## 4. Selection Rationale

### Why Reply Quality Was Selected
Customer support is fundamentally judged by the correctness, helpfulness, and safety of the response delivered to the customer. 
- The **Verified Grounded Reply Quality Score (0.767)** directly measures this output across 6 dimensions: Relevance, Groundedness, Correctness, Helpfulness, Completeness, and Style.
- It demonstrates a clear, defensible gain over both the **Historical Response Baseline (0.500, $\Delta = +0.267$)** and the **Generic Template Baseline (0.265, $\Delta = +0.502$)**.
- It captures the combined benefit of retrieval grounding and post-generation safety verification.

### Why Alternative Candidates Were Not Chosen as the Primary Headline
1. **Auto-Handle Rate (70.0%):** A system can trivially achieve 100% auto-handle by disabling the escalation gate entirely, while delivering disastrous answers. Presenting auto-handle rate as a primary success metric is deceptive.
2. **Intent Macro F1 (0.857):** Intent accuracy is an intermediate upstream technical step. Classifying an inquiry accurately as `account` does not help the customer if the generated reply is hallucinated or dangerous.
3. **Escalation Expected Cost (2.14):** Highly valuable for operational risk modeling, but expected cost relies on synthetic unit penalties (e.g., 10× penalty for missed escalation) that are analytical assumptions rather than audited accounting figures.
4. **Composite Metric:** Combining intent accuracy, reply quality, and escalation into an arbitrary single weighted number masks where the system succeeds and where it fails.

---

## 5. Required Supporting Metrics Package

To prevent metric isolation and ensure intellectual honesty, the headline metric MUST always be presented alongside its three supporting metrics:

1. **Primary Headline:** Verified Grounded Reply Quality = **0.767 / 1.000** ($\Delta = +0.267$ vs. Historical Baseline 0.500).
2. **Upstream Foundation:** Intent Macro F1 = **0.857** ($\Delta = +0.277$ vs. TF-IDF 0.580).
3. **Downstream Safety:** Escalation Expected Cost = **2.14** ($\Delta = -3.96$ vs. Always-Auto 6.10).
4. **Factual Integrity:** Grounding Verification Pass Rate = **56.0%** (with 11.5% unsupported claims intercepted).
