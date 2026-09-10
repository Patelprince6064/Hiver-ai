"""Knowledge base record schema.

Defines the structured format for historical support knowledge base records.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class KnowledgeRecord(BaseModel):
    """A single knowledge base record."""

    knowledge_id: str = Field(..., description="Unique knowledge record ID")
    brand: str = Field(..., description="Brand name")
    conversation_id: str | None = Field(None, description="Source conversation ID")
    source_message_id: str | None = Field(None, description="Source message ID")

    customer_message: str = Field(..., description="Original customer message")
    support_response: str = Field(..., description="Original support response")

    customer_message_normalized: str = Field("", description="Normalized customer message")
    support_response_normalized: str = Field("", description="Normalized support response")

    intent: str | None = Field(None, description="Predicted intent")
    intent_confidence: float | None = Field(None, description="Intent prediction confidence")
    intent_source: str = Field("unlabeled", description="Intent source: semantic_classifier|rule|unlabeled")

    resolution_type: str = Field("unclear", description="Historical response category")
    resolution_evidence: str = Field("", description="Evidence for resolution type")
    resolution_text: str = Field("", description="Canonical retrieval text")

    conversation_position: int = Field(0, description="Position in conversation")

    has_followup: bool = Field(False, description="Whether customer responded after")
    followup_count: int = Field(0, description="Number of follow-up messages")
    final_visible_message_author: str | None = Field(None, description="Who sent last message")
    conversation_end_state: str = Field("unclear", description="Conversation end state")

    quality_flags: list[str] = Field(default_factory=list, description="Quality flags")
    quality_category: str = Field("usable", description="Quality: usable|usable_with_context|low_quality")

    source_timestamp: str | None = Field(None, description="Original timestamp")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("knowledge_id")
    @classmethod
    def validate_knowledge_id(cls, v: str) -> str:
        if not v.startswith("kb_"):
            raise ValueError(f"knowledge_id must start with 'kb_': {v}")
        return v

    @field_validator("quality_category")
    @classmethod
    def validate_quality_category(cls, v: str) -> str:
        valid = {"usable", "usable_with_context", "low_quality"}
        if v not in valid:
            raise ValueError(f"quality_category must be one of {valid}: {v}")
        return v

    @field_validator("customer_message")
    @classmethod
    def validate_customer_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("customer_message cannot be empty")
        return v

    @field_validator("support_response")
    @classmethod
    def validate_support_response(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("support_response cannot be empty")
        return v


def validate_knowledge_record(record: dict[str, Any]) -> list[str]:
    """Validate a knowledge record. Returns list of errors."""
    errors = []
    try:
        KnowledgeRecord(**record)
    except Exception as e:
        errors.append(str(e))
    return errors


def validate_knowledge_base(records: list[dict[str, Any]], valid_intents: set[str] | None = None, valid_resolutions: set[str] | None = None) -> dict[str, Any]:
    """Validate an entire knowledge base. Returns validation report."""
    report = {
        "total_records": len(records),
        "errors": [],
        "warnings": [],
        "valid": True,
    }

    # Check for duplicate knowledge IDs
    ids = [r.get("knowledge_id") for r in records]
    duplicate_ids = [id for id in ids if ids.count(id) > 1]
    if duplicate_ids:
        report["errors"].append(f"Duplicate knowledge IDs: {set(duplicate_ids)}")
        report["valid"] = False

    # Validate each record
    for i, record in enumerate(records):
        errors = validate_knowledge_record(record)
        for error in errors:
            report["errors"].append(f"Record {i} ({record.get('knowledge_id', 'unknown')}): {error}")
            report["valid"] = False

        # Check intent validity
        if valid_intents and record.get("intent") and record["intent"] not in valid_intents:
            report["warnings"].append(
                f"Record {record.get('knowledge_id')}: intent '{record['intent']}' not in taxonomy"
            )

        # Check resolution type validity
        if valid_resolutions and record.get("resolution_type") not in valid_resolutions:
            report["warnings"].append(
                f"Record {record.get('knowledge_id')}: resolution '{record.get('resolution_type')}' not in taxonomy"
            )

    return report
