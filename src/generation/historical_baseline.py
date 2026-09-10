"""Historical response reply baseline.

Returns the top-ranked historical support response as the candidate reply.
"""

from typing import Any

from src.generation.base_generator import BaseReplyGenerator
from src.generation.reply_schema import ReplyOutput, build_reply_output
from src.retrieval.retriever import HistoricalSupportRetriever


class HistoricalReplyGenerator(BaseReplyGenerator):
    """Historical baseline: returns the top historical support response."""

    def __init__(
        self,
        retriever: HistoricalSupportRetriever,
        top_k: int = 1,
        require_evidence: bool = True,
    ) -> None:
        self.retriever = retriever
        self.top_k = top_k
        self.require_evidence = require_evidence

    def generate(
        self,
        customer_message: str,
        context: list[dict[str, Any]] | None = None,
        intent: str | None = None,
        intent_confidence: float | None = None,
    ) -> ReplyOutput:
        retrieval_response = self.retriever.retrieve(
            query=customer_message,
            top_k=self.top_k,
            intent=intent,
        )

        if retrieval_response.retrieval_status != "success" or not retrieval_response.results:
            if self.require_evidence:
                return build_reply_output(
                    query=customer_message,
                    reply=None,
                    generation_method="historical_baseline",
                    status="insufficient_evidence",
                    predicted_intent=intent,
                    intent_confidence=intent_confidence,
                    evidence=[],
                    metadata={"retrieval_status": retrieval_response.retrieval_status},
                )

        top_result = retrieval_response.results[0]
        reply_text = top_result.support_response

        evidence_list = []
        for r in retrieval_response.results:
            evidence_list.append({
                "knowledge_id": r.knowledge_id,
                "conversation_id": r.conversation_id,
                "source_message_id": r.source_message_id,
                "similarity_score": r.similarity_score,
                "support_response": r.support_response,
                "intent": r.intent,
                "resolution_type": r.resolution_type,
            })

        return build_reply_output(
            query=customer_message,
            reply=reply_text,
            generation_method="historical_baseline",
            status="success",
            predicted_intent=intent,
            intent_confidence=intent_confidence,
            evidence=evidence_list,
            metadata={
                "retrieval_status": retrieval_response.retrieval_status,
                "top_k": self.top_k,
                "n_evidence": len(evidence_list),
            },
        )

    def get_params(self) -> dict[str, Any]:
        return {
            "generator": "HistoricalReplyGenerator",
            "top_k": self.top_k,
            "require_evidence": self.require_evidence,
        }
