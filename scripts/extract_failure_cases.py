"""Extract Failure Cases.

Uses actual evaluation signals to identify candidate failures.
Never manufactures failure cases - all examples originate from actual evaluation outputs.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.failure_analysis_schema import (
    FailureRecord,
    PrimaryCategory,
    SecondaryCategory,
    Severity,
    SEVERITY_WEIGHTS,
)
from src.evaluation.failure_severity import classify_severity


def load_jsonl(filepath: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_json(filepath: str) -> dict:
    """Load JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_failures_from_final_evaluation() -> list[dict]:
    """Extract failures from Phase 18 final evaluation failures file."""
    failures = []
    failures_file = Path("evaluation/results/final_failures.jsonl")
    if not failures_file.exists():
        return failures

    data = load_jsonl(str(failures_file))
    type_mapping = {
        "wrong_intent": (
            PrimaryCategory.INTENT_CLASSIFICATION_FAILURE.value,
            SecondaryCategory.WRONG_INTENT.value,
            Severity.MEDIUM.value,
            "Intent classifier predicted wrong intent",
        ),
        "retrieval_failure": (
            PrimaryCategory.RETRIEVAL_FAILURE.value,
            SecondaryCategory.NO_RELEVANT_EVIDENCE.value,
            Severity.LOW.value,
            "No relevant evidence found in knowledge base",
        ),
        "insufficient_evidence": (
            PrimaryCategory.RETRIEVAL_FAILURE.value,
            SecondaryCategory.WRONG_EVIDENCE.value,
            Severity.MEDIUM.value,
            "Retrieved evidence lacks sufficient detail for specific customer query",
        ),
        "unsupported_claim": (
            PrimaryCategory.GROUNDING_FAILURE.value,
            SecondaryCategory.UNSUPPORTED_CLAIM.value,
            Severity.HIGH.value,
            "Generated reply contained claims not supported by evidence",
        ),
        "unsafe_auto_handle": (
            PrimaryCategory.ESCALATION_FAILURE.value,
            SecondaryCategory.UNSAFE_AUTO_HANDLE.value,
            Severity.CRITICAL.value,
            "High-risk request auto-handled instead of escalated to human",
        ),
        "unnecessary_escalation": (
            PrimaryCategory.ESCALATION_FAILURE.value,
            SecondaryCategory.UNNECESSARY_ESCALATION.value,
            Severity.LOW.value,
            "Routine, low-risk inquiry escalated unnecessarily to human agent",
        ),
    }

    for i, item in enumerate(data):
        fail_type = item.get("type", "")
        pri_cat, sec_cat, default_sev, default_cause = type_mapping.get(
            fail_type,
            (
                PrimaryCategory.GENERATION_FAILURE.value,
                SecondaryCategory.UNHELPFUL.value,
                item.get("severity", Severity.MEDIUM.value),
                item.get("description", "Evaluation failure"),
            ),
        )

        record = FailureRecord(
            failure_id=f"FAIL_PH18_{i+1:03d}",
            query_id=item.get("query_id", f"q_final_{i+1:03d}"),
            primary_category=pri_cat,
            secondary_category=sec_cat,
            severity=item.get("severity", default_sev),
            customer_message=item.get("message", ""),
            predicted_intent=item.get("predicted_intent", ""),
            intent_confidence=float(item.get("confidence", 0.0)),
            reply=item.get("reply", ""),
            failure_tags=[fail_type, item.get("severity", "").lower()],
            root_cause=item.get("description", default_cause),
            root_cause_confidence="HIGH",
            hypothesis=f"Real failure observed during Phase 18 evaluation: {item.get('description', fail_type)}",
        )
        failures.append(record.to_dict())

    return failures


