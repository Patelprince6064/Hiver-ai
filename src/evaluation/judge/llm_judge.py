"""LLM Judge implementation.

Evaluates reply quality using an LLM provider.
"""

import json
import re
from typing import Any

from src.evaluation.judge.base_judge import BaseJudge
from src.evaluation.judge.output_validator import validate_judge_output
from src.evaluation.judge_schema import JudgeInput, JudgeResult
from src.evaluation.llm_judge_prompt import build_judge_messages, validate_prompt_safety
from src.generation.llm.base_provider import BaseLLMProvider


class LLMJudge(BaseJudge):
    """Judge implementation that uses an LLM for evaluation.

    Uses the existing LLM provider abstraction for API calls.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        model: str = "unknown",
        temperature: float = 0.0,
        max_tokens: int = 1000,
        retries: int = 2,
    ) -> None:
        """Initialize the LLM judge.

        Args:
            provider: LLM provider instance.
            model: Model identifier for metadata.
            temperature: Sampling temperature (should be 0 for determinism).
            max_tokens: Maximum tokens for response.
            retries: Number of retries for invalid output.
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.retries = retries
        self._call_count = 0
        self._total_latency_ms = 0.0

    def evaluate(self, judge_input: JudgeInput) -> JudgeResult:
        """Evaluate a candidate reply using the LLM.

        Args:
            judge_input: Structured input for evaluation.

        Returns:
            Structured evaluation result.
        """
        if not self.validate_input(judge_input):
            return JudgeResult(
                judge_item_id=judge_input.judge_item_id,
                relevance=1,
                groundedness=1,
                correctness=1,
                helpfulness=1,
                completeness=1,
                style=1,
                overall=1.0,
                failure_tags=["other"],
                short_rationale="Invalid input provided.",
                judge_status="ERROR",
                judge_model=self.model,
            )

        # Build messages
        messages = build_judge_messages(judge_input)

        # Validate prompt safety
        is_safe, violations = validate_prompt_safety(messages[1]["content"])
        if not is_safe:
            return JudgeResult(
                judge_item_id=judge_input.judge_item_id,
                relevance=1,
                groundedness=1,
                correctness=1,
                helpfulness=1,
                completeness=1,
                style=1,
                overall=1.0,
                failure_tags=["other"],
                short_rationale=f"Prompt safety violation: {', '.join(violations)}",
                judge_status="ERROR",
                judge_model=self.model,
            )

        # Attempt evaluation with retries
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                response = self.provider.generate(
                    prompt=messages[1]["content"],
                    system_prompt=messages[0]["content"],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                self._call_count += 1
                self._total_latency_ms += response.latency_ms

                if response.status != "success":
                    last_error = f"Provider error: {response.error_message}"
                    continue

                # Parse and validate output
                result = self._parse_output(judge_input.judge_item_id, response.text)
                if result.judge_status == "SUCCESS":
                    return result

                last_error = f"Invalid output: {result.short_rationale}"

            except Exception as e:
                last_error = str(e)
                continue

        # All retries failed
        return JudgeResult(
            judge_item_id=judge_input.judge_item_id,
            relevance=1,
            groundedness=1,
            correctness=1,
            helpfulness=1,
            completeness=1,
            style=1,
            overall=1.0,
            failure_tags=["other"],
            short_rationale=f"Evaluation failed after {self.retries + 1} attempts: {last_error}",
            judge_status="INVALID_OUTPUT",
            judge_model=self.model,
        )

    def _parse_output(self, judge_item_id: str, output: str) -> JudgeResult:
        """Parse LLM output into JudgeResult.

        Args:
            judge_item_id: The ID of the item being evaluated.
            output: Raw LLM output.

        Returns:
            Parsed JudgeResult or error result.
        """
        try:
            # Try to extract JSON from output
            # Look for JSON block in markdown code fence or raw JSON
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return JudgeResult(
                        judge_item_id=judge_item_id,
                        relevance=1,
                        groundedness=1,
                        correctness=1,
                        helpfulness=1,
                        completeness=1,
                        style=1,
                        overall=1.0,
                        failure_tags=["other"],
                        short_rationale="No JSON found in output.",
                        judge_status="INVALID_OUTPUT",
                        judge_model=self.model,
                    )

            data = json.loads(json_str)

            # Validate and create result
            is_valid, errors = validate_judge_output(data)
            if not is_valid:
                return JudgeResult(
                    judge_item_id=judge_item_id,
                    relevance=1,
                    groundedness=1,
                    correctness=1,
                    helpfulness=1,
                    completeness=1,
                    style=1,
                    overall=1.0,
                    failure_tags=["other"],
                    short_rationale=f"Validation errors: {', '.join(errors)}",
                    judge_status="INVALID_OUTPUT",
                    judge_model=self.model,
                )

            # Create result with locally calculated overall score
            result = JudgeResult(
                judge_item_id=judge_item_id,
                relevance=data["relevance"],
                groundedness=data["groundedness"],
                correctness=data["correctness"],
                helpfulness=data["helpfulness"],
                completeness=data["completeness"],
                style=data["style"],
                overall=0.0,  # Will be calculated
                failure_tags=data.get("failure_tags", []),
                short_rationale=data.get("short_rationale", ""),
                judge_status="SUCCESS",
                judge_model=self.model,
            )

            # Use locally calculated overall score
            result.overall = result.computed_overall

            return result

        except json.JSONDecodeError as e:
            return JudgeResult(
                judge_item_id=judge_item_id,
                relevance=1,
                groundedness=1,
                correctness=1,
                helpfulness=1,
                completeness=1,
                style=1,
                overall=1.0,
                failure_tags=["other"],
                short_rationale=f"JSON parse error: {str(e)}",
                judge_status="INVALID_OUTPUT",
                judge_model=self.model,
            )

    def get_stats(self) -> dict[str, Any]:
        """Return judge statistics."""
        return {
            "model": self.model,
            "call_count": self._call_count,
            "total_latency_ms": self._total_latency_ms,
            "avg_latency_ms": self._total_latency_ms / max(self._call_count, 1),
        }