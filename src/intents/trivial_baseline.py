"""Trivial baseline: Majority class classifier."""

from collections import Counter

import pandas as pd

from src.intents.base_classifier import BaseIntentClassifier


class MajorityClassClassifier(BaseIntentClassifier):
    """Always predicts the most frequent intent from training data."""

    def __init__(self) -> None:
        self.majority_label: str | None = None
        self.majority_proportion: float = 0.0
        self.classes_: list[str] = []
        self._class_counts: dict[str, int] = {}

    def fit(self, X: pd.Series, y: pd.Series) -> None:
        """Identify the majority class from training labels."""
        counts = Counter(y)
        self._class_counts = dict(counts)
        self.classes_ = sorted(counts.keys())
        self.majority_label = counts.most_common(1)[0][0]
        self.majority_proportion = counts[self.majority_label] / len(y)

    def predict(self, X: pd.Series) -> list[str]:
        """Always predict the majority class."""
        if self.majority_label is None:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")
        return [self.majority_label] * len(X)

    def predict_proba(self, X: pd.Series) -> list[dict[str, float]]:
        """Return majority class proportion as confidence."""
        if self.majority_label is None:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")
        proba = {label: 0.0 for label in self.classes_}
        proba[self.majority_label] = self.majority_proportion
        return [proba.copy() for _ in range(len(X))]

    def get_params(self) -> dict:
        return {
            "majority_label": self.majority_label,
            "majority_proportion": self.majority_proportion,
            "n_classes": len(self.classes_),
        }
