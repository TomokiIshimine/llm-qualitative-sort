"""Cache implementations for LLM Qualitative Sort."""

import json
import hashlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from llm_qualitative_sort.models import ComparisonResult

logger = logging.getLogger(__name__)


class Cache(ABC):
    """Abstract base class for caching comparison results.

    Cache key is composed of:
    - item_a: First item text
    - item_b: Second item text
    - criteria: Evaluation criteria
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
        """Get cached comparison result."""
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
        """Store comparison result in cache."""
        pass

    def _make_key(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str
    ) -> str:
        """Create deterministic cache key from components.

        Uses SHA256 for deterministic hashing that persists across Python sessions.
        Python's built-in hash() is randomized per process and should not be used
        for persistent cache keys.
        """
        key_str = f"{item_a}:{item_b}:{criteria}:{order}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]


class MemoryCache(Cache):
    """In-memory cache for comparison results.

    Simple dictionary-based cache that stores results in memory.
    Not persistent across runs.
    """

    def __init__(self) -> None:
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


class FileCache(Cache):
    """File-based cache for comparison results.

    Stores results as JSON files in a directory.
    Persistent across runs.
    """

    def __init__(self, cache_dir: str) -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def get(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str
    ) -> ComparisonResult | None:
        """Get cached comparison result from file."""
        cache_file = self._get_cache_file(item_a, item_b, criteria, order)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ComparisonResult(
                    winner=data["winner"],
                    reasoning=data["reasoning"],
                    raw_response=data["raw_response"]
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "Failed to load cache file %s: %s",
                cache_file,
                e
            )
            return None

    async def set(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str,
        result: ComparisonResult
    ) -> None:
        """Store comparison result in file."""
        cache_file = self._get_cache_file(item_a, item_b, criteria, order)

        data = {
            "winner": result.winner,
            "reasoning": result.reasoning,
            "raw_response": result.raw_response
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_cache_file(
        self,
        item_a: str,
        item_b: str,
        criteria: str,
        order: str
    ) -> Path:
        """Get cache file path for given parameters."""
        hash_key = self._make_key(item_a, item_b, criteria, order)[:16]
        return self._cache_dir / f"{hash_key}.json"


__all__ = [
    "Cache",
    "MemoryCache",
    "FileCache",
]
