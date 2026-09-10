"""Tests for judge agreement dataset."""

import pytest
import json
import tempfile
import os


def create_test_dataset():
    """Create a test dataset."""
    return [
        {
            "query_id": "eval_0001",
            "judge_item_id": "eval_0001_A",
            "system_label": "A",
            "customer_message": "I want to return this item.",
            "intent": "return",
            "candidate_reply": "You can return within 30 days.",
            "human_scores": {
                "relevance": 4,
                "groundedness": 4,
                "correctness": 4,
                "helpfulness": 4,
                "completeness": 4,
                "style": 4,
                "overall": 4.0,
            },
            "llm_scores": {
                "relevance": 4,
                "groundedness": 4,
                "correctness": 4,
                "helpfulness": 4,
                "completeness": 4,
                "style": 4,
                "overall": 4.0,
            },
            "human_failure_tags": [],
            "llm_failure_tags": [],
            "difficulty": "easy",
        },
        {
            "query_id": "eval_0002",
            "judge_item_id": "eval_0002_B",
            "system_label": "B",
            "customer_message": "Where is my order?",
            "intent": "order_status",
            "candidate_reply": "Your order is on the way.",
            "human_scores": {
                "relevance": 3,
                "groundedness": 3,
                "correctness": 3,
                "helpfulness": 3,
                "completeness": 3,
                "style": 3,
                "overall": 3.0,
            },
            "llm_scores": {
                "relevance": 4,
                "groundedness": 3,
                "correctness": 4,
                "helpfulness": 4,
                "completeness": 3,
                "style": 4,
                "overall": 3.67,
            },
            "human_failure_tags": [],
            "llm_failure_tags": [],
            "difficulty": "medium",
        },
    ]


class TestJudgeAgreementDataset:
    """Tests for judge agreement dataset."""

    def test_dataset_creation(self):
        """Test that dataset can be created."""
        dataset = create_test_dataset()
        assert len(dataset) == 2
        assert dataset[0]["query_id"] == "eval_0001"

    def test_dataset_structure(self):
        """Test dataset has required fields."""
        dataset = create_test_dataset()
        for record in dataset:
            assert "query_id" in record
            assert "judge_item_id" in record
            assert "human_scores" in record
            assert "llm_scores" in record
            assert "overall" in record["human_scores"]
            assert "overall" in record["llm_scores"]

    def test_score_ranges(self):
        """Test that scores are in valid range."""
        dataset = create_test_dataset()
        for record in dataset:
            for dim in ["relevance", "groundedness", "correctness", "helpfulness", "completeness", "style"]:
                assert 1 <= record["human_scores"][dim] <= 5
                assert 1 <= record["llm_scores"][dim] <= 5
            assert 1.0 <= record["human_scores"]["overall"] <= 5.0
            assert 1.0 <= record["llm_scores"]["overall"] <= 5.0

    def test_no_duplicates(self):
        """Test that dataset has no duplicate query/system combinations."""
        dataset = create_test_dataset()
        combinations = [(r["query_id"], r["system_label"]) for r in dataset]
        assert len(combinations) == len(set(combinations))