def extract_failures_from_agent_outputs() -> list[dict]:
    """Extract real failure cases from Phase 18 final agent outputs (200 cases)."""
    failures = []
    outputs_file = Path("evaluation/results/final_agent_outputs.jsonl")
    if not outputs_file.exists():
        return failures

    items = load_jsonl(str(outputs_file))

    for item in items:
        qid = item.get("id", "")
        msg = item.get("message", "")
        reply = item.get("reply") or ""
        intent = item.get("intent", "")
        true_intent = item.get("true_intent", "")
        conf = float(item.get("intent_confidence", 0.0))
        g_status = item.get("grounding_status", "").lower()
        g_score = float(item.get("grounding_score", 0.0))
        ret_count = int(item.get("retrieval_count", 0))
        ret_score = float(item.get("best_retrieval_score", 0.0))
        decision = item.get("decision", "")
        reasons = item.get("escalation_reasons", [])

        # 1. Grounding failure
        if g_status in ["fail", "review"]:
            failures.append(
                FailureRecord(
                    failure_id=f"FAIL_GND_{qid}",
                    query_id=qid,
                    conversation_id=item.get("conversation_id", ""),
                    message_id=item.get("message_id", ""),
                    primary_category=PrimaryCategory.GROUNDING_FAILURE.value,
                    secondary_category=SecondaryCategory.UNSUPPORTED_CLAIM.value,
                    severity=Severity.HIGH.value if g_status == "fail" else Severity.MEDIUM.value,
                    customer_message=msg,
                    reply=reply,
                    predicted_intent=intent,
                    intent_confidence=conf,
                    retrieval_summary={"count": ret_count, "best_score": ret_score},
                    grounding_status=g_status.upper(),
                    escalation_decision=decision,
                    failure_tags=["grounding_failure", f"status_{g_status}"],
                    root_cause=f"Grounding score {g_score:.3f} failed threshold verification",
                    root_cause_confidence="HIGH",
                    hypothesis="Generated text contains claims not strictly verifiable against retrieved evidence",
                    recommended_next_step="Apply stricter grounding filtering or fallback to template",
                ).to_dict()
            )

        # 2. Retrieval failure (zero evidence)
        elif ret_count == 0:
            failures.append(
                FailureRecord(
                    failure_id=f"FAIL_RET_{qid}",
                    query_id=qid,
                    conversation_id=item.get("conversation_id", ""),
                    message_id=item.get("message_id", ""),
                    primary_category=PrimaryCategory.RETRIEVAL_FAILURE.value,
                    secondary_category=SecondaryCategory.NO_RELEVANT_EVIDENCE.value,
                    severity=Severity.MEDIUM.value,
                    customer_message=msg,
                    reply=reply,
                    predicted_intent=intent,
                    intent_confidence=conf,
                    retrieval_summary={"count": 0, "best_score": 0.0},
                    grounding_status=g_status.upper(),
                    escalation_decision=decision,
                    failure_tags=["retrieval_failure", "no_evidence"],
                    root_cause="Zero relevant evidence retrieved from knowledge base",
                    root_cause_confidence="HIGH",
                    hypothesis="Query keywords or semantic representation missed relevant documents in KB",
                    recommended_next_step="Improve query expansion and test hybrid BM25 + dense retrieval",
                ).to_dict()
            )

        # 3. Intent low confidence failure
        elif conf < 0.50 or "LOW_INTENT_CONFIDENCE" in reasons:
            failures.append(
                FailureRecord(
                    failure_id=f"FAIL_INT_{qid}",
                    query_id=qid,
                    conversation_id=item.get("conversation_id", ""),
                    message_id=item.get("message_id", ""),
                    primary_category=PrimaryCategory.INTENT_CLASSIFICATION_FAILURE.value,
                    secondary_category=SecondaryCategory.LOW_CONFIDENCE.value,
                    severity=Severity.MEDIUM.value,
                    customer_message=msg,
                    reply=reply,
                    predicted_intent=intent,
                    intent_confidence=conf,
                    retrieval_summary={"count": ret_count, "best_score": ret_score},
                    grounding_status=g_status.upper(),
                    escalation_decision=decision,
                    failure_tags=["low_intent_confidence"],
                    root_cause=f"Intent classifier confidence ({conf:.3f}) below decision threshold",
                    root_cause_confidence="HIGH",
                    hypothesis="Short or ambiguous message lacks sufficient lexical markers for confident classification",
                    recommended_next_step="Incorporate conversational turn context or clarification prompt",
                ).to_dict()
            )

    return failures


