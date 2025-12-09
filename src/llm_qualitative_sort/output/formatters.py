"""Output formatters for sort results."""

from llm_qualitative_sort.models import SortResult
from llm_qualitative_sort.output.models import (
    SortingOutput,
    RankingEntry,
    RankingOutput,
    PercentileEntry,
    PercentileOutput,
)
from llm_qualitative_sort.output.calculators import (
    DEFAULT_TIER_THRESHOLDS,
    calculate_wins_by_item,
    calculate_total_items,
    get_tier_for_percentile,
)


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

    wins_by_item = calculate_wins_by_item(result.match_history)
    total_items = calculate_total_items(result.rankings)

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
    total_items = calculate_total_items(result.rankings)

    entries: list[PercentileEntry] = []
    for rank, items in result.rankings:
        # Calculate percentile: (1 - (rank - 1) / total_items) * 100
        if total_items <= 1:
            percentile = 100.0
        else:
            percentile = (1 - (rank - 1) / total_items) * 100

        tier = get_tier_for_percentile(percentile, thresholds)

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
