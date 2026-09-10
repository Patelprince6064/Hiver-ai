"""Base classifier interface for intent classification.

Defines a simple interface for baseline and future classifiers.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseIntentClassifier(ABC):
    """Abstract base class for intent classifiers."""

    @abstractmethod
    def fit(self, X: pd.Series, y: pd.Series) -> None:
        """Train the classifier.

        Args:
            X: Customer messages.
            y: Intent labels.
        """
        ...

    @abstractmethod
    def predict(self, X: pd.Series) -> list[str]:
        """Predict intent labels.

        Args:
            X: Customer messages.

        Returns:
            List of predicted intent labels.
        """
        ...

    @abstractmethod
    def predict_proba(self, X: pd.Series) -> list[dict[str, float]]:
        """Predict intent probabilities.

        Args:
            X: Customer messages.

        Returns:
            List of dicts mapping intent labels to probabilities.
        """
        ...

    def get_params(self) -> dict:
        """Get classifier parameters."""
        return {}
