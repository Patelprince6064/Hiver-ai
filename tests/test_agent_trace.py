"""Tests for agent trace."""

import pytest
from src.agent.trace import AgentTrace, create_trace


class TestAgentTrace:
    def test_create_trace(self):
        trace = create_trace()
        assert trace.trace_id is not None
        assert len(trace.trace_id) > 0

    def test_trace_to_dict(self):
        trace = create_trace()
        trace.set_intent("order_status", 0.85)
        trace.set_retrieval(3, 0.75)
        trace.set_grounding("pass")
        trace.set_escalation("AUTO_HANDLE", [])

        d = trace.to_dict()
        assert d["intent"] == "order_status"
        assert d["intent_confidence"] == 0.85
        assert d["retrieval_count"] == 3
        assert d["best_retrieval_score"] == 0.75
        assert d["grounding_status"] == "pass"
        assert d["escalation_decision"] == "AUTO_HANDLE"

    def test_trace_set_error(self):
        trace = create_trace()
        trace.set_error("Something went wrong")
        assert trace.error == "Something went wrong"
        d = trace.to_dict()
        assert d["error"] == "Something went wrong"

    def test_trace_add_metadata(self):
        trace = create_trace()
        trace.add_metadata("latency_ms", 150.0)
        assert trace.metadata["latency_ms"] == 150.0

    def test_trace_no_secrets(self):
        trace = create_trace()
        trace.add_metadata("api_key", "secret_key_123")
        trace.add_metadata("prompt", "system prompt text")
        d = trace.to_dict()
        # Secrets should be in metadata (trace is for debugging only)
        # but should not be in the top-level fields
        assert "api_key" not in d
        assert "prompt" not in d

    def test_trace_unique_ids(self):
        trace1 = create_trace()
        trace2 = create_trace()
        assert trace1.trace_id != trace2.trace_id
