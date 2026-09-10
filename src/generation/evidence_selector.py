"""Evidence selector for grounded reply generation.

Selects, filters, and deduplicates evidence from retrieval results.
"""

from typing import Any


class EvidenceSelector:
    """Selects and filters evidence for LLM generation."""

    def __init__(
        self,
        max_evidence: int = 3,
        min_similarity: float | None = None,
        deduplicate: bool = True,
    ) -> None:
        self.max_evidence = max_evidence
        self.min_similarity = min_similarity
        self.deduplicate = deduplicate

    def select(
        self,
        retrieval_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Select evidence from retrieval results.

        Args:
            retrieval_results: Raw retrieval results from the retriever.

        Returns:
            Filtered and deduplicated evidence list.
        """
        candidates = []

        for result in retrieval_results:
            score = result.get("similarity_score", 0.0)

            if self.min_similarity is not None and score < self.min_similarity:
                continue

            quality_flags = result.get("quality_flags", [])
            if "empty_support_response" in quality_flags:
                continue

            support_response = result.get("support_response", "").strip()
            if not support_response:
                continue

            candidates.append(result)

        candidates.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        if self.deduplicate:
            candidates = self._deduplicate(candidates)

        return candidates[: self.max_evidence]

    def _deduplicate(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Remove near-duplicate evidence entries."""
        if not candidates:
            return []

        seen_responses: list[str] = []
        unique: list[dict[str, Any]] = []

        for c in candidates:
            response = c.get("support_response", "").strip().lower()
            if not response:
                continue

            if self._is_duplicate(response, seen_responses):
                continue

            seen_responses.append(response)
            unique.append(c)

        return unique

    def _is_duplicate(self, text: str, seen: list[str]) -> bool:
        """Check if text is a near-duplicate of any seen text."""
        for seen_text in seen:
            if self._text_overlap(text, seen_text) > 0.7:
                return True
        return False

    @staticmethod
    def _text_overlap(a: str, b: str) -> float:
        """Compute token overlap ratio between two texts."""
        tokens_a = set(a.split())
        tokens_b = set(b.split())
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union) if union else 0.0

    def get_params(self) -> dict[str, Any]:
        return {
            "max_evidence": self.max_evidence,
            "min_similarity": self.min_similarity,
            "deduplicate": self.deduplicate,
        }
