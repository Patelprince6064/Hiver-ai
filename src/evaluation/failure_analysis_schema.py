"""Failure Analysis Schema.

Defines structured failure categories and record format for Phase 21.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PrimaryCategory(Enum):
    """Primary failure categories."""
    DATA_FAILURE = "DATA_FAILURE"
    INPUT_PREPROCESSING_FAILURE = "INPUT_PREPROCESSING_FAILURE"
    INTENT_CLASSIFICATION_FAILURE = "INTENT_CLASSIFICATION_FAILURE"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    EVIDENCE_SELECTION_FAILURE = "EVIDENCE_SELECTION_FAILURE"
    GENERATION_FAILURE = "GENERATION_FAILURE"
    GROUNDING_FAILURE = "GROUNDING_FAILURE"
    ESCALATION_FAILURE = "ESCALATION_FAILURE"
    SYSTEM_FAILURE = "SYSTEM_FAILURE"
    EVALUATION_FAILURE = "EVALUATION_FAILURE"


class SecondaryCategory(Enum):
    """Secondary failure categories."""
    # DATA_FAILURE
    NOISY_INPUT = "noisy_input"
    DUPLICATE = "duplicate"
    MISSING_CONTEXT = "missing_context"
    MALFORMED_DATA = "malformed_data"
    
    # INTENT_CLASSIFICATION_FAILURE
    WRONG_INTENT = "wrong_intent"
    LOW_CONFIDENCE = "low_confidence"
    AMBIGUOUS_INTENT = "ambiguous_intent"
    MULTI_INTENT = "multi_intent"
    
    # RETRIEVAL_FAILURE
    NO_RELEVANT_EVIDENCE = "no_relevant_evidence"
    WRONG_EVIDENCE = "wrong_evidence"
    LOW_SIMILARITY = "low_similarity"
    INTENT_MISMATCH = "intent_mismatch"
    
    # GENERATION_FAILURE
    TOO_GENERIC = "too_generic"
    INCOMPLETE = "incomplete"
    WRONG_RESOLUTION = "wrong_resolution"
    UNHELPFUL = "unhelpful"
    AWKWARD_STYLE = "awkward_style"
    
    # GROUNDING_FAILURE
    UNSUPPORTED_CLAIM = "unsupported_claim"
    UNSUPPORTED_PRICE = "unsupported_price"
    UNSUPPORTED_TIMELINE = "unsupported_timeline"
    UNSUPPORTED_POLICY = "unsupported_policy"
    HISTORICAL_CUSTOMER_INFO = "historical_customer_info"
    
    # ESCALATION_FAILURE
    UNSAFE_AUTO_HANDLE = "unsafe_auto_handle"
    UNNECESSARY_ESCALATION = "unnecessary_escalation"
    MISSED_HIGH_RISK_CASE = "missed_high_risk_case"
    INCORRECT_ESCALATION_REASON = "incorrect_escalation_reason"
    
    # SYSTEM_FAILURE
    PROVIDER_ERROR = "provider_error"
    INVALID_OUTPUT = "invalid_output"
    TIMEOUT = "timeout"
    PIPELINE_ERROR = "pipeline_error"
    
    # EVALUATION_FAILURE
    JUDGE_DISAGREEMENT = "judge_disagreement"
    ANNOTATION_AMBIGUITY = "annotation_ambiguity"
    INSUFFICIENT_GROUND_TRUTH = "insufficient_ground_truth"


class Severity(Enum):
    """Failure severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class FailureRecord:
    """Structured failure record."""
    failure_id: str
    query_id: str
    conversation_id: str = ""
    message_id: str = ""
    primary_category: str = ""
    secondary_category: str = ""
    severity: str = "LOW"
    customer_message: str = ""
    conversation_context: list = field(default_factory=list)
    predicted_intent: str = ""
    intent_confidence: float = 0.0
    retrieval_summary: dict = field(default_factory=dict)
    evidence_summary: dict = field(default_factory=dict)
    reply: str = ""
    grounding_status: str = ""
    escalation_decision: str = ""
    human_score: Optional[float] = None
    llm_judge_score: Optional[float] = None
    failure_tags: list = field(default_factory=list)
    root_cause: str = ""
    root_cause_confidence: str = "LOW"
    hypothesis: str = ""
    recommended_next_step: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "failure_id": self.failure_id,
            "query_id": self.query_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "primary_category": self.primary_category,
            "secondary_category": self.secondary_category,
            "severity": self.severity,
            "customer_message": self.customer_message,
            "conversation_context": self.conversation_context,
            "predicted_intent": self.predicted_intent,
            "intent_confidence": self.intent_confidence,
            "retrieval_summary": self.retrieval_summary,
            "evidence_summary": self.evidence_summary,
            "reply": self.reply,
            "grounding_status": self.grounding_status,
            "escalation_decision": self.escalation_decision,
            "human_score": self.human_score,
            "llm_judge_score": self.llm_judge_score,
            "failure_tags": self.failure_tags,
            "root_cause": self.root_cause,
            "root_cause_confidence": self.root_cause_confidence,
            "hypothesis": self.hypothesis,
            "recommended_next_step": self.recommended_next_step,
        }


# Failure chain representation
PIPELINE_STAGES = [
    "INPUT",
    "PREPROCESSING",
    "INTENT",
    "RETRIEVAL",
    "EVIDENCE",
    "GENERATION",
    "GROUNDING",
    "ESCALATION",
    "SYSTEM",
]

# Mapping from primary category to pipeline stage
CATEGORY_TO_STAGE = {
    PrimaryCategory.DATA_FAILURE.value: "INPUT",
    PrimaryCategory.INPUT_PREPROCESSING_FAILURE.value: "PREPROCESSING",
    PrimaryCategory.INTENT_CLASSIFICATION_FAILURE.value: "INTENT",
    PrimaryCategory.RETRIEVAL_FAILURE.value: "RETRIEVAL",
    PrimaryCategory.EVIDENCE_SELECTION_FAILURE.value: "EVIDENCE",
    PrimaryCategory.GENERATION_FAILURE.value: "GENERATION",
    PrimaryCategory.GROUNDING_FAILURE.value: "GROUNDING",
    PrimaryCategory.ESCALATION_FAILURE.value: "ESCALATION",
    PrimaryCategory.SYSTEM_FAILURE.value: "SYSTEM",
    PrimaryCategory.EVALUATION_FAILURE.value: "SYSTEM",
}

# Severity weights for priority calculation
SEVERITY_WEIGHTS = {
    Severity.LOW.value: 1,
    Severity.MEDIUM.value: 2,
    Severity.HIGH.value: 4,
    Severity.CRITICAL.value: 8,
}