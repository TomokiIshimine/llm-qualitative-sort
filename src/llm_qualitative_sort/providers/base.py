"""Base class for LLM providers."""

from abc import ABC, abstractmethod

from llm_qualitative_sort.models import ComparisonResult


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    This class provides a common interface for all LLM providers.
    Subclasses can implement their own initialization logic.
    """

    def __init__(self) -> None:
        """Initialize the provider.

        Subclasses should override this with their specific initialization.
        """
        pass

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
        """Build comparison prompt.

        Note: JSON format instructions are not needed here because
        Structured Outputs guarantee the response format via API parameters.
        """
        return f"""Compare the following two items based on this criteria: {criteria}

Item A:
{item_a}

Item B:
{item_b}

Choose which item is better based on the criteria. You must pick either A or B.
Provide your reasoning for the choice."""
