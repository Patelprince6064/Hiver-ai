"""Validation script to audit final Hiver report consistency and data integrity."""

import csv
import json
import re
import sys
from pathlib import Path


def validate_report_consistency() -> int:
    """Audit final report artifacts for consistency, bounds, and placeholders."""
    repo_root = Path(__file__).resolve().parent.parent
    errors = []
    warnings = []

    print("=" * 60)
    print("VALIDATING FINAL HIVER REPORT & ARTIFACT INTEGRITY")
    print("=" * 60)

    # 1. Check report file existence
    final_report_path = repo_root / "reports" / "final_hiver_report.md"
    if not final_report_path.exists():
        errors.append(f"Missing final report: {final_report_path}")
        return 1

    report_text = final_report_path.read_text(encoding="utf-8")

    # 2. Check for suspicious placeholders
    placeholders = ["TODO", "TBD", "XXX", "<value>", "<metric>", "example metric", "FIXME"]
    for ph in placeholders:
        matches = re.findall(rf"\b{re.escape(ph)}\b", report_text, flags=re.IGNORECASE)
        if matches:
            errors.append(f"Found placeholder '{ph}' {len(matches)} times in final report!")

    # 3. Check Headline Metric JSON vs Report
    headline_json_path = repo_root / "evaluation" / "results" / "headline_metric.json"
    if headline_json_path.exists():
        with open(headline_json_path, "r", encoding="utf-8") as f:
            headline_data = json.load(f)
        headline_val = headline_data.get("value")
        if headline_val is not None and f"{headline_val:.3f}" not in report_text:
            errors.append(f"Headline value {headline_val} not explicitly referenced in final report!")
        else:
            print(f"[OK] Headline metric verified: {headline_val}")

    # 4. Check Final Report Summary JSON
    summary_json_path = repo_root / "evaluation" / "results" / "final_report_summary.json"
    if not summary_json_path.exists():
        errors.append(f"Missing summary JSON: {summary_json_path}")
    else:
        with open(summary_json_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
        required_keys = [
            "headline_metric",
            "intent_results",
            "retrieval_results",
            "reply_results",
            "grounding_results",
            "escalation_results",
            "judge_results",
            "failure_analysis",
        ]
        for rk in required_keys:
            if rk not in summary_data:
                errors.append(f"Missing key '{rk}' in final_report_summary.json")
        print("[OK] Final report summary JSON schema verified.")

    # 5. Check Final Metrics CSV
    metrics_csv_path = repo_root / "evaluation" / "results" / "final_report_metrics.csv"
    if not metrics_csv_path.exists():
        errors.append(f"Missing metrics CSV: {metrics_csv_path}")
    else:
        with open(metrics_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                row_count += 1
                metric_name = row.get("metric", "")
                val_str = row.get("value", "")
                try:
                    val = float(val_str)
                    if "F1" in metric_name or "Accuracy" in metric_name or "Rate" in metric_name or "Score" in metric_name:
                        if not (0.0 <= val <= 1.0):
                            errors.append(f"Metric '{metric_name}' value {val} outside valid range [0, 1]")
                except ValueError:
                    errors.append(f"Metric '{metric_name}' value '{val_str}' is not a valid float")
            if row_count < 5:
                errors.append(f"Metrics CSV has only {row_count} rows; expected at least 5.")
            else:
                print(f"[OK] Final metrics CSV verified ({row_count} metrics, ranges validated).")

    # 6. Check consistency of brand, sample size, and failure count
    if "brand_001" not in report_text:
        errors.append("Target brand 'brand_001' not mentioned in final report.")
    if "200" not in report_text:
        errors.append("Sample size '200' not mentioned in final report.")
    if "Top 5 Failure Modes" not in report_text:
        errors.append("Missing 'Top 5 Failure Modes' heading in final report.")

    print("\nAudit Summary:")
    print(f"Total Errors: {len(errors)}")
    print(f"Total Warnings: {len(warnings)}")

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return 1

    print("\n[OK] ALL FINAL REPORT AUDITS PASSED CLEANLY.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_report_consistency())
