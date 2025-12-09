"""Tests for data models."""

import pytest
from llm_qualitative_sort.models import (
    ComparisonResult,
    RoundResult,
    MatchResult,
    SortResult,
    Statistics,
)


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_create_with_winner_a(self):
        result = ComparisonResult(
            winner="A",
            reasoning="A is better",
            raw_response={"choice": "A"}
        )
        assert result.winner == "A"
        assert result.reasoning == "A is better"
        assert result.raw_response == {"choice": "A"}

    def test_create_with_winner_b(self):
        result = ComparisonResult(
            winner="B",
            reasoning="B is better",
            raw_response={"choice": "B"}
        )
        assert result.winner == "B"

    def test_create_with_no_winner(self):
        result = ComparisonResult(
            winner=None,
            reasoning="Error occurred",
            raw_response={}
        )
        assert result.winner is None


class TestRoundResult:
    """Tests for RoundResult dataclass."""

    def test_create_round_result(self):
        result = RoundResult(
            order="AB",
            winner="A",
            reasoning="A is stronger",
            cached=False
        )
        assert result.order == "AB"
        assert result.winner == "A"
        assert result.reasoning == "A is stronger"
        assert result.cached is False

    def test_create_cached_round_result(self):
        result = RoundResult(
            order="BA",
            winner="B",
            reasoning="B wins",
            cached=True
        )
        assert result.cached is True


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_create_match_result(self):
        rounds = [
            RoundResult(order="AB", winner="A", reasoning="r1", cached=False),
            RoundResult(order="BA", winner="A", reasoning="r2", cached=False),
        ]
        result = MatchResult(
            item_a="text1",
            item_b="text2",
            winner="A",
            rounds=rounds
        )
        assert result.item_a == "text1"
        assert result.item_b == "text2"
        assert result.winner == "A"
        assert len(result.rounds) == 2

    def test_create_draw_match_result(self):
        rounds = [
            RoundResult(order="AB", winner="A", reasoning="r1", cached=False),
            RoundResult(order="BA", winner="B", reasoning="r2", cached=False),
        ]
        result = MatchResult(
            item_a="text1",
            item_b="text2",
            winner=None,
            rounds=rounds
        )
        assert result.winner is None


class TestStatistics:
    """Tests for Statistics dataclass."""

    def test_create_statistics(self):
        stats = Statistics(
            total_matches=10,
            total_api_calls=20,
            cache_hits=5,
            elapsed_time=1.5
        )
        assert stats.total_matches == 10
        assert stats.total_api_calls == 20
        assert stats.cache_hits == 5
        assert stats.elapsed_time == 1.5


class TestSortResult:
    """Tests for SortResult dataclass."""

    def test_create_sort_result(self):
        rankings = [(1, ["item1"]), (2, ["item2", "item3"])]
        stats = Statistics(
            total_matches=5,
            total_api_calls=10,
            cache_hits=2,
            elapsed_time=2.0
        )
        result = SortResult(
            rankings=rankings,
            match_history=[],
            statistics=stats
        )
        assert result.rankings == rankings
        assert len(result.match_history) == 0
        assert result.statistics.total_matches == 5
