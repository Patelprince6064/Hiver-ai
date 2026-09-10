"""Grounded reply generator using LLM with historical evidence.

The generator retrieves evidence, builds a prompt, calls the LLM,
and validates the output.
"""

import json
import time
from typing import Any

from src.generation.context_budget import ContextBudget
from src.generation.evidence_selector import EvidenceSelector
from src.generation.llm.base_provider import BaseLLMProvider, LLMResponse
from src.generation.output_validator import OutputValidator
from src.generation.prompt_builder import GroundedReplyPromptBuilder
from src.generation.reply_schema import ReplyOutput, build_reply_output
from src.retrieval.retriever import HistoricalSupportRetriever


class GroundedReplyGenerator:
    """Generates grounded replies using LLM + historical evidence."""

    def __init__(
        self,
        retriever: HistoricalSupportRetriever,
        llm_provider: BaseLLMProvider,
        evidence_selector: EvidenceSelector | None = None,
        prompt_builder: GroundedReplyPromptBuilder | None = None,
        output_validator: OutputValidator | None = None,
        context_budget: ContextBudget | None = None,
        temperature: float = 0.0,
        max_tokens: int = 300,
        prompt_version: str = "v1",
    ) -> None:
        self.retriever = retriever
        self.llm_provider = llm_provider
        self.evidence_selector = evidence_selector or EvidenceSelector()
        self.prompt_builder = prompt_builder or GroundedReplyPromptBuilder()
        self.output_validator = output_validator or OutputValidator()
        self.context_budget = context_budget or ContextBudget()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_version = prompt_version

    def generate(
        self,
        customer_message: str,
        predicted_intent: str | None = None,
        intent_confidence: float | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> ReplyOutput:
        """Generate a grounded reply.

        Args:
            customer_message: The customer's message.
            predicted_intent: Classified intent.
            intent_confidence: Intent confidence.
            evidence: Optional pre-fetched evidence. If None, retrieves.

        Returns:
            ReplyOutput with the grounded reply.
        """
        start_time = time.time()

        if evidence is None:
            retrieval = self.retriever.retrieve(
                query=customer_message,
                top_k=self.evidence_selector.max_evidence * 2,
                intent=predicted_intent,
            )
            if retrieval.retrieval_status != "success":
                return build_reply_output(
                    query=customer_message,
                    reply=None,
                    generation_method="grounded_llm",
                    status="insufficient_evidence",
                    predicted_intent=predicted_intent,
                    intent_confidence=intent_confidence,
                    evidence=[],
                    metadata={
                        "retrieval_status": retrieval.retrieval_status,
                        "prompt_version": self.prompt_version,
                    },
                )
            raw_evidence = []
            for r in retrieval.results:
                raw_evidence.append({
                    "knowledge_id": r.knowledge_id,
                    "conversation_id": r.conversation_id,
                    "source_message_id": r.source_message_id,
                    "customer_message": r.customer_message,
                    "support_response": r.support_response,
                    "similarity_score": r.similarity_score,
                    "intent": r.intent,
                    "resolution_type": r.resolution_type,
                    "quality_flags": r.quality_flags,
                })
        else:
            raw_evidence = evidence

        selected_evidence = self.evidence_selector.select(raw_evidence)

        if not selected_evidence:
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="grounded_llm",
                status="insufficient_evidence",
                predicted_intent=predicted_intent,
                intent_confidence=intent_confidence,
                evidence=[],
                metadata={
                    "prompt_version": self.prompt_version,
                    "n_raw_evidence": len(raw_evidence),
                    "n_selected_evidence": 0,
                },
            )

        fitted_evidence = self.context_budget.fit_evidence(selected_evidence)
        fitted_message = self.context_budget.fit_customer_message(customer_message)

        prompt = self.prompt_builder.build(
            customer_message=fitted_message,
            predicted_intent=predicted_intent,
            intent_confidence=intent_confidence,
            evidence=fitted_evidence,
        )

        system_prompt = self.prompt_builder.get_system_prompt()

        llm_response: LLMResponse = self.llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        if llm_response.status != "success":
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="grounded_llm",
                status="provider_error",
                predicted_intent=predicted_intent,
                intent_confidence=intent_confidence,
                evidence=self._evidence_for_output(fitted_evidence),
                metadata={
                    "prompt_version": self.prompt_version,
                    "error_type": llm_response.error_type,
                    "error_message": llm_response.error_message,
                    "latency_ms": llm_response.latency_ms,
                },
            )

        raw_text = llm_response.text.strip()

        validation = self.output_validator.validate(
            raw_output=raw_text,
            evidence_ids=[e.get("knowledge_id", "") for e in fitted_evidence],
            customer_message=customer_message,
        )

        if validation.status == "insufficient_evidence":
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="grounded_llm",
                status="insufficient_evidence",
                predicted_intent=predicted_intent,
                intent_confidence=intent_confidence,
                evidence=self._evidence_for_output(fitted_evidence),
                metadata={
                    "prompt_version": self.prompt_version,
                    "latency_ms": llm_response.latency_ms,
                    "usage": llm_response.usage,
                },
            )

        if not validation.is_valid:
            return build_reply_output(
                query=customer_message,
                reply=None,
                generation_method="grounded_llm",
                status="invalid_output",
                predicted_intent=predicted_intent,
                intent_confidence=intent_confidence,
                evidence=self._evidence_for_output(fitted_evidence),
                metadata={
                    "prompt_version": self.prompt_version,
                    "validation_errors": validation.errors,
                    "validation_warnings": validation.warnings,
                    "latency_ms": llm_response.latency_ms,
                },
            )

        latency_ms = (time.time() - start_time) * 1000

        return build_reply_output(
            query=customer_message,
            reply=raw_text,
            generation_method="grounded_llm",
            status="success",
            predicted_intent=predicted_intent,
            intent_confidence=intent_confidence,
            evidence=self._evidence_for_output(fitted_evidence),
            risk_flags=[],
            metadata={
                "prompt_version": self.prompt_version,
                "model": llm_response.model,
                "usage": llm_response.usage,
                "latency_ms": latency_ms,
                "validation_warnings": validation.warnings,
                "n_evidence_used": len(fitted_evidence),
            },
        )

    @staticmethod
    def _evidence_for_output(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format evidence for output."""
        return [
            {
                "knowledge_id": e.get("knowledge_id", ""),
                "similarity_score": e.get("similarity_score", 0.0),
                "support_response": e.get("support_response", ""),
                "intent": e.get("intent"),
                "resolution_type": e.get("resolution_type"),
            }
            for e in evidence
        ]

    def get_params(self) -> dict[str, Any]:
        return {
            "generator": "GroundedReplyGenerator",
            "llm_provider": self.llm_provider.get_params(),
            "evidence_selector": self.evidence_selector.get_params(),
            "output_validator": self.output_validator.get_params(),
            "context_budget": self.context_budget.get_params(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "prompt_version": self.prompt_version,
        }
