"""Tests for accuracy metrics calculation functions."""

import pytest
from scipy.stats import kendalltau

from llm_qualitative_sort.metrics import (
    flatten_rankings,
    calculate_kendall_tau,
    calculate_top_k_accuracy,
    calculate_correct_pair_ratio,
    AccuracyMetrics,
    calculate_all_metrics,
)


class TestFlattenRankings:
    """Tests for flatten_rankings function."""

    def test_flatten_single_rank(self):
        """Single rank with multiple items."""
        rankings = [(1, ["a", "b", "c"])]
        result = flatten_rankings(rankings)
        assert result == ["a", "b", "c"]

    def test_flatten_multiple_ranks(self):
        """Multiple ranks with single items."""
        rankings = [(1, ["a"]), (2, ["b"]), (3, ["c"])]
        result = flatten_rankings(rankings)
        assert result == ["a", "b", "c"]

    def test_flatten_mixed_ranks(self):
        """Mixed ranks with varying item counts."""
        rankings = [(1, ["a"]), (2, ["b", "c"]), (4, ["d"])]
        result = flatten_rankings(rankings)
        assert result == ["a", "b", "c", "d"]

    def test_flatten_empty(self):
        """Empty rankings."""
        rankings = []
        result = flatten_rankings(rankings)
        assert result == []


class TestKendallTau:
    """Tests for Kendall's tau calculation."""

    def test_perfect_correlation(self):
        """Perfect positive correlation (identical rankings)."""
        actual = ["999", "998", "997", "996", "995"]
        expected = ["999", "998", "997", "996", "995"]
        tau = calculate_kendall_tau(actual, expected)
        assert tau == pytest.approx(1.0)

    def test_perfect_negative_correlation(self):
        """Perfect negative correlation (reversed rankings)."""
        actual = ["995", "996", "997", "998", "999"]
        expected = ["999", "998", "997", "996", "995"]
        tau = calculate_kendall_tau(actual, expected)
        assert tau == pytest.approx(-1.0)

    def test_partial_correlation(self):
        """Partial correlation."""
        actual = ["999", "997", "998", "996", "995"]  # One swap
        expected = ["999", "998", "997", "996", "995"]
        tau = calculate_kendall_tau(actual, expected)
        # tau should be between -1 and 1, closer to 1
        assert -1.0 <= tau <= 1.0
        assert tau > 0.5

    def test_with_integer_strings(self):
        """Works with integer strings as expected."""
        actual = [str(i) for i in range(999, 994, -1)]  # ["999", "998", ...]
        expected = [str(i) for i in range(999, 994, -1)]
        tau = calculate_kendall_tau(actual, expected)
        assert tau == pytest.approx(1.0)


class TestTopKAccuracy:
    """Tests for Top-K accuracy calculation."""

    def test_perfect_top_10(self):
        """Perfect accuracy for top 10."""
        actual = [str(i) for i in range(999, 989, -1)]  # 999, 998, ..., 990
        expected = [str(i) for i in range(999, -1, -1)]  # 999, 998, ..., 0
        accuracy = calculate_top_k_accuracy(actual, expected, k=10)
        assert accuracy == pytest.approx(1.0)

    def test_perfect_top_10_different_order(self):
        """Top-10 items all present but in different order."""
        # Actual has top 10 items but slightly different order
        actual = ["998", "999", "997", "996", "995", "994", "993", "992", "991", "990"]
        expected = [str(i) for i in range(999, -1, -1)]
        accuracy = calculate_top_k_accuracy(actual, expected, k=10)
        assert accuracy == pytest.approx(1.0)

    def test_partial_top_10(self):
        """Partial accuracy for top 10."""
        # Only 5 of top 10 expected items in actual top 10
        actual = ["999", "998", "997", "996", "995", "100", "101", "102", "103", "104"]
        expected = [str(i) for i in range(999, -1, -1)]
        accuracy = calculate_top_k_accuracy(actual, expected, k=10)
        assert accuracy == pytest.approx(0.5)

    def test_zero_top_k(self):
        """Zero accuracy (none of expected top K in actual top K)."""
        actual = [str(i) for i in range(100)]  # 0, 1, ..., 99
        expected = [str(i) for i in range(999, -1, -1)]  # 999, 998, ..., 0
        accuracy = calculate_top_k_accuracy(actual, expected, k=10)
        assert accuracy == pytest.approx(0.0)

    def test_k_larger_than_list(self):
        """K larger than list length."""
        actual = ["999", "998", "997"]
        expected = ["999", "998", "997"]
        accuracy = calculate_top_k_accuracy(actual, expected, k=10)
        assert accuracy == pytest.approx(1.0)