def extract_failures_from_escalation() -> list[dict]:
    """Extract failures from Phase 15/16 escalation error analysis with real observed examples."""
    failures = []
    esc_file = Path("evaluation/results/escalation_error_analysis.json")
    if not esc_file.exists():
        return failures

    data = load_json(str(esc_file))
    error_examples = data.get("error_examples", {})

    # 1. High risk detection failures (UNSAFE_AUTO_HANDLE - CRITICAL)
    for i, ex in enumerate(error_examples.get("E_high_risk_detection_failure", [])):
        failures.append(
            FailureRecord(
                failure_id=f"FAIL_ESC_UNSAFE_{i+1:03d}",
                query_id=ex.get("query_id", f"esc_risk_{i+1:03d}"),
                primary_category=PrimaryCategory.ESCALATION_FAILURE.value,
                secondary_category=SecondaryCategory.UNSAFE_AUTO_HANDLE.value,
                severity=Severity.CRITICAL.value,
                customer_message=ex.get("customer_message", ""),
                predicted_intent=ex.get("intent", ""),
                intent_confidence=float(ex.get("signals", {}).get("intent_confidence", 0.85)),
                escalation_decision=ex.get("predicted_decision", "AUTO_HANDLE"),
                failure_tags=["unsafe_auto_handle", "high_risk_missed"],
                root_cause="High-risk request auto-handled instead of escalated to human agent",
                root_cause_confidence="HIGH",
                hypothesis="Risk keywords or sentiment was not captured by heuristic risk rules",
                recommended_next_step="Strengthen high-risk intent triggers and add keyword regex filters",
            ).to_dict()
        )

    # 2. Intent uncertainty triggering escalation (MEDIUM)
    for i, ex in enumerate(error_examples.get("C_intent_uncertainty", [])):
        failures.append(
            FailureRecord(
                failure_id=f"FAIL_ESC_UNCERT_{i+1:03d}",
                query_id=ex.get("query_id", f"esc_uncert_{i+1:03d}"),
                primary_category=PrimaryCategory.ESCALATION_FAILURE.value,
                secondary_category=SecondaryCategory.INCORRECT_ESCALATION_REASON.value,
                severity=Severity.MEDIUM.value,
                customer_message=ex.get("customer_message", ""),
                predicted_intent=ex.get("intent", ""),
                intent_confidence=float(ex.get("signals", {}).get("intent_confidence", 0.65)),
                escalation_decision=ex.get("predicted_decision", "ESCALATE_TO_HUMAN"),
                failure_tags=["intent_uncertainty", "unnecessary_escalation"],
                root_cause="Borderline intent confidence triggered unnecessary escalation",
                root_cause_confidence="HIGH",
                hypothesis="Confidence threshold was too conservative for standard routine inquiries",
                recommended_next_step="Calibrate intent threshold per intent class",
            ).to_dict()
        )

    # 3. Policy threshold borderline cases (MEDIUM)
    for i, ex in enumerate(error_examples.get("G_policy_threshold", [])):
        failures.append(
            FailureRecord(
                failure_id=f"FAIL_ESC_THRESH_{i+1:03d}",
                query_id=ex.get("query_id", f"esc_thresh_{i+1:03d}"),
                primary_category=PrimaryCategory.ESCALATION_FAILURE.value,
                secondary_category=SecondaryCategory.INCORRECT_ESCALATION_REASON.value,
                severity=Severity.MEDIUM.value,
                customer_message=ex.get("customer_message", ""),
                predicted_intent=ex.get("intent", ""),
                intent_confidence=float(ex.get("signals", {}).get("intent_confidence", 0.70)),
                escalation_decision=ex.get("predicted_decision", "ESCALATE_TO_HUMAN"),
                failure_tags=["policy_threshold", "borderline_escalation"],
                root_cause="Policy threshold boundary misclassified borderline request",
                root_cause_confidence="MEDIUM",
                hypothesis="Composite threshold does not smoothly separate edge cases",
                recommended_next_step="Tune escalation decision boundary on validation split",
            ).to_dict()
        )

    # 4. Complexity failure (HIGH)
    for i, ex in enumerate(error_examples.get("F_complexity_failure", [])):
        failures.append(
            FailureRecord(
                failure_id=f"FAIL_ESC_COMPLEX_{i+1:03d}",
                query_id=ex.get("query_id", f"esc_complex_{i+1:03d}"),
                primary_category=PrimaryCategory.ESCALATION_FAILURE.value,
                secondary_category=SecondaryCategory.MISSED_HIGH_RISK_CASE.value,
                severity=Severity.HIGH.value,
                customer_message=ex.get("customer_message", ""),
                predicted_intent=ex.get("intent", ""),
                escalation_decision=ex.get("predicted_decision", "AUTO_HANDLE"),
                failure_tags=["complexity_failure", "missed_escalation"],
                root_cause="High complexity conversation failed to trigger escalation",
                root_cause_confidence="HIGH",
                hypothesis="Turn count and sentiment variance alone did not exceed complexity threshold",
                recommended_next_step="Include customer frustration score in complexity score",
            ).to_dict()
        )

    return failures


