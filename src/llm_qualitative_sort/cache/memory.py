"""In-memory cache implementation."""

from llm_qualitative_sort.cache.base import Cache
from llm_qualitative_sort.models import ComparisonResult


class MemoryCache(Cache):
    """In-memory cache for comparison results.

    Simple dictionary-based cache that stores results in memory.
    Not persistent across runs.
    """

    def __init__(self):
        self._cache: dict[str, ComparisonResult] = {}

    async def get(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str
    ) -> ComparisonResult | None:
        """Get cached comparison result from memory."""
        key = self._make_key(item_a, item_b, criteria, order)
        return self._cache.get(key)

    async def set(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str,
        result: ComparisonResult
    ) -> None:
        """Store comparison result in memory."""
        key = self._make_key(item_a, item_b, criteria, order)
        self._cache[key] = result
