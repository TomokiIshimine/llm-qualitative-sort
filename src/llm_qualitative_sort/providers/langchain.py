"""LangChain provider for LLM Qualitative Sort.

This provider allows using any LangChain-compatible chat model for comparisons.
It leverages LangChain's with_structured_output() for reliable JSON responses.

Example usage:
    from langchain_openai import ChatOpenAI
    from llm_qualitative_sort import LangChainProvider, QualitativeSorter

    # Use with ChatOpenAI
    chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    provider = LangChainProvider(chat_model=chat_model)

    # Use with ChatAnthropic
    from langchain_anthropic import ChatAnthropic
    chat_model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    provider = LangChainProvider(chat_model=chat_model)

    # Use with ChatOllama (local models)
    from langchain_ollama import ChatOllama
    chat_model = ChatOllama(model="llama3.2")
    provider = LangChainProvider(chat_model=chat_model)

    # Then use with QualitativeSorter as usual
    sorter = QualitativeSorter(provider=provider, criteria="your criteria")
"""

from typing import Any

from llm_qualitative_sort.models import ComparisonResponse, ComparisonResult
from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.errors import create_error_result


class LangChainProvider(LLMProvider):
    """LLM provider using LangChain chat models.

    This provider wraps any LangChain-compatible chat model (BaseChatModel)
    and uses with_structured_output() for reliable structured responses.

    Attributes:
        chat_model: LangChain chat model instance (e.g., ChatOpenAI, ChatAnthropic)
    """

    def __init__(self, chat_model: Any) -> None:
        """Initialize with a LangChain chat model.

        Args:
            chat_model: A LangChain BaseChatModel instance that supports
                        with_structured_output(). Examples include:
                        - ChatOpenAI from langchain_openai
                        - ChatAnthropic from langchain_anthropic
                        - ChatOllama from langchain_ollama
                        - ChatGoogleGenerativeAI from langchain_google_genai
                        - AzureChatOpenAI from langchain_openai
                        - ChatBedrock from langchain_aws
        """
        # Call parent with placeholder values since LangChain models
        # handle their own authentication and configuration
        super().__init__(
            api_key="langchain",
            base_url=None,
            model="langchain",
        )
        self.chat_model = chat_model
        # Create structured output model once for reuse
        self._structured_model = chat_model.with_structured_output(ComparisonResponse)

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using the LangChain chat model.

        Args:
            item_a: First item to compare
            item_b: Second item to compare
            criteria: Evaluation criteria

        Returns:
            ComparisonResult with winner, reasoning, and raw response
        """
        prompt = self._build_prompt(item_a, item_b, criteria)

        try:
            # Use ainvoke for async call with structured output
            response: ComparisonResponse = await self._structured_model.ainvoke(prompt)

            return ComparisonResult(
                winner=response.winner,
                reasoning=response.reasoning,
                raw_response={
                    "winner": response.winner,
                    "reasoning": response.reasoning,
                },
            )

        except Exception as e:
            return create_error_result(
                e,
                error_type="langchain_error",
                prefix="LangChain error",
            )
