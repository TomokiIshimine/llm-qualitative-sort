"""Base class for cache implementations."""

from abc import ABC, abstractmethod

from llm_qualitative_sort.models import ComparisonResult


class Cache(ABC):
    """Abstract base class for caching comparison results.

    Cache key is composed of:
    - item_a_hash: Hash of first item
    - item_b_hash: Hash of second item
    - criteria_hash: Hash of evaluation criteria
    - order: "AB" or "BA" indicating presentation order
    """

    @abstractmethod
    async def get(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str
    ) -> ComparisonResult | None:
        """Get cached comparison result.

        Args:
            item_a: First item text
            item_b: Second item text
            criteria: Evaluation criteria
            order: Presentation order ("AB" or "BA")

        Returns:
            Cached ComparisonResult or None if not found
        """
        pass

    @abstractmethod
    async def set(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str,
        result: ComparisonResult
    ) -> None:
        """Store comparison result in cache.

        Args:
            item_a: First item text
            item_b: Second item text
            criteria: Evaluation criteria
            order: Presentation order ("AB" or "BA")
            result: ComparisonResult to cache
        """
        pass

    def _make_key(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str
    ) -> str:
        """Create cache key from components."""
        return f"{hash(item_a)}:{hash(item_b)}:{hash(criteria)}:{order}"
