"""Golden evaluation set schema validation.

This module provides validation for the golden set data format.
It ensures consistency and catches common annotation errors.

The golden set is the locked evaluation dataset — it must NOT be used
for model training or tuning.
"""

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class GoldenExample(BaseModel):
    """A single golden evaluation example."""

    golden_id: str = Field(..., description="Unique identifier for this example")
    conversation_id: str | None = Field(None, description="Source conversation ID")
    message_id: str | None = Field(None, description="Source message ID")
    brand: str = Field(..., description="Selected brand name")
    customer_message: str = Field(..., description="The customer's message text")
    context_messages: list[str] = Field(default_factory=list, description="Surrounding conversation context")
    gold_intent: str = Field(..., description="The labeled intent")
    intent_confidence: str = Field("HIGH", description="Annotation confidence: HIGH/MEDIUM/LOW")
    ambiguous: bool = Field(False, description="Whether this example is ambiguous")
    label_notes: str = Field("", description="Optional annotation notes")
    sampling_category: list[str] = Field(default_factory=list, description="How this example was sampled")
    expected_escalation: bool | None = Field(None, description="Expected escalation decision (if known)")
    escalation_reason: str | None = Field(None, description="Reason for escalation (if known)")
    source_split: str = Field("golden", description="Dataset split identifier")

    @field_validator("golden_id")
    @classmethod
    def validate_golden_id(cls, v: str) -> str:
        if not v.startswith("gold_"):
            raise ValueError(f"golden_id must start with 'gold_': {v}")
        return v

    @field_validator("intent_confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        valid = {"HIGH", "MEDIUM", "LOW"}
        if v not in valid:
            raise ValueError(f"intent_confidence must be one of {valid}: {v}")
        return v

    @field_validator("customer_message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("customer_message cannot be empty")
        return v

    @field_validator("sampling_category")
    @classmethod
    def validate_sampling_categories(cls, v: list[str]) -> list[str]:
        valid_categories = {
            "representative", "rare_intent", "difficult", "confusable",
            "short", "multi_intent", "noisy",
        }
        for cat in v:
            if cat not in valid_categories:
                raise ValueError(f"Invalid sampling_category: {cat}. Valid: {valid_categories}")
        return v


class GoldenSetMetadata(BaseModel):
    """Metadata for the golden evaluation set."""

    version: str = Field("1.0", description="Golden set version")
    size: int = Field(..., description="Number of examples")
    selected_brand: str = Field(..., description="Selected brand name")
    sampling_seed: int = Field(42, description="Random seed used for sampling")
    annotation_method: str = Field("human", description="How examples were annotated")
    locked: bool = Field(False, description="Whether the set is locked")
    intent_taxonomy_version: str = Field("1.0", description="Version of intent taxonomy used")


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------

def validate_golden_example(example: dict[str, Any]) -> list[str]:
    """Validate a single golden example. Returns list of errors."""
    errors = []
    try:
        GoldenExample(**example)
    except Exception as e:
        errors.append(str(e))
    return errors


def validate_golden_set(examples: list[dict[str, Any]], valid_intents: set[str] | None = None) -> dict[str, Any]:
    """Validate an entire golden set. Returns validation report."""
    report = {
        "total_examples": len(examples),
        "errors": [],
        "warnings": [],
        "valid": True,
    }

    # Check for duplicate golden IDs
    ids = [e.get("golden_id") for e in examples]
    duplicate_ids = [id for id in ids if ids.count(id) > 1]
    if duplicate_ids:
        report["errors"].append(f"Duplicate golden IDs: {set(duplicate_ids)}")
        report["valid"] = False

    # Validate each example
    for i, example in enumerate(examples):
        errors = validate_golden_example(example)
        for error in errors:
            report["errors"].append(f"Example {i} ({example.get('golden_id', 'unknown')}): {error}")
            report["valid"] = False

        # Check intent validity
        if valid_intents and example.get("gold_intent") not in valid_intents:
            report["warnings"].append(
                f"Example {example.get('golden_id')}: intent '{example.get('gold_intent')}' not in taxonomy"
            )

    # Check for missing required fields
    required_fields = ["golden_id", "brand", "customer_message", "gold_intent"]
    for i, example in enumerate(examples):
        for field in required_fields:
            if field not in example or not example[field]:
                report["errors"].append(f"Example {i}: missing required field '{field}'")
                report["valid"] = False

    # Check confidence distribution
    confidences = [e.get("intent_confidence", "HIGH") for e in examples]
    low_count = confidences.count("LOW")
    if low_count > len(examples) * 0.1:
        report["warnings"].append(f"High number of LOW confidence examples: {low_count}/{len(examples)}")

    # Check for ambiguous examples
    ambiguous_count = sum(1 for e in examples if e.get("ambiguous", False))
    if ambiguous_count > len(examples) * 0.1:
        report["warnings"].append(f"High number of ambiguous examples: {ambiguous_count}/{len(examples)}")

    return report


def validate_golden_metadata(metadata: dict[str, Any]) -> list[str]:
    """Validate golden set metadata. Returns list of errors."""
    errors = []
    try:
        GoldenSetMetadata(**metadata)
    except Exception as e:
        errors.append(str(e))
    return errors


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_golden_set(golden_path: Path) -> list[dict[str, Any]]:
    """Load the golden set from a JSONL file."""
    examples = []
    with open(golden_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def save_golden_set(examples: list[dict[str, Any]], golden_path: Path) -> None:
    """Save the golden set to a JSONL file."""
    with open(golden_path, "w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")


def load_golden_metadata(metadata_path: Path) -> dict[str, Any]:
    """Load golden set metadata."""
    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_golden_metadata(metadata: dict[str, Any], metadata_path: Path) -> None:
    """Save golden set metadata."""
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
