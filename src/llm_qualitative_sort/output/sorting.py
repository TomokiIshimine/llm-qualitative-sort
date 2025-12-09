"""Sorting output mode implementation."""

from llm_qualitative_sort.models import SortResult
from llm_qualitative_sort.output.models import SortingOutput


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

    # Create index map for original order
    order_index = {item: i for i, item in enumerate(original_order)}

    sorted_items: list[str] = []

    for _rank, items in result.rankings:
        # Sort tied items by their original order
        sorted_tied = sorted(items, key=lambda x: order_index.get(x, float("inf")))
        sorted_items.extend(sorted_tied)

    return SortingOutput(items=sorted_items)
