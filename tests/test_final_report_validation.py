"""Tests for Phase 23 Final Report Packaging & Artifact Validation."""

import csv
import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestFinalReportValidation:
    """Test suite verifying the completeness, bounds, and consistency of Phase 23 deliverables."""

    def test_required_report_files_exist(self):
        """Verify all mandatory Phase 23 reports and summary artifacts exist."""
        required_files = [
            REPO_ROOT / "reports" / "final_hiver_report.md",
            REPO_ROOT / "reports" / "final_claim_audit.md",
            REPO_ROOT / "reports" / "interview_defensibility.md",
            REPO_ROOT / "evaluation" / "results" / "final_report_metrics.csv",
            REPO_ROOT / "evaluation" / "results" / "final_report_summary.json",
            REPO_ROOT / "scripts" / "validate_final_report.py",
        ]
        for f in required_files:
            assert f.exists(), f"Mandatory file missing: {f}"

    def test_headline_metric_bounds_and_values(self):
        """Verify the headline metric value and confidence interval bounds."""
        headline_path = REPO_ROOT / "evaluation" / "results" / "headline_metric.json"
        assert headline_path.exists()
        with open(headline_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        val = data.get("value")
        assert val is not None
        assert 0.0 <= val <= 1.0
        assert val == 0.767
        assert data.get("baseline_value") == 0.500

        ci = data.get("confidence_interval")
        assert ci is not None
        if isinstance(ci, dict):
            assert ci["lower"] < val < ci["upper"]
            assert ci["lower"] == 0.7612
            assert ci["upper"] == 0.7728
        elif isinstance(ci, list):
            assert ci[0] < val < ci[1]
            assert ci[0] == 0.7612
            assert ci[1] == 0.7728

    def test_final_summary_json_schema(self):
        """Verify final_report_summary.json contains all required top-level sections."""
        summary_path = REPO_ROOT / "evaluation" / "results" / "final_report_summary.json"
        assert summary_path.exists()
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        expected_sections = [
            "headline_metric",
            "intent_results",
            "retrieval_results",
            "reply_results",
            "grounding_results",
            "escalation_results",
            "judge_results",
            "failure_analysis",
        ]
        for sec in expected_sections:
            assert sec in summary, f"Section '{sec}' missing in final_report_summary.json"

        assert summary["headline_metric"]["value"] == 0.767
        assert summary["intent_results"]["macro_f1"] == 0.857
        assert summary["escalation_results"]["expected_cost"] == 2.14
        assert len(summary["failure_analysis"]["top_5_failure_modes"]) == 5

    def test_final_metrics_csv_contents(self):
        """Verify final_report_metrics.csv has required columns and valid numbers."""
        csv_path = REPO_ROOT / "evaluation" / "results" / "final_report_metrics.csv"
        assert csv_path.exists()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required_cols = ["metric", "system", "value", "unit", "eval_set", "sample_size", "baseline", "baseline_value", "delta", "notes"]
            assert reader.fieldnames == required_cols

            rows = list(reader)
            assert len(rows) >= 8

            for r in rows:
                val = float(r["value"])
                base_val = float(r["baseline_value"])
                name = r["metric"]
                if "F1" in name or "Accuracy" in name or "Rate" in name or "Score" in name:
                    assert 0.0 <= val <= 1.0, f"Value out of bounds for {name}: {val}"

    def test_no_placeholders_in_final_report(self):
        """Verify final_hiver_report.md contains no placeholder tokens."""
        report_path = REPO_ROOT / "reports" / "final_hiver_report.md"
        assert report_path.exists()
        text = report_path.read_text(encoding="utf-8")

        forbidden_tokens = ["TODO", "TBD", "XXX", "<value>", "<metric>", "FIXME"]
        for tok in forbidden_tokens:
            matches = re.findall(rf"\b{re.escape(tok)}\b", text, flags=re.IGNORECASE)
            assert len(matches) == 0, f"Found forbidden placeholder '{tok}' in final report!"

    def test_required_report_sections(self):
        """Verify that final_hiver_report.md contains all mandatory structural sections."""
        report_path = REPO_ROOT / "reports" / "final_hiver_report.md"
        assert report_path.exists()
        text = report_path.read_text(encoding="utf-8")

        required_sections = [
            "1. Executive Summary",
            "2. Problem Framing",
            "What I Built",
            "What I Did NOT Build",
            "3. Dataset & Evaluation Design",
            "4. System Approach",
            "4.1 Intent Classification",
            "4.2 Historical Support Retrieval",
            "4.3 Grounded Reply Generation",
            "4.4 Grounding Verification",
            "4.5 Risk-Aware Escalation Policy",
            "5. Results",
            "6. Headline Metric",
            "7. Top 5 Failure Modes",
            "8. Human vs. LLM-as-Judge Evaluation",
            "9. Escalation Safety & Operational Tradeoffs",
            "10. Prioritized Next-Week Improvement Plan",
            "11. Conclusion",
        ]
        for sec in required_sections:
            assert sec in text, f"Required section heading '{sec}' missing in final report!"

    def test_brand_and_sample_size_consistency(self):
        """Verify consistent reporting of brand_001 and sample size 200."""
        report_path = REPO_ROOT / "reports" / "final_hiver_report.md"
        text = report_path.read_text(encoding="utf-8")
        assert "brand_001" in text
        assert "200" in text
        assert "0.767" in text
        assert "0.500" in text
        assert "0.857" in text
        assert "2.14" in text
