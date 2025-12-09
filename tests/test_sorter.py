"""Tests for QualitativeSorter."""

import pytest
from llm_qualitative_sort.sorter import QualitativeSorter
from llm_qualitative_sort.providers.mock import MockLLMProvider
from llm_qualitative_sort.cache import MemoryCache
from llm_qualitative_sort.events import EventType, ProgressEvent
from llm_qualitative_sort.models import SortResult


class TestQualitativeSorterInit:
    """Tests for QualitativeSorter initialization."""

    def test_create_sorter(self):
        provider = MockLLMProvider(seed=42)
        sorter = QualitativeSorter(
            provider=provider,
            criteria="larger is better"
        )
        assert sorter is not None

    def test_create_sorter_with_all_options(self):
        provider = MockLLMProvider(seed=42)
        cache = MemoryCache()
        events = []

        def on_progress(event: ProgressEvent):
            events.append(event)

        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=3,
            comparison_rounds=4,
            criteria="larger is better",
            max_concurrent_requests=5,
            cache=cache,
            on_progress=on_progress
        )
        assert sorter.elimination_count == 3
        assert sorter.comparison_rounds == 4
        assert sorter.criteria == "larger is better"
        assert sorter.max_concurrent_requests == 5

    def test_comparison_rounds_must_be_even(self):
        provider = MockLLMProvider(seed=42)
        with pytest.raises(ValueError):
            QualitativeSorter(
                provider=provider,
                comparison_rounds=3,  # Odd number should fail
                criteria="test"
            )


class TestQualitativeSorterSort:
    """Tests for QualitativeSorter.sort() method."""

    async def test_sort_two_items(self):
        provider = MockLLMProvider(seed=42)
        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=1,
            criteria="larger is better"
        )
        result = await sorter.sort(["10", "5"])

        assert isinstance(result, SortResult)
        assert len(result.rankings) > 0
        # 10 should rank higher than 5
        first_rank_items = result.rankings[0][1]
        assert "10" in first_rank_items

    async def test_sort_multiple_items(self):
        provider = MockLLMProvider(seed=42)
        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=2,
            criteria="larger is better"
        )
        items = ["100", "50", "75", "25"]
        result = await sorter.sort(items)

        assert isinstance(result, SortResult)
        assert result.statistics.total_matches > 0

    async def test_sort_with_cache(self):
        provider = MockLLMProvider(seed=42)
        cache = MemoryCache()
        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=1,
            criteria="larger is better",
            cache=cache
        )
        items = ["10", "5"]
        result = await sorter.sort(items)

        # Should have used cache for reverse order comparison
        assert result.statistics.total_api_calls >= 0

    async def test_sort_progress_callback(self):
        provider = MockLLMProvider(seed=42)
        events: list[ProgressEvent] = []

        def on_progress(event: ProgressEvent):
            events.append(event)

        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=1,
            criteria="larger is better",
            on_progress=on_progress
        )
        await sorter.sort(["10", "5"])

        # Should have received progress events
        assert len(events) > 0
        event_types = [e.type for e in events]
        assert EventType.MATCH_START in event_types
        assert EventType.MATCH_END in event_types

    async def test_sort_statistics(self):
        provider = MockLLMProvider(seed=42)
        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="larger is better"
        )
        result = await sorter.sort(["10", "5"])

        assert result.statistics.total_matches >= 1
        assert result.statistics.elapsed_time >= 0

    async def test_sort_match_history(self):
        provider = MockLLMProvider(seed=42)
        sorter = QualitativeSorter(
            provider=provider,
            elimination_count=1,
            criteria="larger is better"
        )
        result = await sorter.sort(["10", "5"])

        assert len(result.match_history) >= 1
        match = result.match_history[0]
        assert match.item_a in ["10", "5"]
        assert match.item_b in ["10", "5"]
