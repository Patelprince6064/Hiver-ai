"""Run judge agreement analysis.

Orchestrates all Phase 20 agreement analysis scripts.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_script(script_name: str) -> dict:
    """Run a script and capture results.

    Args:
        script_name: Name of the script to run.

    Returns:
        Script execution results.
    """
    script_path = project_root / "scripts" / script_name
    if not script_path.exists():
        return {"status": "error", "message": f"Script not found: {script_path}"}

    print(f"\n{'=' * 60}")
    print(f"Running: {script_name}")
    print(f"{'=' * 60}")

    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300,
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"SUCCESS ({elapsed:.1f}s)")
            if result.stdout:
                print(result.stdout[-500:])  # Last 500 chars
            return {"status": "success", "elapsed": elapsed, "output": result.stdout}
        else:
            print(f"FAILED ({elapsed:.1f}s)")
            print(f"Error: {result.stderr[-500:]}")
            return {"status": "failed", "elapsed": elapsed, "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Script timed out after 300s"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """Main entry point."""
    print("=" * 60)
    print("RUNNING JUDGE AGREEMENT ANALYSIS")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # List of scripts to run
    scripts = [
        "build_judge_agreement_dataset.py",
        "validate_judge_agreement_dataset.py",
        "compare_score_distributions.py",
        "analyze_dimension_agreement.py",
        "analyze_judge_agreement_by_intent.py",
        "find_large_judge_disagreements.py",
        "final_judge_blindness_audit.py",
        "create_agreement_visualizations.py",
    ]

    results = {}
    total_start = time.time()

    for script in scripts:
        results[script] = run_script(script)

    total_elapsed = time.time() - total_start

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r["status"] == "success")
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")

    print(f"\nTotal scripts: {len(scripts)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Total time: {total_elapsed:.1f}s")

    print("\nScript Results:")
    for script, result in results.items():
        status = result["status"].upper()
        elapsed = result.get("elapsed", 0)
        print(f"  {script}: {status} ({elapsed:.1f}s)")

    # Save results
    results_file = project_root / "evaluation" / "results" / "agreement_analysis_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_elapsed": total_elapsed,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }, f, indent=2)

    print(f"\nResults saved to: {results_file}")

    return results


if __name__ == "__main__":
    main()