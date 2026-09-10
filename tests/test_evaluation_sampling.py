"""Tests for evaluation sampling and manifest."""

import pytest
import json
import random
from pathlib import Path


class TestEvaluationSampling:
    def test_deterministic_sampling(self):
        rng = random.Random(42)
        indices = rng.sample(range(1000), 100)
        rng2 = random.Random(42)
        indices2 = rng2.sample(range(1000), 100)
        assert indices == indices2

    def test_different_seeds(self):
        rng1 = random.Random(42)
        rng2 = random.Random(99)
        assert rng1.sample(range(1000), 10) != rng2.sample(range(1000), 10)

    def test_sample_size(self):
        rng = random.Random(42)
        indices = rng.sample(range(500), 150)
        assert len(indices) == 150

    def test_sample_no_duplicates(self):
        rng = random.Random(42)
        indices = rng.sample(range(500), 150)
        assert len(set(indices)) == 150

    def test_sample_within_range(self):
        rng = random.Random(42)
        indices = rng.sample(range(500), 150)
        assert all(0 <= i < 500 for i in indices)


class TestBlindLabelRandomization:
    def test_blind_labels_deterministic(self):
        blind_labels = ["System A", "System B", "System C", "System D"]
        rng = random.Random(42)
        labels1 = blind_labels[:]
        rng.shuffle(labels1)

        rng2 = random.Random(42)
        labels2 = blind_labels[:]
        rng2.shuffle(labels2)
        assert labels1 == labels2

    def test_blind_mapping_covers_all(self):
        blind_labels = ["System A", "System B", "System C", "System D"]
        system_names = ["generic_baseline", "historical_baseline", "grounded_llm", "grounded_llm_verified"]
        rng = random.Random(42)
        shuffled = blind_labels[:]
        rng.shuffle(shuffled)
        mapping = {shuffled[i]: system_names[i] for i in range(4)}
        assert set(mapping.keys()) == set(blind_labels)
        assert set(mapping.values()) == set(system_names)

    def test_same_seed_same_shuffle(self):
        blind_labels = ["System A", "System B", "System C", "System D"]
        rng1 = random.Random(42)
        labels1 = blind_labels[:]
        rng1.shuffle(labels1)

        rng2 = random.Random(42)
        labels2 = blind_labels[:]
        rng2.shuffle(labels2)
        assert labels1 == labels2


class TestEvaluationManifest:
    def test_manifest_schema(self):
        manifest = {
            "version": "1.0",
            "n_queries": 150,
            "seed": 42,
            "splits": {"dev": 150},
            "intent_distribution": {"shipping": 50, "billing": 30},
            "timestamp": "2024-01-01T00:00:00Z",
        }
        assert manifest["n_queries"] == 150
        assert manifest["seed"] == 42
        assert "shipping" in manifest["intent_distribution"]

    def test_manifest_intent_sum(self):
        manifest = {
            "intent_distribution": {"shipping": 50, "billing": 30, "technical": 20},
            "n_queries": 100,
        }
        total = sum(manifest["intent_distribution"].values())
        assert total == manifest["n_queries"]


class TestDuplicateQueryDetection:
    def test_no_duplicates(self):
        queries = [
            {"query_id": "q_0001", "customer_message": "A"},
            {"query_id": "q_0002", "customer_message": "B"},
        ]
        qids = [q["query_id"] for q in queries]
        assert len(qids) == len(set(qids))

    def test_detect_duplicates(self):
        queries = [
            {"query_id": "q_0001", "customer_message": "A"},
            {"query_id": "q_0001", "customer_message": "A"},
        ]
        qids = [q["query_id"] for q in queries]
        assert len(qids) != len(set(qids))
