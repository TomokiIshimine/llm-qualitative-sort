"""Mock LLM provider for testing."""

import random

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.models import ComparisonResult


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing.

    Compares numeric strings with Gaussian noise to simulate
    the uncertainty of qualitative comparisons.

    Attributes:
        seed: Random seed for reproducibility
        noise_stddev: Standard deviation of Gaussian noise (default: 3.33)
    """

    def __init__(
        self,
        seed: int | None = None,
        noise_stddev: float = 3.33
    ):
        super().__init__(api_key="mock", base_url=None, model="mock")
        self.seed = seed
        self.noise_stddev = noise_stddev
        self._rng = random.Random(seed)

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using mock numeric comparison with noise.

        Items are parsed as integers and compared with Gaussian noise.
        """
        try:
            value_a = int(item_a) + self._rng.gauss(0, self.noise_stddev)
            value_b = int(item_b) + self._rng.gauss(0, self.noise_stddev)

            winner = "A" if value_a > value_b else "B"
            reasoning = f"Compared {item_a} vs {item_b} with noise"

            return ComparisonResult(
                winner=winner,
                reasoning=reasoning,
                raw_response={
                    "value_a": value_a,
                    "value_b": value_b,
                    "item_a": item_a,
                    "item_b": item_b,
                }
            )
        except ValueError as e:
            return ComparisonResult(
                winner=None,
                reasoning=f"Failed to parse items as integers: {e}",
                raw_response={"error": str(e)}
            )
