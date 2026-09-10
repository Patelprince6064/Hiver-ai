"""Create Failure Case Reports.

Generate detailed reports for representative failures.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def load_jsonl(filepath: str) -> list[dict]:
    """Load JSONL file."""
    data = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def mask_pii(text: str) -> str:
    """Mask personally identifiable information.
    
    Args:
        text: Input text.
        
    Returns:
        Masked text.
    """
    import re
    
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Mask phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Mask URLs with personal info
    text = re.sub(r'https?://[^\s]+', '[URL]', text)
    
    return text


def create_failure_report(failure: dict, report_num: int) -> str:
    """Create a failure case report.
    
    Args:
        failure: Failure dictionary.
        report_num: Report number.
        
    Returns:
        Report content in markdown format.
    """
    # Mask PII
    customer_message = mask_pii(failure.get("customer_message", "No observed example in the evaluated sample."))
    reply = mask_pii(failure.get("reply", "No observed example in the evaluated sample."))
    
    # Build report
    report = f"""# Failure {report_num:03d}

## Customer Message

{customer_message}

## Context

Conversation ID: {failure.get('conversation_id', 'N/A')}
Message ID: {failure.get('message_id', 'N/A')}

## Expected Behavior

Response should address customer inquiry accurately and safely.

## Actual Behavior

{failure.get('root_cause', 'Unknown')}

## Intent

- Predicted: {failure.get('predicted_intent', 'N/A')}
- Confidence: {failure.get('intent_confidence', 'N/A')}

## Retrieval

{json.dumps(failure.get('retrieval_summary', {}), indent=2) if failure.get('retrieval_summary') else 'No retrieval data available.'}

## Evidence

{json.dumps(failure.get('evidence_summary', {}), indent=2) if failure.get('evidence_summary') else 'No evidence data available.'}

## Generated Reply

{reply}

## Grounding

- Status: {failure.get('grounding_status', 'N/A')}
- Failure Tags: {', '.join(failure.get('failure_tags', [])) if failure.get('failure_tags') else 'None'}

## Escalation

- Decision: {failure.get('escalation_decision', 'N/A')}

## Human Evaluation

- Score: {failure.get('human_score', 'N/A')}

## LLM Judge Evaluation

- Score: {failure.get('llm_judge_score', 'N/A')}

## Root Cause

{failure.get('root_cause', 'Unknown')}

## Root Cause Confidence

{failure.get('root_cause_confidence', 'LOW')}

## Hypothesis

{failure.get('hypothesis', 'Insufficient evidence.')}

## Recommended Improvement

{failure.get('recommended_next_step', 'No recommendation.')}
"""
    
    return report


def select_representative_failures(failures: list[dict], n: int = 15) -> list[dict]:
    """Select representative failures for detailed reports.
    
    Prioritizes:
    - CRITICAL failures (unsafe auto-handle)
    - HIGH severity failures (grounding / complexity)
    - MEDIUM severity failures (retrieval, intent uncertainty, policy threshold)
    - LOW severity failures (unnecessary escalation, judge disagreements)
    - Surprising / interview-relevant failures
    
    Args:
        failures: List of failure dictionaries.
        n: Target number to select.
        
    Returns:
        Selected failures.
    """
    selected = []
    seen_ids = set()

    def add_failure(f):
        fid = f.get("failure_id", "")
        if fid and fid not in seen_ids:
            seen_ids.add(fid)
            selected.append(f)

    # 1. All CRITICAL failures (e.g., unsafe auto-handle)
    criticals = [f for f in failures if f.get("severity") == "CRITICAL"]
    for f in criticals:
        add_failure(f)

    # 2. Representative HIGH failures from different categories
    highs = [f for f in failures if f.get("severity") == "HIGH"]
    high_by_cat = {}
    for f in highs:
        cat = f.get("primary_category", "")
        if cat not in high_by_cat:
            high_by_cat[cat] = []
        high_by_cat[cat].append(f)
    for cat, flist in high_by_cat.items():
        for f in flist[:3]:
            add_failure(f)

    # 3. Representative MEDIUM failures (retrieval, intent uncertainty, policy threshold)
    mediums = [f for f in failures if f.get("severity") == "MEDIUM"]
    med_by_cat = {}
    for f in mediums:
        cat = f.get("primary_category", "")
        if cat not in med_by_cat:
            med_by_cat[cat] = []
        med_by_cat[cat].append(f)
    for cat, flist in med_by_cat.items():
        for f in flist[:2]:
            add_failure(f)

    # 4. Representative LOW / EVALUATION failures (unnecessary escalation, judge disagreement)
    lows = [f for f in failures if f.get("severity") == "LOW"]
    for f in lows[:3]:
        add_failure(f)

    # Fill remaining up to n with highest priority failures
    if len(selected) < n:
        remaining = [f for f in failures if f.get("failure_id") not in seen_ids]
        remaining.sort(
            key=lambda x: (
                {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x.get("severity", "LOW"), 4),
                -x.get("intent_confidence", 0),
            )
        )
        for f in remaining:
            if len(selected) >= n:
                break
            add_failure(f)

    return selected[:n]


def main():
    """Main entry point."""
    print("=" * 60)
    print("CREATING FAILURE CASE REPORTS")
    print("=" * 60)
    
    # Load failure candidates
    failures_path = "evaluation/results/failure_candidates.jsonl"
    failures = load_jsonl(failures_path)
    
    print(f"\nLoaded {len(failures)} failures")
    
    # Select representative failures
    representative = select_representative_failures(failures)
    
    # Create reports directory
    reports_dir = Path("reports/failures")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate reports
    for i, failure in enumerate(representative, 1):
        report_content = create_failure_report(failure, i)
        report_path = reports_dir / f"failure_{i:03d}.md"
        
        with open(report_path, "w") as f:
            f.write(report_content)
    
    print(f"\nGenerated {len(representative)} failure reports")
    print(f"Reports saved to: {reports_dir}")
    
    # Print summary
    print(f"\nRepresentative Failures Selected:")
    for i, failure in enumerate(representative, 1):
        print(f"  {i}. {failure.get('failure_id', 'N/A')}: {failure.get('primary_category', 'N/A')} - {failure.get('severity', 'N/A')}")


if __name__ == "__main__":
    main()