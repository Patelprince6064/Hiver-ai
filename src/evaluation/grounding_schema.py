"""Grounding verification result schema.

Defines the structured format for grounding verification results.
"""

from typing import Any

from pydantic import BaseModel, Field


class ClaimVerification(BaseModel):
    """Verification result for a single claim."""

    claim: str = Field(..., description="The extracted claim text")
    type: str = Field(..., description="Fact type category")
    supported: bool = Field(..., description="Whether claim is supported")
    confidence: float = Field(0.0, description="Support confidence")
    support_source: str = Field("none", description="Source of support")
    evidence_ids: list[str] = Field(default_factory=list, description="Supporting evidence IDs")
    reason: str = Field("", description="Explanation")


class GroundingVerification(BaseModel):
    """Complete grounding verification result."""

    status: str = Field(..., description="pass|review|fail|insufficient_evidence")
    grounding_score: float = Field(0.0, description="Overall grounding score 0-1")
    claims: list[ClaimVerification] = Field(default_factory=list, description="Verified claims")
    risk_flags: list[str] = Field(default_factory=list, description="Risk flags detected")
    unsupported_claims: list[dict[str, Any]] = Field(default_factory=list, description="Unsupported claims")
    evidence_used: list[str] = Field(default_factory=list, description="Evidence IDs used")
    reason: str = Field("", description="Overall verification reason")
    repair_attempted: bool = Field(False, description="Whether repair was attempted")
    repair_succeeded: bool = Field(False, description="Whether repair succeeded")
    final_status: str = Field("", description="Final status after repair")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def build_grounding_verification(
    status: str,
    grounding_score: float = 0.0,
    claims: list[dict[str, Any]] | None = None,
    risk_flags: list[str] | None = None,
    unsupported_claims: list[dict[str, Any]] | None = None,
    evidence_used: list[str] | None = None,
    reason: str = "",
    repair_attempted: bool = False,
    repair_succeeded: bool = False,
    final_status: str = "",
    metadata: dict[str, Any] | None = None,
) -> GroundingVerification:
    """Build a GroundingVerification from components."""
    claim_verifications = []
    for c in (claims or []):
        claim_verifications.append(ClaimVerification(
            claim=c.get("claim", ""),
            type=c.get("type", "other"),
            supported=c.get("supported", False),
            confidence=c.get("confidence", 0.0),
            support_source=c.get("support_source", "none"),
            evidence_ids=c.get("evidence_ids", []),
            reason=c.get("reason", ""),
        ))

    return GroundingVerification(
        status=status,
        grounding_score=grounding_score,
        claims=claim_verifications,
        risk_flags=risk_flags or [],
        unsupported_claims=unsupported_claims or [],
        evidence_used=evidence_used or [],
        reason=reason,
        repair_attempted=repair_attempted,
        repair_succeeded=repair_succeeded,
        final_status=final_status or status,
        metadata=metadata or {},
    )