class TestCorrectPairRatio:
    """Tests for correct pair ratio calculation."""

    def test_perfect_ratio(self):
        """All pairs in correct order."""
        actual = ["999", "998", "997", "996"]
        expected = ["999", "998", "997", "996"]
        ratio = calculate_correct_pair_ratio(actual, expected)
        assert ratio == pytest.approx(1.0)

    def test_reversed_ratio(self):
        """All pairs in reverse order."""
        actual = ["996", "997", "998", "999"]
        expected = ["999", "998", "997", "996"]
        ratio = calculate_correct_pair_ratio(actual, expected)
        assert ratio == pytest.approx(0.0)

    def test_partial_ratio(self):
        """Some pairs correct, some incorrect."""
        actual = ["999", "997", "998", "996"]  # One adjacent swap
        expected = ["999", "998", "997", "996"]
        ratio = calculate_correct_pair_ratio(actual, expected)
        # 6 total pairs, 5 correct (only 997-998 is wrong)
        assert 0.0 < ratio < 1.0
        assert ratio == pytest.approx(5/6)

    def test_single_element(self):
        """Single element (no pairs)."""
        actual = ["999"]
        expected = ["999"]
        ratio = calculate_correct_pair_ratio(actual, expected)
        assert ratio == pytest.approx(1.0)

    def test_two_elements_correct(self):
        """Two elements in correct order."""
        actual = ["999", "998"]
        expected = ["999", "998"]
        ratio = calculate_correct_pair_ratio(actual, expected)
        assert ratio == pytest.approx(1.0)

    def test_two_elements_incorrect(self):
        """Two elements in incorrect order."""
        actual = ["998", "999"]
        expected = ["999", "998"]
        ratio = calculate_correct_pair_ratio(actual, expected)
        assert ratio == pytest.approx(0.0)


class TestAccuracyMetrics:
    """Tests for AccuracyMetrics dataclass."""

    def test_dataclass_creation(self):
        """AccuracyMetrics can be created with all fields."""
        metrics = AccuracyMetrics(
            kendall_tau=0.95,
            top_10_accuracy=1.0,
            top_50_accuracy=0.98,
            top_100_accuracy=0.95,
            correct_pair_ratio=0.97,
        )
        assert metrics.kendall_tau == 0.95
        assert metrics.top_10_accuracy == 1.0
        assert metrics.top_50_accuracy == 0.98
        assert metrics.top_100_accuracy == 0.95
        assert metrics.correct_pair_ratio == 0.97


class TestCalculateAllMetrics:
    """Tests for calculate_all_metrics function."""

    def test_calculate_all_metrics_perfect(self):
        """Calculate all metrics for perfect ranking."""
        actual = [str(i) for i in range(999, -1, -1)]
        expected = [str(i) for i in range(999, -1, -1)]

        metrics = calculate_all_metrics(actual, expected)

        assert metrics.kendall_tau == pytest.approx(1.0)
        assert metrics.top_10_accuracy == pytest.approx(1.0)
        assert metrics.top_50_accuracy == pytest.approx(1.0)
        assert metrics.top_100_accuracy == pytest.approx(1.0)
        assert metrics.correct_pair_ratio == pytest.approx(1.0)

    def test_calculate_all_metrics_reversed(self):
        """Calculate all metrics for reversed ranking."""
        actual = [str(i) for i in range(1000)]  # 0, 1, 2, ..., 999
        expected = [str(i) for i in range(999, -1, -1)]  # 999, 998, ..., 0

        metrics = calculate_all_metrics(actual, expected)

        assert metrics.kendall_tau == pytest.approx(-1.0)
        assert metrics.top_10_accuracy == pytest.approx(0.0)
        assert metrics.top_50_accuracy == pytest.approx(0.0)
        assert metrics.top_100_accuracy == pytest.approx(0.0)
        assert metrics.correct_pair_ratio == pytest.approx(0.0)
