"""Percentile output mode implementation."""

from llm_qualitative_sort.models import SortResult
from llm_qualitative_sort.output.models import (
    DEFAULT_TIER_THRESHOLDS,
    PercentileEntry,
    PercentileOutput,
)


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
    total_items = sum(len(items) for _rank, items in result.rankings)

    entries: list[PercentileEntry] = []

    for rank, items in result.rankings:
        percentile = _calculate_percentile(rank, total_items)
        tier = _get_tier(percentile, thresholds)

        for item in items:
            entries.append(
                PercentileEntry(
                    item=item,
                    percentile=percentile,
                    rank=rank,
                    tier=tier,
                )
            )

    # Sort by percentile descending (highest first)
    entries.sort(key=lambda e: (-e.percentile, e.rank))

    return PercentileOutput(entries=entries, total_items=total_items)


def _calculate_percentile(rank: int, total_items: int) -> float:
    """Calculate percentile for a given rank.

    Formula: percentile = (1 - (rank - 1) / total_items) * 100

    Args:
        rank: The rank (1-based)
        total_items: Total number of items

    Returns:
        Percentile value (0.0-100.0)
    """
    if total_items <= 1:
        return 100.0

    return (1 - (rank - 1) / total_items) * 100


def _get_tier(percentile: float, thresholds: dict[str, int]) -> str:
    """Get tier based on percentile.

    Args:
        percentile: The percentile value
        thresholds: Tier thresholds (tier -> minimum percentile)

    Returns:
        Tier string (e.g., "S", "A", "B", "C", "D")
    """
    # Sort thresholds by value descending
    sorted_tiers = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)

    for tier, threshold in sorted_tiers:
        if percentile >= threshold:
            return tier

    # Fallback to lowest tier if no threshold matched
    return sorted_tiers[-1][0] if sorted_tiers else "D"
