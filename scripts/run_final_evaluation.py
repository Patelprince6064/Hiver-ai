"""Run final evaluation pipeline.

Orchestrates all Phase 18 evaluation scripts.

Usage:
    python scripts/run_final_evaluation.py
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_script(script_name: str) -> bool:
    """Run a script and return success status."""
    script_path = PROJECT_ROOT / "scripts" / script_name
    if not script_path.exists():
        print(f"  Script not found: {script_name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print(f"  ✓ {script_name}")
            return True
        else:
            print(f"  ✗ {script_name}")
            print(f"    Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ {script_name} (timeout)")
        return False
    except Exception as e:
        print(f"  ✗ {script_name}: {e}")
        return False


def main() -> None:
    """Run final evaluation pipeline."""
    print("=" * 60)
    print("PHASE 18 - FINAL EVALUATION PIPELINE")
    print("=" * 60)
    
    start_time = time.time()
    
    scripts = [
        ("1. Create Final Manifest", "create_final_manifest.py"),
        ("2. Leakage Check", "final_leakage_check.py"),
        ("3. Intent Evaluation", "final_intent_evaluation.py"),
        ("4. Reply Comparison", "final_reply_comparison.py"),
        ("5. Grounding Evaluation", "final_grounding_evaluation.py"),
        ("6. Escalation Evaluation", "final_escalation_evaluation.py"),
        ("7. End-to-End Evaluation", "final_end_to_end_evaluation.py"),
        ("8. Coverage Quality Analysis", "analyze_coverage_quality.py"),
        ("9. Intent Analysis", "final_intent_analysis.py"),
        ("10. Collect Failures", "collect_final_failures.py"),
        ("11. Baseline Table", "create_final_baseline_table.py"),
        ("12. Evaluation Summary", "create_final_evaluation_summary.py"),
    ]
    
    results = []
    for name, script in scripts:
        print(f"\n{name}")
        success = run_script(script)
        results.append((name, success))
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"\nTotal time: {elapsed:.1f}s")
    
    # Print summary
    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\nFailed scripts:")
        for name, success in results:
            if not success:
                print(f"  - {name}")
    
    print("\nTo view results:")
    print("  python scripts/create_final_evaluation_summary.py")
    print("  python scripts/create_final_baseline_table.py")


if __name__ == "__main__":
    main()
