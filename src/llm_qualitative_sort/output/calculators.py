"""Calculation utilities for output formatting."""

from llm_qualitative_sort.models import MatchResult


# Default tier thresholds (percentile >= threshold)
DEFAULT_TIER_THRESHOLDS: dict[str, int] = {
    "S": 90,
    "A": 70,
    "B": 50,
    "C": 30,
    "D": 0,
}


def calculate_wins_by_item(match_history: list[MatchResult]) -> dict[str, int]:
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


def calculate_total_items(rankings: list[tuple[int, list[str]]]) -> int:
    """Calculate total number of items from rankings.

    Args:
        rankings: List of (rank, items) tuples

    Returns:
        Total number of items
    """
    return sum(len(items) for _rank, items in rankings)


def get_tier_for_percentile(
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
