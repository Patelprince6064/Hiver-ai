"""Tests for agent batch processing."""

import json
import pytest
from pathlib import Path

from src.agent.agent_schema import AgentRequest
from src.agent.support_agent import create_agent


class TestAgentBatch:
    def test_batch_processing(self, tmp_path):
        input_file = tmp_path / "requests.jsonl"
        output_file = tmp_path / "outputs.jsonl"

        requests = [
            {"message": "Where is my order?"},
            {"message": "I want to return an item"},
            {"message": "How do I reset my password?"},
        ]

        with open(input_file, "w") as f:
            for req in requests:
                f.write(json.dumps(req) + "\n")

        agent = create_agent(mock_mode=True)

        with open(input_file, "r") as fin, open(output_file, "w") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                request_data = json.loads(line)
                request = AgentRequest(message=request_data["message"])
                response = agent.process(request)
                fout.write(json.dumps({
                    "decision": response.decision,
                    "intent": response.intent,
                }) + "\n")

        with open(output_file, "r") as f:
            outputs = [json.loads(line) for line in f if line.strip()]

        assert len(outputs) == 3
        assert all(o["decision"] in ("AUTO_HANDLE", "ESCALATE_TO_HUMAN") for o in outputs)

    def test_batch_handles_individual_failures(self, tmp_path):
        input_file = tmp_path / "requests.jsonl"
        output_file = tmp_path / "outputs.jsonl"

        requests = [
            {"message": "valid message"},
            {"message": ""},  # Invalid
            {"message": "another valid message"},
        ]

        with open(input_file, "w") as f:
            for req in requests:
                f.write(json.dumps(req) + "\n")

        agent = create_agent(mock_mode=True)
        errors = 0
        success = 0

        with open(input_file, "r") as fin, open(output_file, "w") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                try:
                    request_data = json.loads(line)
                    request = AgentRequest(message=request_data["message"])
                    response = agent.process(request)
                    fout.write(json.dumps({"decision": response.decision}) + "\n")
                    success += 1
                except Exception:
                    errors += 1

        assert success == 3  # All processed (empty message escalates, not crashes)
        assert errors == 0

    def test_batch_empty_input(self, tmp_path):
        input_file = tmp_path / "empty.jsonl"
        output_file = tmp_path / "outputs.jsonl"

        input_file.write_text("")

        agent = create_agent(mock_mode=True)
        count = 0

        with open(input_file, "r") as fin, open(output_file, "w") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                count += 1

        assert count == 0
