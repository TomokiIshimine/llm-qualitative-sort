"""Tests for output modes."""

import pytest
from llm_qualitative_sort.models import SortResult, Statistics, MatchResult
from llm_qualitative_sort.output import (
    to_sorting,
    to_ranking,
    to_percentile,
    SortingOutput,
    RankingOutput,
    RankingEntry,
    PercentileOutput,
    PercentileEntry,
)


@pytest.fixture
def sample_statistics() -> Statistics:
    """Create sample statistics for testing."""
    return Statistics(
        total_matches=6,
        total_api_calls=12,
        cache_hits=0,
        elapsed_time=1.5,
    )


@pytest.fixture
def sample_sort_result(sample_statistics: Statistics) -> SortResult:
    """Create sample sort result with rankings.

    Rankings: Alice(1st), Bob&Carol(2nd tied), Dave(4th)
    """
    return SortResult(
        rankings=[
            (1, ["Alice"]),
            (2, ["Bob", "Carol"]),
            (4, ["Dave"]),
        ],
        match_history=[],
        statistics=sample_statistics,
    )


@pytest.fixture
def single_item_result(sample_statistics: Statistics) -> SortResult:
    """Create sort result with single item."""
    return SortResult(
        rankings=[(1, ["Only"])],
        match_history=[],
        statistics=sample_statistics,
    )


class TestSortingOutput:
    """Tests for to_sorting function."""

    def test_basic_sorting(self, sample_sort_result: SortResult):
        """Test basic sorting output."""
        original_order = ["Alice", "Bob", "Carol", "Dave"]
        result = to_sorting(sample_sort_result, original_order=original_order)

        assert isinstance(result, SortingOutput)
        assert result.items == ["Alice", "Bob", "Carol", "Dave"]

    def test_tied_items_preserve_original_order(self, sample_statistics: Statistics):
        """Test that tied items maintain original input order."""
        sort_result = SortResult(
            rankings=[
                (1, ["Carol", "Bob"]),  # Tied, but Carol listed first in rankings
                (3, ["Alice"]),
            ],
            match_history=[],
            statistics=sample_statistics,
        )
        # Original order: Alice, Bob, Carol
        original_order = ["Alice", "Bob", "Carol"]
        result = to_sorting(sort_result, original_order=original_order)

        # Bob should come before Carol (original order)
        assert result.items == ["Bob", "Carol", "Alice"]

    def test_single_item(self, single_item_result: SortResult):
        """Test sorting with single item."""
        result = to_sorting(single_item_result, original_order=["Only"])

        assert result.items == ["Only"]

    def test_empty_rankings(self, sample_statistics: Statistics):
        """Test sorting with empty rankings."""
        sort_result = SortResult(
            rankings=[],
            match_history=[],
            statistics=sample_statistics,
        )
        result = to_sorting(sort_result, original_order=[])

        assert result.items == []


class TestRankingOutput:
    """Tests for to_ranking function."""

    def test_basic_ranking(self, sample_sort_result: SortResult):
        """Test basic ranking output."""
        result = to_ranking(sample_sort_result)

        assert isinstance(result, RankingOutput)
        assert result.total_items == 4
        assert len(result.entries) == 4

    def test_ranking_entries_have_correct_ranks(self, sample_sort_result: SortResult):
        """Test that ranking entries have correct rank numbers."""
        result = to_ranking(sample_sort_result)

        # Alice: rank 1
        alice = next(e for e in result.entries if e.item == "Alice")
        assert alice.rank == 1
        assert alice.is_tied is False

        # Bob: rank 2 (tied)
        bob = next(e for e in result.entries if e.item == "Bob")
        assert bob.rank == 2
        assert bob.is_tied is True

        # Carol: rank 2 (tied)
        carol = next(e for e in result.entries if e.item == "Carol")
        assert carol.rank == 2
        assert carol.is_tied is True

        # Dave: rank 4
        dave = next(e for e in result.entries if e.item == "Dave")
        assert dave.rank == 4
        assert dave.is_tied is False

    def test_ranking_entries_ordered_by_rank(self, sample_sort_result: SortResult):
        """Test that entries are ordered by rank."""
        result = to_ranking(sample_sort_result)

        ranks = [e.rank for e in result.entries]
        assert ranks == sorted(ranks)

    def test_single_item_ranking(self, single_item_result: SortResult):
        """Test ranking with single item."""
        result = to_ranking(single_item_result)

        assert result.total_items == 1
        assert len(result.entries) == 1
        assert result.entries[0].rank == 1
        assert result.entries[0].is_tied is False

    def test_wins_from_match_history(self, sample_statistics: Statistics):
        """Test that wins are calculated from rankings position."""
        # Create result with known win counts (inferred from rank)
        sort_result = SortResult(
            rankings=[
                (1, ["Winner"]),      # 3 wins (highest)
                (2, ["Second"]),      # 2 wins
                (3, ["Third"]),       # 1 win
            ],
            match_history=[],
            statistics=sample_statistics,
        )
        result = to_ranking(sort_result)

        # Wins should be inferred from rankings
        # Higher rank = more wins
        winner = next(e for e in result.entries if e.item == "Winner")
        second = next(e for e in result.entries if e.item == "Second")
        third = next(e for e in result.entries if e.item == "Third")

        assert winner.wins >= second.wins >= third.wins