def extract_judge_disagreements() -> tuple[list[dict], list[dict]]:
    """Extract judge disagreements from Phase 19/20 outputs.
    
    Returns:
        (disagreement_failures_for_candidates, judge_disagreement_cases_for_separate_file)
    """
    candidate_failures = []
    judge_cases = []

    judge_file = Path("evaluation/results/judge_disagreements.json")
    dataset_file = Path("evaluation/results/judge_agreement_dataset.jsonl")

    # Map dataset details by judge_item_id
    item_details = {}
    if dataset_file.exists():
        for line in load_jsonl(str(dataset_file)):
            jid = line.get("judge_item_id")
            if jid:
                item_details[jid] = line

    if judge_file.exists():
        data = load_json(str(judge_file))
        disagreements_data = data.get("disagreements", {})
        
        examples_list = []
        if isinstance(disagreements_data, dict):
            # Collect from high_human_low_llm and high_llm_low_human
            for cat_name in ["high_human_low_llm", "high_llm_low_human"]:
                cat_dict = disagreements_data.get(cat_name, {})
                for ex in cat_dict.get("examples", []):
                    ex["disagreement_type"] = cat_name
                    examples_list.append(ex)
        elif isinstance(disagreements_data, list):
            examples_list = disagreements_data

        for i, dis in enumerate(examples_list):
            jid = dis.get("judge_item_id", f"judge_dis_{i+1:03d}")
            parent_info = item_details.get(jid, {})
            human_score = dis.get("human_score", parent_info.get("human_scores", {}).get("overall"))
            llm_score = dis.get("llm_score", parent_info.get("llm_scores", {}).get("overall"))
            diff = dis.get("difference", 0.0)
            dims = dis.get("dimensions", {})

            case_record = {
                "judge_item_id": jid,
                "query_id": parent_info.get("query_id", jid.split("_")[0] if "_" in jid else jid),
                "disagreement_type": dis.get("disagreement_type", "human_vs_llm"),
                "human_score": human_score,
                "llm_score": llm_score,
                "difference": diff,
                "dimension_breakdown": dims,
                "customer_message": parent_info.get("customer_message", ""),
                "candidate_reply": parent_info.get("candidate_reply", ""),
                "predicted_intent": parent_info.get("intent", ""),
                "human_failure_tags": parent_info.get("human_failure_tags", []),
                "llm_failure_tags": parent_info.get("llm_failure_tags", []),
                "llm_rationale": parent_info.get("llm_rationale", ""),
                "disagreement_reasons": [
                    "rubric_ambiguity",
                    "judge_strictness_bias",
                    "differing_evaluation_standards",
                ],
            }
            judge_cases.append(case_record)

            # Failure record for evaluation candidates
            candidate_failures.append(
                FailureRecord(
                    failure_id=f"FAIL_JUDGE_{i+1:03d}",
                    query_id=case_record["query_id"],
                    primary_category=PrimaryCategory.EVALUATION_FAILURE.value,
                    secondary_category=SecondaryCategory.JUDGE_DISAGREEMENT.value,
                    severity=Severity.LOW.value,
                    customer_message=case_record["customer_message"],
                    reply=case_record["candidate_reply"],
                    predicted_intent=case_record["predicted_intent"],
                    human_score=human_score,
                    llm_judge_score=llm_score,
                    failure_tags=["judge_disagreement", f"diff_{abs(diff):.1f}"],
                    root_cause=f"Human ({human_score}) vs LLM judge ({llm_score}) score divergence",
                    root_cause_confidence="LOW",
                    hypothesis="LLM judge applies stricter criteria on completeness/style than human annotator",
                    recommended_next_step="Refine judge rubrics with few-shot calibration examples",
                ).to_dict()
            )

    return candidate_failures, judge_cases


def extract_all_failures() -> tuple[list[dict], list[dict]]:
    """Extract all failures from evaluation outputs without fabricating data."""
    all_failures = []

    # 1. Phase 18 final failures
    all_failures.extend(extract_failures_from_final_evaluation())

    # 2. Phase 18 agent outputs (real 200 cases)
    all_failures.extend(extract_failures_from_agent_outputs())

    # 3. Escalation failures (real error cases)
    all_failures.extend(extract_failures_from_escalation())

    # 4. Judge disagreement failures
    judge_failures, judge_cases = extract_judge_disagreements()
    all_failures.extend(judge_failures)

    # Deduplicate by failure_id
    seen_ids = set()
    deduped = []
    for f in all_failures:
        fid = f.get("failure_id", "")
        if fid not in seen_ids:
            seen_ids.add(fid)
            deduped.append(f)

    return deduped, judge_cases


def save_jsonl(records: list[dict], output_path: str) -> None:
    """Save records to JSONL file."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def main():
    """Main entry point."""
    print("=" * 60)
    print("EXTRACTING FAILURE CASES (PHASE 21)")
    print("=" * 60)

    failures, judge_cases = extract_all_failures()

    # Save failure candidates
    candidates_path = "evaluation/results/failure_candidates.jsonl"
    save_jsonl(failures, candidates_path)
    print(f"\nSaved {len(failures)} failure candidates to: {candidates_path}")

    # Save judge disagreement cases separately (Section 8 requirement)
    disagreements_path = "evaluation/results/judge_disagreement_cases.jsonl"
    save_jsonl(judge_cases, disagreements_path)
    print(f"Saved {len(judge_cases)} judge disagreement cases to: {disagreements_path}")

    # Summary
    print("\nExtraction Summary by Primary Category:")
    cat_counts = {}
    for f in failures:
        cat = f.get("primary_category", "UNKNOWN")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")

    print("\nExtraction Summary by Severity:")
    sev_counts = {}
    for f in failures:
        sev = f.get("severity", "LOW")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        print(f"  {sev}: {sev_counts.get(sev, 0)}")


if __name__ == "__main__":
    main()