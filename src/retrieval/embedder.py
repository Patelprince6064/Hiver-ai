"""Embedder for semantic retrieval.

Provides embedding generation using sentence-transformers.
"""

import numpy as np
from pathlib import Path


class RetrieverEmbedder:
    """Sentence-transformer embedder for retrieval."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        normalize: bool = True,
        batch_size: int = 32,
    ) -> None:
        self.model_name = model_name
        self.normalize = normalize
        self.batch_size = batch_size
        self._model = None

    def _get_model(self):
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        """Encode a list of documents to embeddings."""
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=True,
        )
        return np.array(embeddings)

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single query to embedding."""
        model = self._get_model()
        embedding = model.encode(
            [query],
            normalize_embeddings=self.normalize,
        )
        return np.array(embedding[0])

    def get_embedding_dim(self) -> int:
        """Get the embedding dimension."""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()
