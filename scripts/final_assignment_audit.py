"""Final assignment requirement audit script.

Audits repository files, mandatory documents, report sections, and deliverables
against the Hiver SDE Intern assignment specifications.

Usage:
    python scripts/final_assignment_audit.py
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def audit_assignment() -> int:
    print("=" * 65)
    print("HIVER SDE INTERN ASSIGNMENT — FINAL REQUIREMENT AUDIT")
    print("=" * 65)

    all_passed = True

    # 1. Mandatory Files & Directories
    file_checks = [
        ("README.md", REPO_ROOT / "README.md"),
        ("DECISION_LOG.md", REPO_ROOT / "DECISION_LOG.md"),
        ("reports/final_hiver_report.md", REPO_ROOT / "reports" / "final_hiver_report.md"),
        ("reports/what_is_misleading_about_my_headline_number.md", REPO_ROOT / "reports" / "what_is_misleading_about_my_headline_number.md"),
        ("reports/interview_defensibility.md", REPO_ROOT / "reports" / "interview_defensibility.md"),
        ("reports/final_submission_checklist.md", REPO_ROOT / "reports" / "final_submission_checklist.md"),
        ("evaluation/results/ directory", REPO_ROOT / "evaluation" / "results"),
        ("tests/ directory", REPO_ROOT / "tests"),
        (".env.example", REPO_ROOT / ".env.example"),
        (".gitignore", REPO_ROOT / ".gitignore"),
    ]

    print("\n[Audit 1/3] Checking Required Files & Directories:")
    for label, path in file_checks:
        if path.exists():
            print(f"  [PASS] {label}")
        else:
            print(f"  [FAIL] {label} (missing at {path})")
            all_passed = False

    # 2. Golden Evaluation Artifacts
    golden_dir = REPO_ROOT / "data" / "golden"
    golden_docs = REPO_ROOT / "docs" / "GOLDEN_METRIC_LIMITATIONS.md"
    print("\n[Audit 2/3] Checking Golden Set & Leakage Safeguards:")
    if golden_dir.exists() and golden_docs.exists():
        print("  [PASS] Golden evaluation artifacts & limitation documents present")
    else:
        print("  [FAIL] Golden artifacts or documentation missing")
        all_passed = False

    # 3. Final Report Required Content Keywords
    print("\n[Audit 3/3] Auditing Final Report Required Topic Coverage:")
    report_path = REPO_ROOT / "reports" / "final_hiver_report.md"
    if report_path.exists():
        text = report_path.read_text(encoding="utf-8")
        keywords = [
            ("Problem Framing", r"problem"),
            ("Baseline Comparisons", r"baseline"),
            ("Top Failure Modes", r"failure"),
            ("Misleading Headline Caveat", r"misleading"),
            ("Next Week Improvement Plan", r"next[\s\-]week"),
        ]
        for topic, pattern in keywords:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"  [PASS] Found '{topic}' coverage (pattern: '{pattern}')")
            else:
                print(f"  [FAIL] Missing '{topic}' coverage (pattern: '{pattern}')")
                all_passed = False
    else:
        print("  [FAIL] Final report missing, cannot audit topics")
        all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("FINAL AUDIT RESULT: ALL REQUIREMENTS PASS")
        print("=" * 65)
        return 0
    else:
        print("FINAL AUDIT RESULT: SOME REQUIREMENTS FAILED")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(audit_assignment())
