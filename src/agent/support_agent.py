"""End-to-end support agent orchestrator.

Combines all components into a single pipeline for processing customer messages.
"""

import logging
import time
from typing import Any

from src.agent.agent_schema import (
    AgentRequest,
    AgentResponse,
    build_agent_response,
)
from src.agent.input_validation import validate_request
from src.agent.trace import AgentTrace, create_trace
from src.evaluation.grounding_checks import run_grounding_checks
from src.escalation.decision_engine import EscalationDecisionEngine
from src.escalation.reason_codes import ReasonCode
from src.escalation.rule_based_policy import RiskAwarePolicy
from src.generation.evidence_selector import EvidenceSelector
from src.generation.grounded_reply_generator import GroundedReplyGenerator
from src.generation.reply_schema import ReplyOutput
from src.intents.semantic_classifier import SemanticIntentClassifier
from src.retrieval.retriever import HistoricalSupportRetriever

logger = logging.getLogger(__name__)


class SupportAgent:
    """End-to-end support agent that orchestrates all components.

    Usage:
        agent = SupportAgent(
            classifier=classifier,
            retriever=retriever,
            generator=generator,
        )
        response = agent.process(request)
    """

    def __init__(
        self,
        classifier: SemanticIntentClassifier | None = None,
        retriever: HistoricalSupportRetriever | None = None,
        generator: GroundedReplyGenerator | None = None,
        escalation_engine: EscalationDecisionEngine | None = None,
        evidence_selector: EvidenceSelector | None = None,
        policy: RiskAwarePolicy | None = None,
        mock_mode: bool = False,
    ) -> None:
        """Initialize the support agent.

        Args:
            classifier: Intent classifier. If None, mock mode is required.
            retriever: Historical support retriever. If None, mock mode is required.
            generator: Grounded reply generator. If None, mock mode is required.
            escalation_engine: Escalation decision engine. If None, creates default.
            evidence_selector: Evidence selector. If None, creates default.
            policy: Escalation policy. If None, uses RiskAwarePolicy (v1.1).
            mock_mode: If True, use mock components for testing.
        """
        self.mock_mode = mock_mode

        if mock_mode:
            self.classifier = classifier or self._create_mock_classifier()
            self.retriever = retriever or self._create_mock_retriever()
            self.generator = generator or self._create_mock_generator()
        else:
            self.classifier = classifier
            self.retriever = retriever
            self.generator = generator

        self.policy = policy or RiskAwarePolicy()
        self.escalation_engine = escalation_engine or EscalationDecisionEngine(
            policy=self.policy
        )
        self.evidence_selector = evidence_selector or EvidenceSelector()

    def process(self, request: AgentRequest) -> AgentResponse:
        """Process a customer message through the full pipeline.

        Args:
            request: The agent request containing the customer message.

        Returns:
            AgentResponse with decision, reply or human review package.
        """
        trace = create_trace()
        start_time = time.time()

        validation = validate_request(request)
        if not validation.is_valid:
            trace.set_error(f"Validation failed: {validation.errors}")
            return self._build_error_response(
                request, trace, "Validation failed", validation.errors
            )

        message = request.message.strip()

        try:
            intent_result = self._classify_intent(message, trace)
            if intent_result is None:
                return self._build_escalation_response(
                    request, trace, start_time,
                    reason_codes=[ReasonCode.PROVIDER_ERROR.value],
                    risk_level="HIGH",
                )
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            trace.set_error(f"Intent classification failed: {e}")
            return self._build_escalation_response(
                request, trace, start_time,
                reason_codes=[ReasonCode.PROVIDER_ERROR.value],
                risk_level="HIGH",
            )

        try:
            retrieval_result, evidence = self._retrieve_evidence(
                message, intent_result, trace
            )
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            trace.set_error(f"Retrieval failed: {e}")
            return self._build_escalation_response(
                request, trace, start_time,
                intent_result=intent_result,
                reason_codes=[ReasonCode.RETRIEVAL_FAILURE.value],
                risk_level="HIGH",
            )

        try:
            reply_result = self._generate_reply(
                message, intent_result, evidence, trace
            )
        except Exception as e:
            logger.error(f"Reply generation failed: {e}")
            trace.set_error(f"Reply generation failed: {e}")
            return self._build_escalation_response(
                request, trace, start_time,
                intent_result=intent_result,
                retrieval_result=retrieval_result,
                reason_codes=[ReasonCode.PROVIDER_ERROR.value],
                risk_level="HIGH",
            )

        try:
            grounding_result = self._verify_grounding(
                message, reply_result, evidence, trace
            )
        except Exception as e:
            logger.error(f"Grounding verification failed: {e}")
            trace.set_error(f"Grounding verification failed: {e}")
            return self._build_escalation_response(
                request, trace, start_time,
                intent_result=intent_result,
                retrieval_result=retrieval_result,
                reply_result=reply_result,
                reason_codes=[ReasonCode.GROUNDING_FAILURE.value],
                risk_level="HIGH",
            )

        try:
            escalation_decision = self._evaluate_escalation(
                intent_result, retrieval_result, reply_result, grounding_result, trace
            )
        except Exception as e:
            logger.error(f"Escalation evaluation failed: {e}")
            trace.set_error(f"Escalation evaluation failed: {e}")
            return self._build_escalation_response(
                request, trace, start_time,
                intent_result=intent_result,
                retrieval_result=retrieval_result,
                reply_result=reply_result,
                grounding_result=grounding_result,
                reason_codes=[ReasonCode.PROVIDER_ERROR.value],
                risk_level="HIGH",
            )

        if escalation_decision.decision == "AUTO_HANDLE":
            return self._build_auto_handle_response(
                request, trace, start_time,
                intent_result, retrieval_result, reply_result,
                grounding_result, escalation_decision,
            )
        else:
            return self._build_escalation_response(
                request, trace, start_time,
                intent_result=intent_result,
                retrieval_result=retrieval_result,
                reply_result=reply_result,
                grounding_result=grounding_result,
                escalation_decision=escalation_decision,
            )

    def _classify_intent(
        self, message: str, trace: AgentTrace
    ) -> dict[str, Any] | None:
        """Classify intent of the message."""
        if self.classifier is None:
            trace.set_error("No classifier available")
            return None

        try:
            import pandas as pd
            X = pd.Series([message])
            results = self.classifier.predict_with_confidence(X)
            if not results:
                trace.set_error("Classifier returned no results")
                return None

            result = results[0]
            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.0)
            probabilities = result.get("probabilities", {})

            trace.set_intent(intent, confidence)
            return {
                "intent": intent,
                "confidence": confidence,
                "probabilities": probabilities,
            }
        except Exception as e:
            trace.set_error(f"Intent classification error: {e}")
            return None

    def _retrieve_evidence(
        self,
        message: str,
        intent_result: dict[str, Any],
        trace: AgentTrace,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Retrieve historical evidence."""
        if self.retriever is None:
            trace.set_retrieval(0, None)
            return {"retrieval_status": "error", "results": []}, []

        try:
            retrieval_response = self.retriever.retrieve(
                query=message,
                top_k=5,
                intent=intent_result.get("intent"),
            )

            retrieval_result = {
                "retrieval_status": retrieval_response.retrieval_status,
                "results": [
                    {
                        "knowledge_id": r.knowledge_id,
                        "customer_message": r.customer_message,
                        "support_response": r.support_response,
                        "similarity_score": r.similarity_score,
                        "intent": r.intent,
                        "resolution_type": r.resolution_type,
                    }
                    for r in retrieval_response.results
                ],
                "top_similarity": (
                    retrieval_response.results[0].similarity_score
                    if retrieval_response.results
                    else None
                ),
            }

            evidence = [
                {
                    "knowledge_id": r.knowledge_id,
                    "conversation_id": r.conversation_id,
                    "source_message_id": r.source_message_id,
                    "customer_message": r.customer_message,
                    "support_response": r.support_response,
                    "similarity_score": r.similarity_score,
                    "intent": r.intent,
                    "resolution_type": r.resolution_type,
                }
                for r in retrieval_response.results
            ]

            count = len(retrieval_response.results)
            best_score = (
                retrieval_response.results[0].similarity_score
                if retrieval_response.results
                else None
            )
            trace.set_retrieval(count, best_score)

            return retrieval_result, evidence
        except Exception as e:
            trace.set_error(f"Retrieval error: {e}")
            return {"retrieval_status": "error", "results": []}, []

    def _generate_reply(
        self,
        message: str,
        intent_result: dict[str, Any],
        evidence: list[dict[str, Any]],
        trace: AgentTrace,
    ) -> dict[str, Any]:
        """Generate a grounded reply."""
        if self.generator is None:
            return {
                "status": "provider_error",
                "reply": None,
                "risk_flags": [],
                "generation_method": "mock",
            }

        try:
            selected_evidence = self.evidence_selector.select(evidence)
            if not selected_evidence:
                return {
                    "status": "insufficient_evidence",
                    "reply": None,
                    "risk_flags": [],
                    "generation_method": "grounded_llm",
                }

            reply_output: ReplyOutput = self.generator.generate(
                customer_message=message,
                predicted_intent=intent_result.get("intent"),
                intent_confidence=intent_result.get("confidence"),
                evidence=selected_evidence,
            )

            return {
                "status": reply_output.status,
                "reply": reply_output.reply,
                "risk_flags": reply_output.risk_flags,
                "generation_method": reply_output.generation_method,
                "evidence": [
                    {
                        "knowledge_id": e.knowledge_id,
                        "similarity_score": e.similarity_score,
                        "support_response": e.support_response,
                    }
                    for e in reply_output.evidence
                ],
                "metadata": reply_output.metadata,
            }
        except Exception as e:
            trace.set_error(f"Reply generation error: {e}")
            return {
                "status": "provider_error",
                "reply": None,
                "risk_flags": [],
                "generation_method": "error",
            }

    def _verify_grounding(
        self,
        message: str,
        reply_result: dict[str, Any],
        evidence: list[dict[str, Any]],
        trace: AgentTrace,
    ) -> dict[str, Any]:
        """Verify grounding of the generated reply."""
        reply_text = reply_result.get("reply")
        if not reply_text:
            trace.set_grounding("insufficient_evidence")
            return {
                "status": "insufficient_evidence",
                "grounding_score": 0.0,
                "risk_flags": [],
                "unsupported_claims": [],
            }

        try:
            check_result = run_grounding_checks(
                reply=reply_text,
                evidence=evidence,
                customer_message=message,
            )

            status = "pass" if check_result.passed else "fail"
            trace.set_grounding(status)

            return {
                "status": status,
                "grounding_score": 1.0 if check_result.passed else 0.0,
                "risk_flags": check_result.issues,
                "unsupported_claims": [
                    {"type": "unsupported", "claim": issue}
                    for issue in check_result.issues
                ],
                "checks": check_result.checks,
            }
        except Exception as e:
            trace.set_error(f"Grounding verification error: {e}")
            trace.set_grounding("error")
            return {
                "status": "fail",
                "grounding_score": 0.0,
                "risk_flags": [str(e)],
                "unsupported_claims": [],
            }

    def _evaluate_escalation(
        self,
        intent_result: dict[str, Any],
        retrieval_result: dict[str, Any],
        reply_result: dict[str, Any],
        grounding_result: dict[str, Any],
        trace: AgentTrace,
    ) -> Any:
        """Evaluate escalation decision."""
        try:
            decision = self.escalation_engine.evaluate(
                intent_result=intent_result,
                retrieval_result=retrieval_result,
                reply_result=reply_result,
                grounding_result=grounding_result,
            )
            trace.set_escalation(decision.decision, decision.reason_codes)
            return decision
        except Exception as e:
            trace.set_error(f"Escalation evaluation error: {e}")
            from src.escalation.escalation_schema import build_escalation_decision
            return build_escalation_decision(
                decision="ESCALATE_TO_HUMAN",
                reason_codes=[ReasonCode.PROVIDER_ERROR.value],
                risk_level="HIGH",
                policy_version=self.policy.policy_version,
            )

    def _build_auto_handle_response(
        self,
        request: AgentRequest,
        trace: AgentTrace,
        start_time: float,
        intent_result: dict[str, Any],
        retrieval_result: dict[str, Any],
        reply_result: dict[str, Any],
        grounding_result: dict[str, Any],
        escalation_decision: Any,
    ) -> AgentResponse:
        """Build an AUTO_HANDLE response."""
        latency_ms = (time.time() - start_time) * 1000
        trace.add_metadata("latency_ms", latency_ms)

        return build_agent_response(
            decision="AUTO_HANDLE",
            reply=reply_result.get("reply"),
            intent=intent_result.get("intent"),
            intent_confidence=intent_result.get("confidence"),
            evidence=retrieval_result.get("results", []),
            grounding_status=grounding_result.get("status"),
            escalation_decision=escalation_decision.decision,
            escalation_reason_codes=escalation_decision.reason_codes,
            escalation_risk_level=escalation_decision.risk_level,
            escalation_policy_version=escalation_decision.policy_version,
            escalation_recommended_action=escalation_decision.recommended_action,
            trace_id=trace.trace_id,
            metadata={
                "latency_ms": latency_ms,
                "policy_version": escalation_decision.policy_version,
            },
        )

    def _build_escalation_response(
        self,
        request: AgentRequest,
        trace: AgentTrace,
        start_time: float,
        intent_result: dict[str, Any] | None = None,
        retrieval_result: dict[str, Any] | None = None,
        reply_result: dict[str, Any] | None = None,
        grounding_result: dict[str, Any] | None = None,
        escalation_decision: Any = None,
        reason_codes: list[str] | None = None,
        risk_level: str = "MEDIUM",
    ) -> AgentResponse:
        """Build an ESCALATE_TO_HUMAN response."""
        latency_ms = (time.time() - start_time) * 1000
        trace.add_metadata("latency_ms", latency_ms)

        if escalation_decision is None:
            from src.escalation.escalation_schema import build_escalation_decision
            escalation_decision = build_escalation_decision(
                decision="ESCALATE_TO_HUMAN",
                reason_codes=reason_codes or [],
                risk_level=risk_level,
                policy_version=self.policy.policy_version,
            )

        evidence = retrieval_result.get("results", []) if retrieval_result else []
        draft_reply = reply_result.get("reply") if reply_result else None

        human_review = {
            "customer_message": request.message,
            "conversation_id": request.conversation_id,
            "predicted_intent": (
                intent_result.get("intent") if intent_result else None
            ),
            "intent_confidence": (
                intent_result.get("confidence") if intent_result else None
            ),
            "draft_reply": draft_reply,
            "grounding_status": (
                grounding_result.get("status") if grounding_result else None
            ),
            "escalation_reasons": escalation_decision.reason_codes,
            "risk_signals": escalation_decision.signals if hasattr(escalation_decision, 'signals') else {},
            "recommended_action": escalation_decision.recommended_action,
            "policy_version": escalation_decision.policy_version,
        }

        return build_agent_response(
            decision="ESCALATE_TO_HUMAN",
            reply=None,
            intent=intent_result.get("intent") if intent_result else None,
            intent_confidence=intent_result.get("confidence") if intent_result else None,
            evidence=evidence,
            grounding_status=grounding_result.get("status") if grounding_result else None,
            escalation_decision=escalation_decision.decision,
            escalation_reason_codes=escalation_decision.reason_codes,
            escalation_risk_level=escalation_decision.risk_level,
            escalation_policy_version=escalation_decision.policy_version,
            escalation_recommended_action=escalation_decision.recommended_action,
            human_review=human_review,
            trace_id=trace.trace_id,
            metadata={
                "latency_ms": latency_ms,
                "policy_version": escalation_decision.policy_version,
            },
        )

    def _build_error_response(
        self,
        request: AgentRequest,
        trace: AgentTrace,
        error_message: str,
        errors: list[Any],
    ) -> AgentResponse:
        """Build an error response for validation failures."""
        from src.escalation.escalation_schema import build_escalation_decision

        escalation = build_escalation_decision(
            decision="ESCALATE_TO_HUMAN",
            reason_codes=[ReasonCode.INVALID_REPLY.value],
            risk_level="HIGH",
            policy_version=self.policy.policy_version,
        )

        return build_agent_response(
            decision="ESCALATE_TO_HUMAN",
            reply=None,
            escalation_decision=escalation.decision,
            escalation_reason_codes=escalation.reason_codes,
            escalation_risk_level=escalation.risk_level,
            escalation_policy_version=escalation.policy_version,
            escalation_recommended_action="Input validation failed",
            trace_id=trace.trace_id,
            metadata={"error": error_message, "validation_errors": str(errors)},
        )

    def _create_mock_classifier(self) -> SemanticIntentClassifier:
        """Create a mock classifier for testing."""
        from unittest.mock import MagicMock
        import pandas as pd

        mock_classifier = MagicMock(spec=SemanticIntentClassifier)
        mock_classifier.predict_with_confidence.return_value = [
            {
                "intent": "order_status",
                "confidence": 0.85,
                "probabilities": {"order_status": 0.85, "general_inquiry": 0.15},
            }
        ]
        return mock_classifier

    def _create_mock_retriever(self) -> HistoricalSupportRetriever:
        """Create a mock retriever for testing."""
        from unittest.mock import MagicMock
        from src.retrieval.retrieval_schema import RetrievalResponse, RetrievalResult

        mock_retriever = MagicMock(spec=HistoricalSupportRetriever)
        mock_retriever.retrieve.return_value = RetrievalResponse(
            query="test",
            retrieval_status="success",
            results=[
                RetrievalResult(
                    rank=1,
                    knowledge_id="KB001",
                    customer_message="Where is my order?",
                    support_response="Your order is on the way.",
                    similarity_score=0.75,
                    intent="order_status",
                    resolution_type="information_provided",
                )
            ],
        )
        return mock_retriever

    def _create_mock_generator(self) -> GroundedReplyGenerator:
        """Create a mock generator for testing."""
        from unittest.mock import MagicMock
        from src.generation.reply_schema import build_reply_output

        mock_generator = MagicMock(spec=GroundedReplyGenerator)
        mock_generator.generate.return_value = build_reply_output(
            query="test",
            reply="Your order is on the way and should arrive soon.",
            generation_method="grounded_llm",
            status="success",
            predicted_intent="order_status",
            intent_confidence=0.85,
            evidence=[],
        )
        return mock_generator


def create_agent(
    mock_mode: bool = False,
    classifier: SemanticIntentClassifier | None = None,
    retriever: HistoricalSupportRetriever | None = None,
    generator: GroundedReplyGenerator | None = None,
    **kwargs: Any,
) -> SupportAgent:
    """Create a support agent with the given components.

    Args:
        mock_mode: If True, use mock components for testing.
        classifier: Intent classifier.
        retriever: Historical support retriever.
        generator: Grounded reply generator.
        **kwargs: Additional arguments for SupportAgent.

    Returns:
        SupportAgent instance.
    """
    return SupportAgent(
        classifier=classifier,
        retriever=retriever,
        generator=generator,
        mock_mode=mock_mode,
        **kwargs,
    )
