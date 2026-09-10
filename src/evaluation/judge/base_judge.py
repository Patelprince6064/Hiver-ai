"""Base judge abstraction.

Defines the interface for all judge implementations.
"""

from abc import ABC, abstractmethod

from src.evaluation.judge_schema import JudgeInput, JudgeResult


class BaseJudge(ABC):
    """Abstract base class for judge implementations.

    All judges must implement the evaluate method.
    """

    @abstractmethod
    def evaluate(self, judge_input: JudgeInput) -> JudgeResult:
        """Evaluate a candidate reply.

        Args:
            judge_input: Structured input containing the reply and context.

        Returns:
            Structured evaluation result with scores and rationale.
        """
        pass

    def validate_input(self, judge_input: JudgeInput) -> bool:
        """Validate that input meets requirements.

        Args:
            judge_input: The input to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not judge_input.customer_message:
            return False
        if not judge_input.candidate_reply:
            return False
        if not judge_input.judge_item_id:
            return False
        return True