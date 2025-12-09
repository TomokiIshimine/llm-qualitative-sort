"""Tests for cache implementations."""

import pytest
import tempfile
import os
from abc import ABC

from llm_qualitative_sort.cache import Cache, MemoryCache, FileCache
from llm_qualitative_sort.models import ComparisonResult


class TestCacheBase:
    """Tests for Cache abstract base class."""

    def test_is_abstract_class(self):
        assert issubclass(Cache, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Cache()

    def test_has_get_method(self):
        assert hasattr(Cache, "get")

    def test_has_set_method(self):
        assert hasattr(Cache, "set")


class TestMemoryCache:
    """Tests for MemoryCache."""

    def test_inherits_from_cache(self):
        assert issubclass(MemoryCache, Cache)

    def test_create_memory_cache(self):
        cache = MemoryCache()
        assert cache is not None

    async def test_get_nonexistent_key(self):
        cache = MemoryCache()
        result = await cache.get("nonexistent", "key", "criteria", "AB")
        assert result is None

    async def test_set_and_get(self):
        cache = MemoryCache()
        comparison = ComparisonResult(
            winner="A",
            reasoning="A is better",
            raw_response={}
        )
        await cache.set("item_a", "item_b", "criteria", "AB", comparison)
        result = await cache.get("item_a", "item_b", "criteria", "AB")
        assert result is not None
        assert result.winner == "A"

    async def test_different_order_different_cache(self):
        cache = MemoryCache()
        comparison = ComparisonResult(
            winner="A",
            reasoning="A wins",
            raw_response={}
        )
        await cache.set("item_a", "item_b", "criteria", "AB", comparison)

        # Different order should not hit cache
        result = await cache.get("item_a", "item_b", "criteria", "BA")
        assert result is None

    async def test_different_criteria_different_cache(self):
        cache = MemoryCache()
        comparison = ComparisonResult(
            winner="A",
            reasoning="A wins",
            raw_response={}
        )
        await cache.set("item_a", "item_b", "criteria1", "AB", comparison)

        # Different criteria should not hit cache
        result = await cache.get("item_a", "item_b", "criteria2", "AB")
        assert result is None


class TestFileCache:
    """Tests for FileCache."""

    def test_inherits_from_cache(self):
        assert issubclass(FileCache, Cache)

    def test_create_file_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(tmpdir)
            assert cache is not None

    async def test_get_nonexistent_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(tmpdir)
            result = await cache.get("nonexistent", "key", "criteria", "AB")
            assert result is None

    async def test_set_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(tmpdir)
            comparison = ComparisonResult(
                winner="B",
                reasoning="B is better",
                raw_response={"test": "data"}
            )
            await cache.set("item_a", "item_b", "criteria", "AB", comparison)
            result = await cache.get("item_a", "item_b", "criteria", "AB")
            assert result is not None
            assert result.winner == "B"
            assert result.reasoning == "B is better"

    async def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # First cache instance
            cache1 = FileCache(tmpdir)
            comparison = ComparisonResult(
                winner="A",
                reasoning="A wins",
                raw_response={}
            )
            await cache1.set("item_a", "item_b", "criteria", "AB", comparison)

            # Second cache instance should find the cached value
            cache2 = FileCache(tmpdir)
            result = await cache2.get("item_a", "item_b", "criteria", "AB")
            assert result is not None
            assert result.winner == "A"
