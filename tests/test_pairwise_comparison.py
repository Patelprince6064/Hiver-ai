"""Tests for pairwise comparison logic."""

import pytest
from src.evaluation.reply_evaluation_schema import PairwiseComparison


class TestPairwiseComparison:
    def test_valid_comparison(self):
        pc = PairwiseComparison(
            system_a="grounded_llm",
            system_b="historical_baseline",
            n_queries=100,
            wins_a=60,
            ties=20,
            wins_b=20,
            win_rate_a=0.6,
            win_rate_b=0.2,
            tie_rate=0.2,
            mean_difference=0.5,
            median_difference=0.5,
        )
        assert pc.wins_a == 60
        assert pc.n_queries == 100
        assert pc.win_rate_a == 0.6

    def test_win_rates_sum_to_one(self):
        pc = PairwiseComparison(
            system_a="A",
            system_b="B",
            n_queries=100,
            wins_a=50,
            ties=30,
            wins_b=20,
            win_rate_a=0.5,
            win_rate_b=0.2,
            tie_rate=0.3,
        )
        total = pc.win_rate_a + pc.win_rate_b + pc.tie_rate
        assert abs(total - 1.0) < 0.01

    def test_zero_queries(self):
        pc = PairwiseComparison(
            system_a="A",
            system_b="B",
            n_queries=0,
        )
        assert pc.win_rate_a == 0.0
        assert pc.win_rate_b == 0.0
        assert pc.tie_rate == 0.0


class TestPairwiseComparisonComputation:
    def _compute_pairwise(self, records, sys_a, sys_b):
        from collections import defaultdict
        by_query = defaultdict(dict)
        for rec in records:
            qid = rec["query_id"]
            sname = rec.get("system_name") or rec.get("system", "")
            by_query[qid][sname] = rec

        wins_a = 0
        wins_b = 0
        ties = 0
        diffs = []

        for qid, sys_records in by_query.items():
            if sys_a not in sys_records or sys_b not in sys_records:
                continue
            score_a = sys_records[sys_a].get("scores", {}).get("overall")
            score_b = sys_records[sys_b].get("scores", {}).get("overall")
            if score_a is None or score_b is None:
                continue
            diff = float(score_a) - float(score_b)
            diffs.append(diff)
            if diff > 0.01:
                wins_a += 1
            elif diff < -0.01:
                wins_b += 1
            else:
                ties += 1

        n = len(diffs)
        return {
            "system_a": sys_a,
            "system_b": sys_b,
            "n_queries": n,
            "wins_a": wins_a,
            "ties": ties,
            "wins_b": wins_b,
            "win_rate_a": round(wins_a / n, 3) if n else 0,
            "win_rate_b": round(wins_b / n, 3) if n else 0,
            "tie_rate": round(ties / n, 3) if n else 0,
            "mean_difference": round(float(sum(diffs) / len(diffs)), 3) if diffs else 0,
        }

    def test_a_wins(self):
        records = [
            {"query_id": "q1", "system_name": "A", "scores": {"overall": 5}},
            {"query_id": "q1", "system_name": "B", "scores": {"overall": 3}},
        ]
        result = self._compute_pairwise(records, "A", "B")
        assert result["wins_a"] == 1
        assert result["wins_b"] == 0
        assert result["ties"] == 0

    def test_b_wins(self):
        records = [
            {"query_id": "q1", "system_name": "A", "scores": {"overall": 2}},
            {"query_id": "q1", "system_name": "B", "scores": {"overall": 5}},
        ]
        result = self._compute_pairwise(records, "A", "B")
        assert result["wins_a"] == 0
        assert result["wins_b"] == 1

    def test_tie(self):
        records = [
            {"query_id": "q1", "system_name": "A", "scores": {"overall": 4}},
            {"query_id": "q1", "system_name": "B", "scores": {"overall": 4}},
        ]
        result = self._compute_pairwise(records, "A", "B")
        assert result["ties"] == 1
        assert result["wins_a"] == 0
        assert result["wins_b"] == 0

    def test_mixed(self):
        records = [
            {"query_id": "q1", "system_name": "A", "scores": {"overall": 5}},
            {"query_id": "q1", "system_name": "B", "scores": {"overall": 3}},
            {"query_id": "q2", "system_name": "A", "scores": {"overall": 2}},
            {"query_id": "q2", "system_name": "B", "scores": {"overall": 4}},
            {"query_id": "q3", "system_name": "A", "scores": {"overall": 4}},
            {"query_id": "q3", "system_name": "B", "scores": {"overall": 4}},
        ]
        result = self._compute_pairwise(records, "A", "B")
        assert result["wins_a"] == 1
        assert result["wins_b"] == 1
        assert result["ties"] == 1

    def test_missing_scores_skipped(self):
        records = [
            {"query_id": "q1", "system_name": "A", "scores": {"overall": None}},
            {"query_id": "q1", "system_name": "B", "scores": {"overall": 4}},
        ]
        result = self._compute_pairwise(records, "A", "B")
        assert result["n_queries"] == 0

    def test_missing_system_skipped(self):
        records = [
            {"query_id": "q1", "system_name": "A", "scores": {"overall": 5}},
        ]
        result = self._compute_pairwise(records, "A", "B")
        assert result["n_queries"] == 0
