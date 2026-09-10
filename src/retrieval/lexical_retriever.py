"""Lexical retriever using TF-IDF.

Provides a baseline retrieval method for comparison with semantic retrieval.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.intents.tfidf_baseline import preprocess_text


class LexicalRetriever:
    """TF-IDF based lexical retriever."""

    def __init__(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        min_df: int = 1,
        max_df: float = 0.95,
    ) -> None:
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        self._vectorizer = None
        self._document_matrix = None
        self._record_mapping: list[str] = []
        self._records: list[dict] = []

    def fit(self, records: list[dict]) -> None:
        """Fit the TF-IDF vectorizer on knowledge base records."""
        self._records = records
        self._record_mapping = [r.get("knowledge_id", "") for r in records]

        texts = [preprocess_text(r.get("resolution_text", "")) for r in records]

        self._vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            min_df=self.min_df,
            max_df=self.max_df,
            sublinear_tf=True,
        )
        self._document_matrix = self._vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Search for similar documents using TF-IDF."""
        if self._vectorizer is None or self._document_matrix is None:
            raise RuntimeError("Retriever has not been fitted. Call fit() first.")

        query_processed = preprocess_text(query)
        query_vector = self._vectorizer.transform([query_processed])
        similarities = cosine_similarity(query_vector, self._document_matrix).flatten()

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                knowledge_id = self._record_mapping[idx]
                results.append((knowledge_id, float(similarities[idx])))

        return results

    def save(self, save_dir: Path) -> None:
        """Save the retriever to disk."""
        import joblib

        save_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._vectorizer, save_dir / "tfidf_vectorizer.joblib")

        with open(save_dir / "record_mapping.json", "w") as f:
            json.dump(self._record_mapping, f)

    def load(self, save_dir: Path) -> None:
        """Load the retriever from disk."""
        import joblib

        self._vectorizer = joblib.load(save_dir / "tfidf_vectorizer.joblib")

        with open(save_dir / "record_mapping.json", "r") as f:
            self._record_mapping = json.load(f)
