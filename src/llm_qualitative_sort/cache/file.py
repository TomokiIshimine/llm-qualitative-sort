"""File-based cache implementation."""

import json
import hashlib
from pathlib import Path

from llm_qualitative_sort.cache.base import Cache
from llm_qualitative_sort.models import ComparisonResult


class FileCache(Cache):
    """File-based cache for comparison results.

    Stores results as JSON files in a directory.
    Persistent across runs.
    """

    def __init__(self, cache_dir: str):
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
        except (json.JSONDecodeError, KeyError):
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
        key = f"{item_a}:{item_b}:{criteria}:{order}"
        hash_key = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._cache_dir / f"{hash_key}.json"
