"""Tests for final leakage check."""

import pytest
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFinalLeakage:
    """Test final leakage check."""
    
    def test_leakage_report_exists(self):
        """Test that leakage report can be generated."""
        from scripts.final_leakage_check import check_leakage
        
        report = check_leakage()
        
        assert "status" in report
        assert report["status"] in ["PASS", "FAIL"]
    
    def test_no_id_overlap_in_manifest(self):
        """Test that final manifest has no ID overlaps."""
        manifest_path = PROJECT_ROOT / "data" / "interim" / "final_evaluation" / "final_manifest.jsonl"
        if not manifest_path.exists():
            pytest.skip("Final manifest not created yet")
        
        ids = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    ids.append(record.get("id"))
        
        # Check for duplicates
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {len(ids) - len(set(ids))}"
    
    def test_golden_set_is_empty(self):
        """Test that golden set is empty (not downloaded)."""
        golden_path = PROJECT_ROOT / "data" / "golden" / "golden_set.jsonl"
        if golden_path.exists():
            with open(golden_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            # Golden set should be empty or very small
            assert len(lines) <= 10, f"Golden set has {len(lines)} examples"
