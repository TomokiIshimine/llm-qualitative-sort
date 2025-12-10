"""Utility functions for llm-qualitative-sort."""

from typing import TypeVar, Callable, Hashable

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)


def group_by(items: list[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    """Group items by a key function.

    Args:
        items: List of items to group
        key_fn: Function that extracts the grouping key from an item

    Returns:
        Dictionary mapping keys to lists of items with that key

    Example:
        >>> data = [{"name": "a", "score": 1}, {"name": "b", "score": 1}]
        >>> group_by(data, lambda x: x["score"])
        {1: [{"name": "a", "score": 1}, {"name": "b", "score": 1}]}
    """
    result: dict[K, list[T]] = {}
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result
