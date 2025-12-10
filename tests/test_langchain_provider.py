"""Tests for LangChainProvider."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from llm_qualitative_sort.models import ComparisonResponse, ComparisonResult


class TestLangChainProvider:
    """Tests for LangChainProvider."""

    def test_inherits_from_llm_provider(self):
        """LangChainProvider should inherit from LLMProvider."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider
        from llm_qualitative_sort.providers.base import LLMProvider

        assert issubclass(LangChainProvider, LLMProvider)

    def test_create_with_chat_model(self):
        """Should create provider with a LangChain chat model."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        # Create a mock chat model
        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_model)

        provider = LangChainProvider(chat_model=mock_model)
        assert provider.chat_model is mock_model

    def test_base_class_attributes_set(self):
        """Base class attributes should be set with placeholder values."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_model)

        provider = LangChainProvider(chat_model=mock_model)

        # LangChainProvider doesn't need api_key, but base class requires it
        assert provider.api_key == "langchain"
        assert provider.model == "langchain"

    @pytest.mark.asyncio
    async def test_compare_returns_comparison_result(self):
        """compare() should return a ComparisonResult."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        # Create mock model that supports structured output
        mock_structured_model = AsyncMock()
        mock_structured_model.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="A", reasoning="Item A is better")
        )

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured_model)

        provider = LangChainProvider(chat_model=mock_model)
        result = await provider.compare("item1", "item2", "quality")

        assert isinstance(result, ComparisonResult)
        assert result.winner == "A"
        assert result.reasoning == "Item A is better"

    @pytest.mark.asyncio
    async def test_compare_with_winner_b(self):
        """compare() should correctly return winner B."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        mock_structured_model = AsyncMock()
        mock_structured_model.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="B", reasoning="Item B is superior")
        )

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured_model)

        provider = LangChainProvider(chat_model=mock_model)
        result = await provider.compare("item1", "item2", "quality")

        assert result.winner == "B"
        assert result.reasoning == "Item B is superior"

    @pytest.mark.asyncio
    async def test_compare_passes_prompt_to_model(self):
        """compare() should pass the built prompt to the model."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        mock_structured_model = AsyncMock()
        mock_structured_model.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="A", reasoning="test")
        )

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured_model)

        provider = LangChainProvider(chat_model=mock_model)
        await provider.compare("apple", "banana", "taste")

        # Check that ainvoke was called with the prompt
        mock_structured_model.ainvoke.assert_called_once()
        call_args = mock_structured_model.ainvoke.call_args[0][0]
        assert "apple" in call_args
        assert "banana" in call_args
        assert "taste" in call_args

    @pytest.mark.asyncio
    async def test_compare_raw_response_contains_model_output(self):
        """raw_response should contain the original model output."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        expected_response = ComparisonResponse(winner="A", reasoning="test reasoning")

        mock_structured_model = AsyncMock()
        mock_structured_model.ainvoke = AsyncMock(return_value=expected_response)

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured_model)

        provider = LangChainProvider(chat_model=mock_model)
        result = await provider.compare("item1", "item2", "criteria")

        assert "winner" in result.raw_response
        assert "reasoning" in result.raw_response
        assert result.raw_response["winner"] == "A"
        assert result.raw_response["reasoning"] == "test reasoning"

    @pytest.mark.asyncio
    async def test_compare_handles_exception(self):
        """compare() should handle exceptions and return error result."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        mock_structured_model = AsyncMock()
        mock_structured_model.ainvoke = AsyncMock(side_effect=Exception("API error"))

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured_model)

        provider = LangChainProvider(chat_model=mock_model)
        result = await provider.compare("item1", "item2", "criteria")

        assert result.winner is None
        assert "API error" in result.reasoning
        assert "error" in result.raw_response

    @pytest.mark.asyncio
    async def test_uses_with_structured_output(self):
        """Provider should use with_structured_output for type safety."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        mock_structured_model = AsyncMock()
        mock_structured_model.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="A", reasoning="test")
        )

        mock_model = MagicMock()
        mock_model.with_structured_output = MagicMock(return_value=mock_structured_model)

        provider = LangChainProvider(chat_model=mock_model)
        await provider.compare("item1", "item2", "criteria")

        # Verify with_structured_output was called with ComparisonResponse
        mock_model.with_structured_output.assert_called_once_with(ComparisonResponse)

    def test_export_from_providers_package(self):
        """LangChainProvider should be exported from providers package."""
        from llm_qualitative_sort.providers import LangChainProvider

        assert LangChainProvider is not None

    def test_export_from_main_package(self):
        """LangChainProvider should be exported from main package."""
        from llm_qualitative_sort import LangChainProvider

        assert LangChainProvider is not None


class TestLangChainProviderWithRealModels:
    """Tests that demonstrate usage with real LangChain models (mocked)."""

    @pytest.mark.asyncio
    async def test_usage_pattern_with_openai(self):
        """Demonstrate expected usage pattern with ChatOpenAI."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        # Mock what would be: from langchain_openai import ChatOpenAI
        mock_chat_openai = MagicMock()
        mock_structured = AsyncMock()
        mock_structured.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="A", reasoning="Better quality")
        )
        mock_chat_openai.with_structured_output = MagicMock(return_value=mock_structured)

        # This is how users would use it:
        # chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        # provider = LangChainProvider(chat_model=chat_model)
        provider = LangChainProvider(chat_model=mock_chat_openai)

        result = await provider.compare(
            "Python is great for ML",
            "JavaScript is great for web",
            "which language is better for data science"
        )

        assert result.winner == "A"
        assert result.reasoning == "Better quality"

    @pytest.mark.asyncio
    async def test_usage_pattern_with_anthropic(self):
        """Demonstrate expected usage pattern with ChatAnthropic."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        # Mock what would be: from langchain_anthropic import ChatAnthropic
        mock_chat_anthropic = MagicMock()
        mock_structured = AsyncMock()
        mock_structured.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="B", reasoning="More comprehensive")
        )
        mock_chat_anthropic.with_structured_output = MagicMock(return_value=mock_structured)

        # This is how users would use it:
        # chat_model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        # provider = LangChainProvider(chat_model=chat_model)
        provider = LangChainProvider(chat_model=mock_chat_anthropic)

        result = await provider.compare("item1", "item2", "quality")

        assert result.winner == "B"

    @pytest.mark.asyncio
    async def test_usage_pattern_with_ollama(self):
        """Demonstrate expected usage pattern with ChatOllama (local LLM)."""
        from llm_qualitative_sort.providers.langchain import LangChainProvider

        # Mock what would be: from langchain_ollama import ChatOllama
        mock_chat_ollama = MagicMock()
        mock_structured = AsyncMock()
        mock_structured.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="A", reasoning="Local model choice")
        )
        mock_chat_ollama.with_structured_output = MagicMock(return_value=mock_structured)

        # This is how users would use it:
        # chat_model = ChatOllama(model="llama3.2")
        # provider = LangChainProvider(chat_model=chat_model)
        provider = LangChainProvider(chat_model=mock_chat_ollama)

        result = await provider.compare("item1", "item2", "criteria")

        assert result.winner == "A"