class TestPercentileOutput:
    """Tests for to_percentile function."""

    def test_basic_percentile(self, sample_sort_result: SortResult):
        """Test basic percentile output."""
        result = to_percentile(sample_sort_result)

        assert isinstance(result, PercentileOutput)
        assert result.total_items == 4
        assert len(result.entries) == 4

    def test_percentile_calculation(self, sample_sort_result: SortResult):
        """Test percentile values are calculated correctly."""
        result = to_percentile(sample_sort_result)

        # With 4 items:
        # Rank 1: percentile = (1 - (1-1)/4) * 100 = 100.0
        # Rank 2: percentile = (1 - (2-1)/4) * 100 = 75.0
        # Rank 4: percentile = (1 - (4-1)/4) * 100 = 25.0
        alice = next(e for e in result.entries if e.item == "Alice")
        assert alice.percentile == 100.0
        assert alice.rank == 1

        bob = next(e for e in result.entries if e.item == "Bob")
        assert bob.percentile == 75.0
        assert bob.rank == 2

        carol = next(e for e in result.entries if e.item == "Carol")
        assert carol.percentile == 75.0  # Same rank as Bob
        assert carol.rank == 2

        dave = next(e for e in result.entries if e.item == "Dave")
        assert dave.percentile == 25.0
        assert dave.rank == 4

    def test_tier_assignment(self, sample_sort_result: SortResult):
        """Test tier assignment based on percentile."""
        result = to_percentile(sample_sort_result)

        # Default tiers: S>=90, A>=70, B>=50, C>=30, D<30
        alice = next(e for e in result.entries if e.item == "Alice")
        assert alice.tier == "S"  # 100%

        bob = next(e for e in result.entries if e.item == "Bob")
        assert bob.tier == "A"  # 75%

        dave = next(e for e in result.entries if e.item == "Dave")
        assert dave.tier == "D"  # 25%

    def test_custom_tier_thresholds(self, sample_sort_result: SortResult):
        """Test custom tier thresholds."""
        custom_tiers = {"S": 95, "A": 80, "B": 60, "C": 40, "D": 0}
        result = to_percentile(sample_sort_result, tier_thresholds=custom_tiers)

        alice = next(e for e in result.entries if e.item == "Alice")
        assert alice.tier == "S"  # 100% >= 95

        bob = next(e for e in result.entries if e.item == "Bob")
        assert bob.tier == "B"  # 75% >= 60, < 80

    def test_single_item_percentile(self, single_item_result: SortResult):
        """Test percentile with single item."""
        result = to_percentile(single_item_result)

        assert result.total_items == 1
        assert result.entries[0].percentile == 100.0
        assert result.entries[0].tier == "S"

    def test_entries_ordered_by_percentile_descending(self, sample_sort_result: SortResult):
        """Test that entries are ordered by percentile (highest first)."""
        result = to_percentile(sample_sort_result)

        percentiles = [e.percentile for e in result.entries]
        assert percentiles == sorted(percentiles, reverse=True)

    def test_all_items_same_rank(self, sample_statistics: Statistics):
        """Test when all items have the same rank."""
        sort_result = SortResult(
            rankings=[(1, ["A", "B", "C"])],
            match_history=[],
            statistics=sample_statistics,
        )
        result = to_percentile(sort_result)

        # All items should have 100% percentile
        for entry in result.entries:
            assert entry.percentile == 100.0
            assert entry.tier == "S"
