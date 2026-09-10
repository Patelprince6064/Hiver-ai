"""Tests for policy_version.py — Policy versioning system."""

import pytest
from src.escalation.policy_version import (
    PolicyVersion,
    build_evaluation_metadata,
    get_policy_version,
    get_policy_version_strings,
    list_policy_versions,
    register_policy_version,
)


class TestPolicyVersion:
    def test_register_and_get(self):
        pv = register_policy_version(
            version="v_test",
            name="Test Policy",
            description="Test description",
            parameters={"param1": 0.5},
        )
        assert pv.version == "v_test"
        assert pv.name == "Test Policy"
        assert pv.parameters["param1"] == 0.5

        retrieved = get_policy_version("v_test")
        assert retrieved is not None
        assert retrieved.version == "v_test"

    def test_list_versions(self):
        versions = list_policy_versions()
        assert len(versions) >= 2  # v1.0 and v1.1
        version_strings = get_policy_version_strings()
        assert "v1.0" in version_strings
        assert "v1.1" in version_strings

    def test_get_nonexistent(self):
        result = get_policy_version("v_nonexistent")
        assert result is None

    def test_build_evaluation_metadata(self):
        metadata = build_evaluation_metadata(
            policy_version="v1.0",
            config_version="v1.0",
            dataset_name="dev",
            seed=42,
            dataset_size=100,
        )
        assert metadata["policy_version"] == "v1.0"
        assert metadata["config_version"] == "v1.0"
        assert metadata["dataset_name"] == "dev"
        assert metadata["seed"] == 42
        assert metadata["dataset_size"] == 100
        assert "timestamp" in metadata

    def test_build_metadata_with_additional(self):
        metadata = build_evaluation_metadata(
            policy_version="v1.1",
            config_version="v1.1",
            dataset_name="golden",
            additional={"custom_field": "value"},
        )
        assert metadata["custom_field"] == "value"

    def test_v10_registered(self):
        v10 = get_policy_version("v1.0")
        assert v10 is not None
        assert v10.name == "Phase 15 Conservative Policy"
        assert v10.parameters["min_intent_confidence"] == 0.70

    def test_v11_registered(self):
        v11 = get_policy_version("v1.1")
        assert v11 is not None
        assert v11.name == "Phase 16 Risk-Aware Policy"
        assert v11.parent_version == "v1.0"
        assert v11.parameters["min_confidence_margin"] == 0.15
