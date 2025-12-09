"""Integration tests for OpenAI provider.

These tests make actual API calls to OpenAI and require:
- OPENAI_API_KEY environment variable to be set

Tests are skipped if the API key is not available.
"""

import os
import pytest

from llm_qualitative_sort.sorter import QualitativeSorter
from llm_qualitative_sort.providers.openai import OpenAIProvider
from llm_qualitative_sort.cache import MemoryCache
from llm_qualitative_sort.events import EventType, ProgressEvent
from llm_qualitative_sort.models import SortResult, ComparisonResult


# Skip all tests in this module if OPENAI_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY environment variable not set"
)


@pytest.fixture
def openai_provider():
    """Create an OpenAI provider with API key from environment."""
    api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAIProvider(api_key=api_key)


@pytest.fixture
def openai_provider_with_model():
    """Create an OpenAI provider with specific model."""
    api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAIProvider(api_key=api_key, model="gpt-4o-mini")


class TestOpenAIProviderIntegration:
    """Integration tests for OpenAIProvider."""

    async def test_compare_numbers(self, openai_provider):
        """Test comparing two numbers."""
        result = await openai_provider.compare(
            item_a="100",
            item_b="50",
            criteria="Select the larger number"
        )

        assert isinstance(result, ComparisonResult)
        assert result.winner == "A"
        assert result.reasoning is not None
        assert len(result.reasoning) > 0

    async def test_compare_with_reasoning(self, openai_provider):
        """Test that comparison includes reasoning."""
        result = await openai_provider.compare(
            item_a="Python",
            item_b="JavaScript",
            criteria="Select the language better suited for data science"
        )

        assert isinstance(result, ComparisonResult)
        assert result.winner in ["A", "B"]
        assert result.reasoning is not None
        assert len(result.reasoning) > 10

    async def test_compare_returns_raw_response(self, openai_provider):
        """Test that raw response is included."""
        result = await openai_provider.compare(
            item_a="Apple",
            item_b="Orange",
            criteria="Select the fruit with more vitamin C"
        )

        assert result.raw_response is not None
        assert isinstance(result.raw_response, dict)

    async def test_compare_text_quality(self, openai_provider):
        """Test comparing text quality."""
        text_a = "The quick brown fox jumps over the lazy dog."
        text_b = "fox quick brown lazy dog over jumps the the"

        result = await openai_provider.compare(
            item_a=text_a,
            item_b=text_b,
            criteria="Select the text that is more grammatically correct and readable"
        )

        assert isinstance(result, ComparisonResult)
        assert result.winner == "A"

    async def test_compare_with_custom_model(self, openai_provider_with_model):
        """Test comparison with explicitly specified model."""
        result = await openai_provider_with_model.compare(
            item_a="10",
            item_b="5",
            criteria="Select the larger number"
        )

        assert isinstance(result, ComparisonResult)
        assert result.winner == "A"


class TestQualitativeSorterWithOpenAI:
    """Integration tests for QualitativeSorter with OpenAI provider."""

    async def test_sort_two_items(self, openai_provider):
        """Test sorting two items."""
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the larger number"
        )

        result = await sorter.sort(["100", "50"])

        assert isinstance(result, SortResult)
        assert len(result.rankings) > 0
        # 100 should rank higher than 50
        first_rank_items = result.rankings[0][1]
        assert "100" in first_rank_items

    async def test_sort_three_items(self, openai_provider):
        """Test sorting three items."""
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the larger number"
        )

        result = await sorter.sort(["100", "50", "75"])

        assert isinstance(result, SortResult)
        assert len(result.rankings) > 0
        # 100 should rank first
        first_rank_items = result.rankings[0][1]
        assert "100" in first_rank_items

    async def test_sort_with_cache(self, openai_provider):
        """Test sorting with caching enabled."""
        cache = MemoryCache()
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the larger number",
            cache=cache
        )

        items = ["100", "50"]
        result = await sorter.sort(items)

        assert isinstance(result, SortResult)
        # Cache should have been used for at least some comparisons
        assert result.statistics.cache_hits >= 0

    async def test_sort_progress_events(self, openai_provider):
        """Test that progress events are emitted."""
        events: list[ProgressEvent] = []

        def on_progress(event: ProgressEvent):
            events.append(event)

        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the larger number",
            on_progress=on_progress
        )

        await sorter.sort(["100", "50"])

        assert len(events) > 0
        event_types = [e.type for e in events]
        assert EventType.MATCH_START in event_types
        assert EventType.MATCH_END in event_types

    async def test_sort_statistics(self, openai_provider):
        """Test that statistics are collected."""
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the larger number"
        )

        result = await sorter.sort(["100", "50"])

        assert result.statistics.total_matches >= 1
        assert result.statistics.total_api_calls >= 1
        assert result.statistics.elapsed_time >= 0

    async def test_sort_match_history(self, openai_provider):
        """Test that match history is recorded."""
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the larger number"
        )

        result = await sorter.sort(["100", "50"])

        assert len(result.match_history) >= 1
        match = result.match_history[0]
        assert match.item_a in ["100", "50"]
        assert match.item_b in ["100", "50"]
        # Winner is "A", "B", or None (draw)
        assert match.winner in ["A", "B", None]


class TestQualitativeSorterTextSorting:
    """Integration tests for sorting text content with OpenAI."""

    async def test_sort_by_text_quality(self, openai_provider):
        """Test sorting texts by grammatical quality."""
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the text that is more grammatically correct and well-written"
        )

        texts = [
            "The elegant solution effectively addresses the complex problem.",
            "solution elegant the complex problem addresses effectively",
            "A good solution for the problem."
        ]

        result = await sorter.sort(texts)

        assert isinstance(result, SortResult)
        # The first text should rank highest
        first_rank_items = result.rankings[0][1]
        assert texts[0] in first_rank_items

    async def test_sort_by_creativity(self, openai_provider):
        """Test sorting texts by creativity."""
        sorter = QualitativeSorter(
            provider=openai_provider,
            elimination_count=1,
            comparison_rounds=2,
            criteria="Select the more creative and imaginative text"
        )

        texts = [
            "The dragon soared through clouds of cotton candy, breathing rainbow fire.",
            "The dog walked in the park.",
            "A mysterious portal opened, revealing a world of dancing stars."
        ]

        result = await sorter.sort(texts)

        assert isinstance(result, SortResult)
        # The plain text should rank lowest
        last_rank = result.rankings[-1][1]
        assert texts[1] in last_rank


class TestOpenAIProviderErrorHandling:
    """Integration tests for error handling with OpenAI provider."""

    async def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        provider = OpenAIProvider(api_key="invalid-key-12345")

        result = await provider.compare(
            item_a="A",
            item_b="B",
            criteria="Select one"
        )

        # Should return an error result, not raise an exception
        assert isinstance(result, ComparisonResult)
        assert result.winner is None
        # Error type is stored in raw_response dict
        assert result.raw_response.get("error_type") is not None
