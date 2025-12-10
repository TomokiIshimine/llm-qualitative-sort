"""LangChain provider implementation for flexible LLM usage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.errors import create_error_result
from llm_qualitative_sort.models import ComparisonResult, ComparisonResponse

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class LangChainProvider(LLMProvider):
    """LangChain-based provider for LLM comparisons.

    This provider accepts any LangChain BaseChatModel that supports
    structured output via with_structured_output().

    Example usage with different LangChain models:

        # OpenAI
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", api_key="...")
        provider = LangChainProvider(llm=llm)

        # Anthropic
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key="...")
        provider = LangChainProvider(llm=llm)

        # Google
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key="...")
        provider = LangChainProvider(llm=llm)

    Args:
        llm: A LangChain BaseChatModel instance that supports with_structured_output()
    """

    def __init__(self, llm: BaseChatModel) -> None:
        """Initialize the LangChain provider.

        Args:
            llm: A LangChain BaseChatModel that supports structured output.
                 The model should be pre-configured with API keys and settings.
        """
        super().__init__()
        self._llm = llm
        self._structured_llm = llm.with_structured_output(ComparisonResponse)

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using the LangChain model with structured output.

        Args:
            item_a: First item to compare
            item_b: Second item to compare
            criteria: Evaluation criteria

        Returns:
            ComparisonResult with winner, reasoning, and raw response
        """
        prompt = self._build_prompt(item_a, item_b, criteria)

        try:
            response: ComparisonResponse = await self._structured_llm.ainvoke(prompt)

            raw_response = {
                "winner": response.winner,
                "reasoning": response.reasoning,
            }

            return ComparisonResult(
                winner=response.winner,
                reasoning=response.reasoning,
                raw_response=raw_response
            )

        except Exception as e:
            return create_error_result(e, type(e).__name__, str(e))
