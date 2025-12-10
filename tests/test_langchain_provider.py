"""Tests for LangChainProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.langchain import LangChainProvider
from llm_qualitative_sort.models import ComparisonResult, ComparisonResponse


class TestLangChainProvider:
    """Tests for LangChainProvider."""

    def test_inherits_from_llm_provider(self):
        """LangChainProvider should inherit from LLMProvider."""
        assert issubclass(LangChainProvider, LLMProvider)

    def test_create_with_langchain_model(self):
        """Should create provider with any LangChain BaseChatModel."""
        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_llm)

        provider = LangChainProvider(llm=mock_llm)

        assert provider._llm is mock_llm
        mock_llm.with_structured_output.assert_called_once_with(ComparisonResponse)

    def test_stores_original_llm(self):
        """Should store the original LLM for reference."""
        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=MagicMock())

        provider = LangChainProvider(llm=mock_llm)

        assert provider._llm is mock_llm

    def test_creates_structured_llm(self):
        """Should create structured LLM with ComparisonResponse schema."""
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_structured)

        provider = LangChainProvider(llm=mock_llm)

        assert provider._structured_llm is mock_structured


class TestLangChainProviderCompare:
    """Tests for LangChainProvider.compare method."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LangChain LLM."""
        mock = MagicMock()
        mock_structured = AsyncMock()
        mock.with_structured_output = MagicMock(return_value=mock_structured)
        return mock

    @pytest.fixture
    def provider(self, mock_llm):
        """Create a LangChainProvider with mock LLM."""
        return LangChainProvider(llm=mock_llm)

    async def test_compare_returns_comparison_result(self, provider):
        """compare should return ComparisonResult."""
        mock_response = ComparisonResponse(winner="A", reasoning="A is better")
        provider._structured_llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await provider.compare("item1", "item2", "quality")

        assert isinstance(result, ComparisonResult)
        assert result.winner == "A"
        assert result.reasoning == "A is better"

    async def test_compare_calls_ainvoke_with_prompt(self, provider):
        """compare should call ainvoke with the built prompt."""
        mock_response = ComparisonResponse(winner="B", reasoning="B is better")
        provider._structured_llm.ainvoke = AsyncMock(return_value=mock_response)

        await provider.compare("item_a_text", "item_b_text", "test criteria")

        provider._structured_llm.ainvoke.assert_called_once()
        call_args = provider._structured_llm.ainvoke.call_args
        prompt = call_args[0][0]

        assert "item_a_text" in prompt
        assert "item_b_text" in prompt
        assert "test criteria" in prompt

    async def test_compare_winner_b(self, provider):
        """compare should correctly return winner B."""
        mock_response = ComparisonResponse(winner="B", reasoning="B is clearly better")
        provider._structured_llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await provider.compare("weak", "strong", "strength")

        assert result.winner == "B"
        assert result.reasoning == "B is clearly better"

    async def test_compare_includes_raw_response(self, provider):
        """compare should include raw response in result."""
        mock_response = ComparisonResponse(winner="A", reasoning="test")
        provider._structured_llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await provider.compare("a", "b", "criteria")

        assert "winner" in result.raw_response
        assert "reasoning" in result.raw_response

    async def test_compare_handles_exception(self, provider):
        """compare should handle exceptions gracefully."""
        provider._structured_llm.ainvoke = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await provider.compare("a", "b", "criteria")

        assert result.winner is None
        assert "error" in result.raw_response
        assert "API Error" in result.reasoning

    async def test_compare_handles_connection_error(self, provider):
        """compare should handle connection errors gracefully."""
        provider._structured_llm.ainvoke = AsyncMock(
            side_effect=ConnectionError("Connection failed")
        )

        result = await provider.compare("a", "b", "criteria")

        assert result.winner is None
        assert "connection" in result.raw_response.get("error_type", "").lower() or \
               "Connection" in result.reasoning

    async def test_compare_handles_timeout_error(self, provider):
        """compare should handle timeout errors gracefully."""
        import asyncio
        provider._structured_llm.ainvoke = AsyncMock(
            side_effect=asyncio.TimeoutError("Timeout")
        )

        result = await provider.compare("a", "b", "criteria")

        assert result.winner is None


class TestLangChainProviderWithRealModels:
    """Test that provider works with real LangChain model interfaces.

    These tests use mocks that simulate real LangChain model behavior.
    """

    async def test_compatible_with_chat_model_interface(self):
        """Should work with models that implement BaseChatModel interface."""
        # Simulate a LangChain ChatModel
        mock_chat_model = MagicMock()
        mock_structured = AsyncMock()
        mock_structured.ainvoke = AsyncMock(
            return_value=ComparisonResponse(winner="A", reasoning="A wins")
        )
        mock_chat_model.with_structured_output = MagicMock(return_value=mock_structured)

        provider = LangChainProvider(llm=mock_chat_model)
        result = await provider.compare("item1", "item2", "criteria")

        assert result.winner == "A"
        assert result.reasoning == "A wins"

    async def test_structured_output_schema_passed_correctly(self):
        """Should pass ComparisonResponse as the schema for structured output."""
        mock_llm = MagicMock()
        mock_structured = AsyncMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_structured)

        LangChainProvider(llm=mock_llm)

        # Verify the schema was passed correctly
        mock_llm.with_structured_output.assert_called_once()
        call_args = mock_llm.with_structured_output.call_args
        schema = call_args[0][0] if call_args[0] else call_args[1].get('schema')

        assert schema == ComparisonResponse
