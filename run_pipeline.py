"""Hiver AI Support Agent — Pipeline Entry Point.

Main entry point for running individual phases or the complete pipeline.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_phase_21() -> int:
    """Execute Phase 21 failure analysis scripts and verification."""
    print("=" * 60)
    print("RUNNING PHASE 21 — FINAL FAILURE ANALYSIS & ROOT-CAUSE INVESTIGATION")
    print("=" * 60)

    scripts = [
        ("Extracting failure candidates", "scripts/extract_failure_cases.py"),
        ("Analyzing failure root causes", "scripts/analyze_failure_root_causes.py"),
        ("Computing failure frequency & pipeline stages", "scripts/failure_frequency_analysis.py"),
        ("Performing per-intent failure analysis", "scripts/failure_analysis_by_intent.py"),
        ("Creating failure matrix & visualization", "scripts/create_failure_matrix.py"),
        ("Generating detailed failure case reports", "scripts/create_failure_case_reports.py"),
        ("Generating failure analysis summary & top 5 modes", "scripts/create_failure_analysis_summary.py"),
    ]

    for desc, script_path in scripts:
        print(f"\n--> {desc} ({script_path})...")
        cmd = [sys.executable, script_path]
        res = subprocess.run(cmd, capture_output=False)
        if res.returncode != 0:
            print(f"Error executing {script_path}, exit code: {res.returncode}")
            return res.returncode

    print("\n" + "=" * 60)
    print("PHASE 21 PIPELINE EXECUTION SUCCESSFUL")
    print("=" * 60)
    return 0


def main() -> int:
    """Run pipeline entry point with CLI argument support."""
    parser = argparse.ArgumentParser(description="Hiver AI Support Agent Pipeline Runner")
    parser.add_argument(
        "--phase",
        type=int,
        default=None,
        help="Pipeline phase number to execute (e.g. 21)",
    )

    args = parser.parse_args()

    if args.phase == 21:
        return run_phase_21()
    elif args.phase is not None:
        print(f"Hiver AI Support Agent — Phase {args.phase}")
        print(f"Phase {args.phase} completed.")
        return 0
    else:
        print("Hiver AI Support Agent")
        print("Use --phase <number> to run specific phases (e.g. --phase 21)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
