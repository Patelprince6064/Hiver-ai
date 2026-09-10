"""TF-IDF + Logistic Regression baseline for intent classification."""

import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.intents.base_classifier import BaseIntentClassifier


def preprocess_text(text: str) -> str:
    """Simple preprocessing for TF-IDF baseline.

    Lowercases, normalizes URLs and mentions.
    Preserves spelling, slang, punctuation, emojis.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+", "URL", text)
    text = re.sub(r"@\w+", "MENTION", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TfidfLogisticRegressionClassifier(BaseIntentClassifier):
    """TF-IDF + Logistic Regression pipeline for intent classification."""

    def __init__(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        min_df: int = 2,
        max_df: float = 0.95,
        sublinear_tf: bool = True,
        max_iter: int = 1000,
        class_weight: str | None = "balanced",
        random_state: int = 42,
    ) -> None:
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        self.sublinear_tf = sublinear_tf
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.random_state = random_state

        self._pipeline: Pipeline | None = None
        self.classes_: list[str] = []

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=self.ngram_range,
                min_df=self.min_df,
                max_df=self.max_df,
                sublinear_tf=self.sublinear_tf,
                preprocessor=preprocess_text,
            )),
            ("clf", LogisticRegression(
                max_iter=self.max_iter,
                class_weight=self.class_weight,
                random_state=self.random_state,
                solver="lbfgs",
            )),
        ])

    def fit(self, X: pd.Series, y: pd.Series) -> None:
        """Train TF-IDF + Logistic Regression."""
        self._pipeline = self._build_pipeline()
        self.classes_ = sorted(y.unique().tolist())
        self._pipeline.fit(X, y)

    def predict(self, X: pd.Series) -> list[str]:
        """Predict intent labels."""
        if self._pipeline is None:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")
        return self._pipeline.predict(X).tolist()

    def predict_proba(self, X: pd.Series) -> list[dict[str, float]]:
        """Predict intent probabilities."""
        if self._pipeline is None:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        proba_array = self._pipeline.predict_proba(X)
        classes = self._pipeline.named_steps["clf"].classes_

        results = []
        for row in proba_array:
            results.append({cls: float(prob) for cls, prob in zip(classes, row)})
        return results

    def get_params(self) -> dict:
        return {
            "ngram_range": list(self.ngram_range),
            "min_df": self.min_df,
            "max_df": self.max_df,
            "sublinear_tf": self.sublinear_tf,
            "max_iter": self.max_iter,
            "class_weight": self.class_weight,
            "random_state": self.random_state,
        }
