"""Tests for evidence selector."""

import pytest
from src.generation.evidence_selector import EvidenceSelector


class TestEvidenceSelector:
    def test_select_top_k(self):
        selector = EvidenceSelector(max_evidence=2)
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "A"},
            {"knowledge_id": "kb_002", "similarity_score": 0.8, "support_response": "B"},
            {"knowledge_id": "kb_003", "similarity_score": 0.7, "support_response": "C"},
        ]
        selected = selector.select(evidence)
        assert len(selected) == 2
        assert selected[0]["knowledge_id"] == "kb_001"
        assert selected[1]["knowledge_id"] == "kb_002"

    def test_select_filters_empty_response(self):
        selector = EvidenceSelector(max_evidence=5)
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "A"},
            {"knowledge_id": "kb_002", "similarity_score": 0.8, "support_response": ""},
            {"knowledge_id": "kb_003", "similarity_score": 0.7, "support_response": "  "},
        ]
        selected = selector.select(evidence)
        assert len(selected) == 1
        assert selected[0]["knowledge_id"] == "kb_001"

    def test_select_filters_low_similarity(self):
        selector = EvidenceSelector(max_evidence=5, min_similarity=0.8)
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "A"},
            {"knowledge_id": "kb_002", "similarity_score": 0.7, "support_response": "B"},
        ]
        selected = selector.select(evidence)
        assert len(selected) == 1

    def test_select_deduplicates(self):
        selector = EvidenceSelector(max_evidence=5, deduplicate=True)
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "Please DM us your order number and we will look into this for you right away."},
            {"knowledge_id": "kb_002", "similarity_score": 0.85, "support_response": "Please DM us your order number and we will look into this for you right away."},
            {"knowledge_id": "kb_003", "similarity_score": 0.8, "support_response": "Please DM us your order number and we will look into this for you right away."},
        ]
        selected = selector.select(evidence)
        assert len(selected) == 1

    def test_select_empty_input(self):
        selector = EvidenceSelector(max_evidence=3)
        selected = selector.select([])
        assert selected == []

    def test_select_no_dedup(self):
        selector = EvidenceSelector(max_evidence=5, deduplicate=False)
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "Hello"},
            {"knowledge_id": "kb_002", "similarity_score": 0.85, "support_response": "Hello there"},
        ]
        selected = selector.select(evidence)
        assert len(selected) == 2

    def test_select_filters_quality_flags(self):
        selector = EvidenceSelector(max_evidence=5)
        evidence = [
            {"knowledge_id": "kb_001", "similarity_score": 0.9, "support_response": "A", "quality_flags": []},
            {"knowledge_id": "kb_002", "similarity_score": 0.8, "support_response": "B", "quality_flags": ["empty_support_response"]},
        ]
        selected = selector.select(evidence)
        assert len(selected) == 1
        assert selected[0]["knowledge_id"] == "kb_001"

    def test_text_overlap(self):
        a = "DM us your order number"
        b = "Please DM your order number"
        overlap = EvidenceSelector._text_overlap(a, b)
        assert overlap > 0.5

    def test_get_params(self):
        selector = EvidenceSelector(max_evidence=2, min_similarity=0.7)
        params = selector.get_params()
        assert params["max_evidence"] == 2
        assert params["min_similarity"] == 0.7
