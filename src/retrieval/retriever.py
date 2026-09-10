"""Semantic retriever for historical support examples.

Provides the main retrieval interface combining vector search with filtering.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.retrieval.embedder import RetrieverEmbedder
from src.retrieval.vector_index import VectorIndex
from src.retrieval.retrieval_schema import build_retrieval_response, RetrievalResponse


class HistoricalSupportRetriever:
    """Semantic retriever for historical support examples."""

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings: bool = True,
        default_top_k: int = 5,
        min_similarity: float | None = None,
        intent_reranking: bool = False,
        intent_boost: float = 0.0,
        intent_confidence_threshold: float = 0.80,
    ) -> None:
        self.embedding_model = embedding_model
        self.normalize_embeddings = normalize_embeddings
        self.default_top_k = default_top_k
        self.min_similarity = min_similarity
        self.intent_reranking = intent_reranking
        self.intent_boost = intent_boost
        self.intent_confidence_threshold = intent_confidence_threshold

        self._embedder = RetrieverEmbedder(
            model_name=embedding_model,
            normalize=normalize_embeddings,
        )
        self._index = VectorIndex(
            dimension=384,  # Will be set on load
            metric="cosine",
        )
        self._records: dict[str, dict] = {}
        self._loaded = False

    def load(self, index_dir: Path) -> None:
        """Load the retrieval index and records."""
        self._index.load(index_dir)

        # Load record mapping
        records_path = index_dir / "records.jsonl"
        if records_path.exists():
            self._records = {}
            with open(records_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        record = json.loads(line)
                        kid = record.get("knowledge_id", "")
                        if kid:
                            self._records[kid] = record

        self._loaded = True

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        intent: str | None = None,
        min_similarity: float | None = None,
    ) -> RetrievalResponse:
        """Retrieve relevant historical support examples.

        Args:
            query: Customer message query
            top_k: Number of results to return
            intent: Optional intent for filtering/reranking
            min_similarity: Minimum similarity threshold

        Returns:
            RetrievalResponse with ranked results
        """
        if not self._loaded:
            raise RuntimeError("Index not loaded. Call load() first.")

        top_k = top_k or self.default_top_k
        min_sim = min_similarity if min_similarity is not None else self.min_similarity

        # Get query intent if not provided
        predicted_intent = intent
        intent_confidence = None

        # Encode query
        query_embedding = self._embedder.encode_query(query)

        # Search index
        candidate_k = max(top_k * 4, 20)
        raw_results = self._index.search(query_embedding, top_k=candidate_k)

        # Build results with metadata
        results = []
        for knowledge_id, score in raw_results:
            record = self._records.get(knowledge_id, {})

            # Apply quality filter
            quality_flags = record.get("quality_flags", [])
            if "empty_customer_message" in quality_flags or "empty_support_response" in quality_flags:
                continue

            # Apply similarity threshold
            if min_sim is not None and score < min_sim:
                continue

            results.append({
                "knowledge_id": knowledge_id,
                "conversation_id": record.get("conversation_id"),
                "source_message_id": record.get("source_message_id"),
                "customer_message": record.get("customer_message", ""),
                "support_response": record.get("support_response", ""),
                "intent": record.get("intent"),
                "resolution_type": record.get("resolution_type"),
                "similarity_score": score,
                "quality_flags": quality_flags,
                "quality_category": record.get("quality_category", "usable"),
            })

        # Intent-aware reranking
        if self.intent_reranking and intent and results:
            for r in results:
                if r.get("intent") == intent:
                    r["similarity_score"] += self.intent_boost
            results.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Take top-k
        results = results[:top_k]

        # Build response
        return build_retrieval_response(
            query=query,
            results=results,
            predicted_intent=predicted_intent,
            intent_confidence=intent_confidence,
            top_k=top_k,
            retrieval_mode="semantic",
        )
