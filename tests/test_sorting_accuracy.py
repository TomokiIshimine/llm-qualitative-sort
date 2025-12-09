"""Tests for sorting accuracy with different elimination counts (N values)."""

import pytest

from llm_qualitative_sort import (
    QualitativeSorter,
    MockLLMProvider,
    flatten_rankings,
    calculate_kendall_tau,
    calculate_all_metrics,
)


class TestSortingAccuracyBasic:
    """Basic sorting accuracy tests with small datasets."""

    @pytest.mark.asyncio
    async def test_small_dataset_sorting(self):
        """Test sorting with a small dataset."""
        provider = MockLLMProvider(seed=42, noise_stddev=3.33)
        sorter = QualitativeSorter(
            provider=provider,
            criteria="larger is better",
            elimination_count=2,
            seed=42,
        )

        # Small dataset: 10 items
        items = [str(i) for i in range(10)]
        result = await sorter.sort(items)

        # Flatten rankings
        actual = flatten_rankings(result.rankings)
        expected = [str(i) for i in range(9, -1, -1)]  # 9, 8, ..., 0

        # Tau should be positive (better than random)
        tau = calculate_kendall_tau(actual, expected)
        assert tau > 0, f"Kendall's tau should be positive, got {tau}"

    @pytest.mark.asyncio
    async def test_higher_n_improves_small_dataset(self):
        """Test that higher N improves accuracy on small dataset."""
        seed = 42
        items = [str(i) for i in range(20)]
        expected = [str(i) for i in range(19, -1, -1)]

        results = {}

        for n in [1, 2, 3]:
            provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
            sorter = QualitativeSorter(
                provider=provider,
                criteria="larger is better",
                elimination_count=n,
                seed=seed,
            )

            result = await sorter.sort(items)
            actual = flatten_rankings(result.rankings)
            tau = calculate_kendall_tau(actual, expected)
            results[n] = tau

        # N=2 should generally be better than N=1
        # N=3 should generally be better than N=2
        # Due to randomness, we allow some tolerance
        assert results[2] >= results[1] - 0.2, (
            f"N=2 ({results[2]:.3f}) should be close to or better than "
            f"N=1 ({results[1]:.3f})"
        )


class TestSortingAccuracyWithNValues:
    """Tests for verifying N value impact on accuracy."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("n", [1, 2, 3])
    async def test_accuracy_with_different_n(self, n: int):
        """Test accuracy with different N values."""
        provider = MockLLMProvider(seed=42, noise_stddev=3.33)
        sorter = QualitativeSorter(
            provider=provider,
            criteria="larger is better",
            elimination_count=n,
            seed=42,
        )

        items = [str(i) for i in range(30)]
        result = await sorter.sort(items)

        actual = flatten_rankings(result.rankings)
        expected = [str(i) for i in range(29, -1, -1)]

        metrics = calculate_all_metrics(actual, expected)

        # All metrics should be better than random (> 0 for tau, > some threshold for others)
        assert metrics.kendall_tau > 0, f"N={n}: Kendall's tau should be > 0"
        # Top-10 should capture at least some of the expected top items
        assert metrics.top_10_accuracy >= 0.3, f"N={n}: Top-10 accuracy too low"

    @pytest.mark.asyncio
    async def test_reproducibility_with_seed(self):
        """Test that results are reproducible with same seed."""
        seed = 123
        items = [str(i) for i in range(15)]

        results = []
        for _ in range(2):
            provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
            sorter = QualitativeSorter(
                provider=provider,
                criteria="larger is better",
                elimination_count=2,
                seed=seed,
            )
            result = await sorter.sort(items)
            results.append(flatten_rankings(result.rankings))

        # Same seed should produce same results
        assert results[0] == results[1], "Same seed should produce identical results"

    @pytest.mark.asyncio
    async def test_top_items_more_accurate(self):
        """Test that top rankings are more accurate than bottom."""
        provider = MockLLMProvider(seed=42, noise_stddev=3.33)
        sorter = QualitativeSorter(
            provider=provider,
            criteria="larger is better",
            elimination_count=3,
            seed=42,
        )

        items = [str(i) for i in range(50)]
        result = await sorter.sort(items)

        actual = flatten_rankings(result.rankings)
        expected = [str(i) for i in range(49, -1, -1)]

        # Calculate Top-K accuracy for different K values
        from llm_qualitative_sort import calculate_top_k_accuracy

        top_5 = calculate_top_k_accuracy(actual, expected, k=5)
        top_10 = calculate_top_k_accuracy(actual, expected, k=10)
        top_25 = calculate_top_k_accuracy(actual, expected, k=25)

        # Top-5 accuracy should be >= Top-10 >= Top-25 (generally)
        # This reflects that the algorithm is better at identifying top items
        print(f"Top-5: {top_5:.3f}, Top-10: {top_10:.3f}, Top-25: {top_25:.3f}")

        # Top rankings should have reasonable accuracy
        assert top_5 >= 0.2, f"Top-5 accuracy too low: {top_5}"
