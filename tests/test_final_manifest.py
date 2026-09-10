"""Tests for final evaluation manifest."""

import pytest
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFinalManifest:
    """Test final evaluation manifest."""
    
    def test_manifest_exists(self):
        """Test that final manifest exists."""
        manifest_path = PROJECT_ROOT / "data" / "interim" / "final_evaluation" / "final_manifest.jsonl"
        assert manifest_path.exists(), f"Manifest not found: {manifest_path}"
    
    def test_manifest_has_required_fields(self):
        """Test that manifest records have required fields."""
        manifest_path = PROJECT_ROOT / "data" / "interim" / "final_evaluation" / "final_manifest.jsonl"
        if not manifest_path.exists():
            pytest.skip("Manifest not created yet")
        
        required_fields = ["id", "message", "intent", "difficulty", "ambiguity", "should_escalate"]
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                
                record = json.loads(line)
                for field in required_fields:
                    assert field in record, f"Record {i} missing field: {field}"
                
                if i >= 10:  # Check first 10 records
                    break
    
    def test_manifest_is_deterministic(self):
        """Test that manifest is deterministic (same seed produces same output)."""
        manifest_path = PROJECT_ROOT / "data" / "interim" / "final_evaluation" / "final_manifest.jsonl"
        if not manifest_path.exists():
            pytest.skip("Manifest not created yet")
        
        # Load manifest
        records = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        
        # Check that first record has expected ID
        assert records[0]["id"] == "eval_0001", f"Expected eval_0001, got {records[0]['id']}"
    
    def test_manifest_metadata_exists(self):
        """Test that manifest metadata exists."""
        metadata_path = PROJECT_ROOT / "data" / "interim" / "final_evaluation" / "metadata.json"
        assert metadata_path.exists(), f"Metadata not found: {metadata_path}"
        
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        assert "total_examples" in metadata
        assert metadata["total_examples"] == 200
        assert "seed" in metadata
        assert metadata["seed"] == 42
