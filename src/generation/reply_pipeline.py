"""Reply generation pipeline.

Orchestrates intent classification -> retrieval -> reply generation.
Supports generic, historical, and grounded LLM generation methods.
"""

from pathlib import Path
from typing import Any

from src.generation.base_generator import BaseReplyGenerator
from src.generation.generic_baseline import GenericReplyGenerator
from src.generation.historical_baseline import HistoricalReplyGenerator
from src.generation.reply_schema import ReplyOutput, build_reply_output
from src.generation.safety_filters import analyze_reply_safety
from src.retrieval.retriever import HistoricalSupportRetriever


class ReplyPipeline:
    """Pipeline: classify intent -> retrieve history -> generate reply."""

    def __init__(
        self,
        retriever: HistoricalSupportRetriever,
        generator: BaseReplyGenerator | None = None,
        generic_fallback: bool = True,
        detect_safety: bool = True,
    ) -> None:
        self.retriever = retriever
        self.generator = generator or HistoricalReplyGenerator(retriever=retriever)
        self.generic_fallback = generic_fallback
        self.detect_safety = detect_safety
        self._generic = GenericReplyGenerator()

    def generate(
        self,
        customer_message: str,
        context: list[dict[str, Any]] | None = None,
        intent: str | None = None,
        intent_confidence: float | None = None,
    ) -> ReplyOutput:
        result = self.generator.generate(
            customer_message=customer_message,
            context=context,
            intent=intent,
            intent_confidence=intent_confidence,
        )

        if result.status == "insufficient_evidence" and self.generic_fallback:
            generic_result = self._generic.generate(
                customer_message=customer_message,
                context=context,
                intent=intent,
                intent_confidence=intent_confidence,
            )
            generic_result.metadata["fallback_from"] = result.generation_method
            generic_result.metadata["original_status"] = "insufficient_evidence"
            result = generic_result

        if self.detect_safety and result.reply:
            safety = analyze_reply_safety(result.reply)
            result.risk_flags = safety.flags

        return result

    def generate_grounded(
        self,
        customer_message: str,
        predicted_intent: str | None = None,
        intent_confidence: float | None = None,
    ) -> ReplyOutput:
        """Generate using grounded LLM (requires GroundedReplyGenerator).

        This method exists so the pipeline can dispatch to the grounded generator
        without circular imports at module level.
        """
        from src.generation.grounded_reply_generator import GroundedReplyGenerator

        if isinstance(self.generator, GroundedReplyGenerator):
            return self.generate(
                customer_message=customer_message,
                intent=predicted_intent,
                intent_confidence=intent_confidence,
            )

        return build_reply_output(
            query=customer_message,
            reply=None,
            generation_method="grounded_llm",
            status="error",
            predicted_intent=predicted_intent,
            intent_confidence=intent_confidence,
            metadata={"error": "GroundedReplyGenerator not configured"},
        )
