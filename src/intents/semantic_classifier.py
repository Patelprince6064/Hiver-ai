"""Semantic intent classifier using sentence-transformer embeddings.

Provides a reusable classifier that encodes text using sentence-transformers
and trains a Logistic Regression on the embeddings.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.evaluation.embedding_cache import load_cache, save_cache
from src.intents.base_classifier import BaseIntentClassifier
from src.intents.tfidf_baseline import preprocess_text


class SemanticIntentClassifier(BaseIntentClassifier):
    """Sentence-transformer + Logistic Regression intent classifier."""

    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings: bool = True,
        batch_size: int = 32,
        max_iter: int = 1000,
        class_weight: str | None = "balanced",
        random_state: int = 42,
        cache_dir: Path | None = None,
    ) -> None:
        self.embedding_model_name = embedding_model
        self.normalize_embeddings = normalize_embeddings
        self.batch_size = batch_size
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.random_state = random_state
        self.cache_dir = cache_dir

        self._encoder = None
        self._classifier: LogisticRegression | None = None
        self.classes_: list[str] = []

    def _get_encoder(self):
        """Lazy-load the sentence-transformer encoder."""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer(self.embedding_model_name)
        return self._encoder

    def _encode(self, texts: list[str], split_name: str = "unknown") -> np.ndarray:
        """Encode texts to embeddings, using cache if available."""
        if self.cache_dir is not None:
            cached = load_cache(
                self.cache_dir,
                split_name,
                self.embedding_model_name,
                self.normalize_embeddings,
                texts,
            )
            if cached is not None:
                return cached

        encoder = self._get_encoder()
        embeddings = encoder.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=True,
        )

        if self.cache_dir is not None:
            save_cache(
                embeddings,
                self.cache_dir,
                split_name,
                self.embedding_model_name,
                self.normalize_embeddings,
                texts,
            )

        return np.array(embeddings)

    def fit(self, X: pd.Series, y: pd.Series, split_name: str = "train") -> None:
        """Train the semantic classifier."""
        texts = [preprocess_text(t) for t in X.tolist()]
        self.classes_ = sorted(y.unique().tolist())

        embeddings = self._encode(texts, split_name=split_name)

        self._classifier = LogisticRegression(
            max_iter=self.max_iter,
            class_weight=self.class_weight,
            random_state=self.random_state,
            solver="lbfgs",
        )
        self._classifier.fit(embeddings, y.tolist())

    def predict(self, X: pd.Series) -> list[str]:
        """Predict intent labels."""
        if self._classifier is None:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")
        texts = [preprocess_text(t) for t in X.tolist()]
        embeddings = self._encode(texts, split_name="predict")
        return self._classifier.predict(embeddings).tolist()

    def predict_proba(self, X: pd.Series) -> list[dict[str, float]]:
        """Predict intent probabilities."""
        if self._classifier is None:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")
        texts = [preprocess_text(t) for t in X.tolist()]
        embeddings = self._encode(texts, split_name="predict")
        proba = self._classifier.predict_proba(embeddings)
        classes = self._classifier.classes_
        return [{cls: float(prob) for cls, prob in zip(classes, row)} for row in proba]

    def predict_with_confidence(self, X: pd.Series) -> list[dict]:
        """Predict with intent, confidence, and full probabilities."""
        proba = self.predict_proba(X)
        results = []
        for p in proba:
            intent = max(p, key=p.get)
            results.append({
                "intent": intent,
                "confidence": p[intent],
                "probabilities": p,
            })
        return results

    def save(self, save_dir: Path) -> None:
        """Save the trained classifier and metadata."""
        save_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self._classifier, save_dir / "classifier.joblib")

        metadata = {
            "embedding_model": self.embedding_model_name,
            "normalize_embeddings": self.normalize_embeddings,
            "batch_size": self.batch_size,
            "classifier_type": "logistic_regression",
            "max_iter": self.max_iter,
            "class_weight": self.class_weight,
            "random_state": self.random_state,
            "classes": self.classes_,
            "n_classes": len(self.classes_),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "preprocessing_version": "1.0",
        }

        with open(save_dir / "model_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load(cls, save_dir: Path) -> "SemanticIntentClassifier":
        """Load a saved classifier."""
        with open(save_dir / "model_metadata.json", "r") as f:
            metadata = json.load(f)

        clf = cls(
            embedding_model=metadata["embedding_model"],
            normalize_embeddings=metadata["normalize_embeddings"],
            batch_size=metadata["batch_size"],
            max_iter=metadata["max_iter"],
            class_weight=metadata["class_weight"],
            random_state=metadata["random_state"],
        )
        clf._classifier = joblib.load(save_dir / "classifier.joblib")
        clf.classes_ = metadata["classes"]
        return clf

    def get_params(self) -> dict:
        return {
            "embedding_model": self.embedding_model_name,
            "normalize_embeddings": self.normalize_embeddings,
            "batch_size": self.batch_size,
            "classifier_type": "logistic_regression",
            "max_iter": self.max_iter,
            "class_weight": self.class_weight,
            "random_state": self.random_state,
        }
