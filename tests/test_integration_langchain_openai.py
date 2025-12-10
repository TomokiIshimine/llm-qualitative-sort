"""Integration tests for LangChainProvider with OpenAI."""

import os
import pytest

from llm_qualitative_sort import (
    LangChainProvider,
    QualitativeSorter,
    MemoryCache,
    EventType,
)


@pytest.fixture
def openai_llm():
    """Create an OpenAI LLM for testing."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=0,
    )


@pytest.fixture
def langchain_provider(openai_llm):
    """Create a LangChainProvider with OpenAI."""
    return LangChainProvider(llm=openai_llm)


@pytest.mark.integration
class TestLangChainProviderWithOpenAI:
    """Integration tests for LangChainProvider with OpenAI."""

    async def test_compare_text_quality(self, langchain_provider):
        """Test comparing text quality."""
        text_a = "The quick brown fox jumps over the lazy dog."
        text_b = "fox quick brown lazy dog over jumps the the"

        result = await langchain_provider.compare(
            item_a=text_a,
            item_b=text_b,
            criteria="Select the text that is more grammatically correct and readable"
        )

        assert result.winner == "A", f"Expected A, got {result.winner}. Reasoning: {result.reasoning}"
        assert result.reasoning
        assert "winner" in result.raw_response

    async def test_compare_numbers(self, langchain_provider):
        """Test comparing numerical values."""
        result = await langchain_provider.compare(
            item_a="100",
            item_b="50",
            criteria="Select the larger number"
        )

        assert result.winner == "A", f"Expected A, got {result.winner}. Reasoning: {result.reasoning}"

    async def test_compare_with_custom_model(self):
        """Test with custom model specification."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0,
        )
        provider = LangChainProvider(llm=llm)

        result = await provider.compare(
            item_a="Python",
            item_b="JavaScript",
            criteria="Which programming language has a simpler syntax for beginners?"
        )

        assert result.winner in ("A", "B")
        assert result.reasoning


@pytest.mark.integration
class TestQualitativeSorterWithOpenAI:
    """Integration tests for QualitativeSorter with OpenAI via LangChain."""

    async def test_sort_three_items(self, langchain_provider):
        """Test sorting three items."""
        sorter = QualitativeSorter(
            provider=langchain_provider,
            criteria="Select the larger number",
            elimination_count=2,
            comparison_rounds=2,
        )

        items = ["10", "50", "30"]
        result = await sorter.sort(items)

        # Check that we got rankings
        assert len(result.rankings) > 0
        assert result.statistics.total_api_calls > 0

        # The first rank should contain "50"
        first_rank_items = result.rankings[0][1]
        assert "50" in first_rank_items, f"Expected '50' in first rank, got {first_rank_items}"

    async def test_sort_with_cache(self, langchain_provider):
        """Test sorting with cache enabled."""
        cache = MemoryCache()
        sorter = QualitativeSorter(
            provider=langchain_provider,
            criteria="Select the larger number",
            elimination_count=2,
            comparison_rounds=2,
            cache=cache,
        )

        items = ["100", "200"]
        result = await sorter.sort(items)

        assert result.statistics.total_api_calls > 0
        # First run should have no cache hits
        first_run_api_calls = result.statistics.total_api_calls

        # Run again - should hit cache
        result2 = await sorter.sort(items)
        assert result2.statistics.cache_hits > 0

    async def test_sort_with_progress_callback(self, langchain_provider):
        """Test that progress events are emitted."""
        events = []

        def on_progress(event):
            events.append(event)

        sorter = QualitativeSorter(
            provider=langchain_provider,
            criteria="Select the larger number",
            elimination_count=2,
            comparison_rounds=2,
            on_progress=on_progress,
        )

        items = ["10", "20"]
        await sorter.sort(items)

        # Should have received events
        assert len(events) > 0

        # Check for expected event types
        event_types = [e.type for e in events]
        assert EventType.MATCH_START in event_types
        assert EventType.MATCH_END in event_types


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling with invalid API keys."""

    async def test_invalid_api_key(self):
        """Test that invalid API key is handled gracefully."""
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key="sk-invalid-key",
            temperature=0,
        )
        provider = LangChainProvider(llm=llm)

        result = await provider.compare(
            item_a="test",
            item_b="test2",
            criteria="test"
        )

        # Should return error result, not raise exception
        assert result.winner is None
        assert "error" in result.raw_response
