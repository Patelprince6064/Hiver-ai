"""Policy versioning system for escalation policies.

Supports explicit policy versions with metadata tracking for reproducibility.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PolicyVersion:
    """Metadata for a policy version."""

    version: str
    name: str
    description: str
    created_at: str = ""
    config_hash: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    parent_version: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# Registry of known policy versions
_POLICY_REGISTRY: dict[str, PolicyVersion] = {}


def register_policy_version(
    version: str,
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
    parent_version: str = "",
    config_hash: str = "",
) -> PolicyVersion:
    """Register a new policy version."""
    pv = PolicyVersion(
        version=version,
        name=name,
        description=description,
        parameters=parameters or {},
        parent_version=parent_version,
        config_hash=config_hash,
    )
    _POLICY_REGISTRY[version] = pv
    return pv


def get_policy_version(version: str) -> PolicyVersion | None:
    """Get a registered policy version."""
    return _POLICY_REGISTRY.get(version)


def list_policy_versions() -> list[PolicyVersion]:
    """List all registered policy versions."""
    return list(_POLICY_REGISTRY.values())


def get_policy_version_strings() -> list[str]:
    """Get all registered version strings."""
    return sorted(_POLICY_REGISTRY.keys())


def build_evaluation_metadata(
    policy_version: str,
    config_version: str,
    dataset_name: str,
    dataset_hash: str = "",
    seed: int = 42,
    dataset_size: int = 0,
    model_version: str = "",
    additional: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build metadata dict for an evaluation result.

    This ensures every evaluation result contains:
    - policy_version
    - config version
    - timestamp
    - dataset identifier
    - seed
    """
    metadata = {
        "policy_version": policy_version,
        "config_version": config_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_name": dataset_name,
        "dataset_hash": dataset_hash,
        "seed": seed,
        "dataset_size": dataset_size,
        "model_version": model_version,
    }
    if additional:
        metadata.update(additional)
    return metadata


# Register known versions
register_policy_version(
    version="v1.0",
    name="Phase 15 Conservative Policy",
    description="Conservative rule-based escalation policy from Phase 15. "
    "Escalates on low confidence, missing evidence, grounding failure, "
    "high-risk claims, ambiguous intent, and multi-intent.",
    parameters={
        "min_intent_confidence": 0.70,
        "require_evidence": True,
        "allowed_grounding_statuses": ["pass"],
        "require_valid_reply": True,
        "escalate_on_high_risk": True,
        "escalate_on_ambiguous": True,
        "escalate_on_multi_intent": True,
    },
)

register_policy_version(
    version="v1.1",
    name="Phase 16 Risk-Aware Policy",
    description="Improved risk-aware policy with confidence margin, retrieval quality, "
    "grounding safety gates, high-risk detection, conversation complexity, "
    "and repeated unresolved issue detection.",
    parameters={
        "min_intent_confidence": 0.70,
        "min_confidence_margin": 0.15,
        "require_evidence": True,
        "allowed_grounding_statuses": ["pass"],
        "require_valid_reply": True,
        "escalate_on_high_risk": True,
        "escalate_on_ambiguous": True,
        "escalate_on_multi_intent": True,
        "escalate_on_repeated_unresolved": True,
        "escalate_on_complex_conversation": True,
        "high_risk_default_escalate": True,
    },
    parent_version="v1.0",
)
