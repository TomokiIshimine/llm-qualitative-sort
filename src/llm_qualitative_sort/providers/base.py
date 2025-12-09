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

    def _build_prompt(self, item_a: str, item_b: str, criteria: str) -> str:
        """Build comparison prompt."""
        return f"""Compare the following two items based on this criteria: {criteria}

Item A:
{item_a}

Item B:
{item_b}

You must respond with ONLY a JSON object in this exact format:
{{"winner": "A" or "B", "reasoning": "your explanation"}}

Choose which item is better based on the criteria. You must pick either A or B."""
