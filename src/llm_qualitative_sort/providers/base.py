"""Base class for LLM providers."""

from abc import ABC, abstractmethod

from llm_qualitative_sort.models import ComparisonResult


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Attributes:
        api_key: API key for the provider
        base_url: Base URL for the API endpoint
        model: Model name to use
    """

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "default"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using LLM.

        Args:
            item_a: First item to compare
            item_b: Second item to compare
            criteria: Evaluation criteria

        Returns:
            ComparisonResult with winner, reasoning, and raw response
        """
        pass
