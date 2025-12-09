"""Tests for MockLLMProvider."""

import pytest
from llm_qualitative_sort.providers.mock import MockLLMProvider
from llm_qualitative_sort.providers.base import LLMProvider


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    def test_inherits_from_llm_provider(self):
        assert issubclass(MockLLMProvider, LLMProvider)

    def test_create_with_seed(self):
        provider = MockLLMProvider(seed=42)
        assert provider.seed == 42

    def test_create_with_noise_stddev(self):
        provider = MockLLMProvider(noise_stddev=5.0)
        assert provider.noise_stddev == 5.0

    def test_default_noise_stddev(self):
        provider = MockLLMProvider()
        assert provider.noise_stddev == 3.33

    async def test_compare_larger_wins(self):
        # With seed, results should be reproducible
        provider = MockLLMProvider(seed=42, noise_stddev=0.1)
        result = await provider.compare("100", "10", "larger is better")

        # With minimal noise, 100 should almost always beat 10
        assert result.winner == "A"

    async def test_compare_smaller_value(self):
        provider = MockLLMProvider(seed=42, noise_stddev=0.1)
        result = await provider.compare("10", "100", "larger is better")

        # With minimal noise, 10 should lose to 100
        assert result.winner == "B"

    async def test_reproducibility_with_seed(self):
        provider1 = MockLLMProvider(seed=42)
        provider2 = MockLLMProvider(seed=42)

        result1 = await provider1.compare("50", "51", "test")
        result2 = await provider2.compare("50", "51", "test")

        assert result1.winner == result2.winner

    async def test_different_seeds_may_differ(self):
        # Run multiple times to check randomness works
        results = []
        for seed in range(100):
            provider = MockLLMProvider(seed=seed)
            result = await provider.compare("50", "51", "test")
            results.append(result.winner)

        # With similar values and noise, should get both A and B
        assert "A" in results
        assert "B" in results

    async def test_noise_affects_close_comparisons(self):
        # Close values should sometimes flip with noise
        results = {"A": 0, "B": 0}
        for seed in range(100):
            provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
            result = await provider.compare("50", "51", "test")
            results[result.winner] += 1

        # Both should win sometimes (50 and 51 are very close)
        assert results["A"] > 0
        assert results["B"] > 0

    async def test_large_difference_consistent(self):
        # Large value difference should be consistent
        wins_a = 0
        for seed in range(100):
            provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
            result = await provider.compare("900", "100", "test")
            if result.winner == "A":
                wins_a += 1

        # 900 should win almost all the time
        assert wins_a > 95

    async def test_invalid_input_returns_none(self):
        provider = MockLLMProvider(seed=42)
        result = await provider.compare("not_a_number", "100", "test")

        assert result.winner is None

    async def test_raw_response_contains_values(self):
        provider = MockLLMProvider(seed=42)
        result = await provider.compare("50", "100", "test")

        assert "value_a" in result.raw_response
        assert "value_b" in result.raw_response
        assert "item_a" in result.raw_response
        assert "item_b" in result.raw_response
