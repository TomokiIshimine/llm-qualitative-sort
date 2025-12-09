"""Output modes for LLM Qualitative Sort.

This module provides various output formats for sort results:
- Sorting: Simple sorted list of items
- Ranking: Detailed ranking with wins and tie status
- Percentile: Percentile scores with tier classification
"""

from dataclasses import dataclass

from llm_qualitative_sort.models import SortResult, MatchResult


# Default tier thresholds (percentile >= threshold)
DEFAULT_TIER_THRESHOLDS: dict[str, int] = {
    "S": 90,
    "A": 70,
    "B": 50,
    "C": 30,
    "D": 0,
}


# =============================================================================
# Utility Functions
# =============================================================================


def _calculate_wins_by_item(match_history: list[MatchResult]) -> dict[str, int]:
    """Calculate total wins for each item from match history.

    Args:
        match_history: List of match results

    Returns:
        Dictionary mapping item to win count
    """
    wins_by_item: dict[str, int] = {}
    for match in match_history:
        if match.winner == "A":
            wins_by_item[match.item_a] = wins_by_item.get(match.item_a, 0) + 1
        elif match.winner == "B":
            wins_by_item[match.item_b] = wins_by_item.get(match.item_b, 0) + 1
    return wins_by_item


def _calculate_total_items(rankings: list[tuple[int, list[str]]]) -> int:
    """Calculate total number of items from rankings.

    Args:
        rankings: List of (rank, items) tuples

    Returns:
        Total number of items
    """
    return sum(len(items) for _rank, items in rankings)


def _get_tier_for_percentile(
    percentile: float,
    thresholds: dict[str, int]
) -> str:
    """Determine tier classification for a percentile score.

    Args:
        percentile: Percentile score (0.0-100.0)
        thresholds: Dictionary mapping tier name to minimum percentile

    Returns:
        Tier name (e.g., "S", "A", "B", "C", "D")
    """
    # Sort thresholds by value descending
    sorted_tiers = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)

    # Default to lowest tier if no match
    default_tier = sorted_tiers[-1][0] if sorted_tiers else "D"

    for tier_name, threshold in sorted_tiers:
        if percentile >= threshold:
            return tier_name

    return default_tier


@dataclass
class SortingOutput:
    """Sorted items in rank order.

    Attributes:
        items: List of items sorted by rank (1st place first).
               Tied items maintain their original input order.
    """
    items: list[str]


@dataclass
class RankingEntry:
    """Single entry in the ranking output.

    Attributes:
        rank: Rank number (1-based, ties share the same rank)
        item: The item
        wins: Number of wins in the tournament
        is_tied: Whether this item is tied with others at the same rank
    """
    rank: int
    item: str
    wins: int
    is_tied: bool


@dataclass
class RankingOutput:
    """Complete ranking output.

    Attributes:
        entries: List of ranking entries ordered by rank
        total_items: Total number of items
    """
    entries: list[RankingEntry]
    total_items: int


@dataclass
class PercentileEntry:
    """Single entry in the percentile output.

    Attributes:
        item: The item
        percentile: Percentile score (0.0-100.0, higher is better)
        rank: Rank number
        tier: Tier classification (S/A/B/C/D)
    """
    item: str
    percentile: float
    rank: int
    tier: str


@dataclass
class PercentileOutput:
    """Complete percentile output.

    Attributes:
        entries: List of percentile entries ordered by percentile (descending)
        total_items: Total number of items
    """
    entries: list[PercentileEntry]
    total_items: int


def to_sorting(result: SortResult, original_order: list[str]) -> SortingOutput:
    """Convert sort result to a simple sorted list.

    Args:
        result: The sort result from QualitativeSorter
        original_order: Original input order of items (used to break ties)

    Returns:
        SortingOutput with items sorted by rank.
        Tied items maintain their original input order.
    """
    if not result.rankings:
        return SortingOutput(items=[])

    order_index = {item: i for i, item in enumerate(original_order)}
    sorted_items: list[str] = []

    for _rank, items in result.rankings:
        sorted_tied = sorted(items, key=lambda x: order_index.get(x, float("inf")))
        sorted_items.extend(sorted_tied)

    return SortingOutput(items=sorted_items)


def to_ranking(result: SortResult) -> RankingOutput:
    """Convert sort result to ranking format with detailed entries.

    Args:
        result: The sort result from QualitativeSorter

    Returns:
        RankingOutput with entries containing rank, wins, and tie status.
    """
    if not result.rankings:
        return RankingOutput(entries=[], total_items=0)

    wins_by_item = _calculate_wins_by_item(result.match_history)
    total_items = _calculate_total_items(result.rankings)

    entries: list[RankingEntry] = []
    for rank, items in result.rankings:
        is_tied = len(items) > 1
        for item in items:
            entries.append(
                RankingEntry(
                    rank=rank,
                    item=item,
                    wins=wins_by_item.get(item, 0),
                    is_tied=is_tied,
                )
            )

    entries.sort(key=lambda e: e.rank)

    return RankingOutput(entries=entries, total_items=total_items)


def to_percentile(
    result: SortResult,
    tier_thresholds: dict[str, int] | None = None,
) -> PercentileOutput:
    """Convert sort result to percentile format.

    Args:
        result: The sort result from QualitativeSorter
        tier_thresholds: Custom tier thresholds (percentile >= threshold).
                        Default: {"S": 90, "A": 70, "B": 50, "C": 30, "D": 0}

    Returns:
        PercentileOutput with entries containing percentile and tier.
    """
    if not result.rankings:
        return PercentileOutput(entries=[], total_items=0)

    thresholds = tier_thresholds or DEFAULT_TIER_THRESHOLDS
    total_items = _calculate_total_items(result.rankings)

    entries: list[PercentileEntry] = []
    for rank, items in result.rankings:
        # Calculate percentile: (1 - (rank - 1) / total_items) * 100
        if total_items <= 1:
            percentile = 100.0
        else:
            percentile = (1 - (rank - 1) / total_items) * 100

        tier = _get_tier_for_percentile(percentile, thresholds)

        for item in items:
            entries.append(
                PercentileEntry(
                    item=item,
                    percentile=percentile,
                    rank=rank,
                    tier=tier,
                )
            )

    entries.sort(key=lambda e: (-e.percentile, e.rank))

    return PercentileOutput(entries=entries, total_items=total_items)


__all__ = [
    # Functions
    "to_sorting",
    "to_ranking",
    "to_percentile",
    # Models
    "SortingOutput",
    "RankingOutput",
    "RankingEntry",
    "PercentileOutput",
    "PercentileEntry",
    # Constants
    "DEFAULT_TIER_THRESHOLDS",
]
