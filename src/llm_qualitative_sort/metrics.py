"""Accuracy metrics for sorting evaluation."""

from dataclasses import dataclass

from scipy.stats import kendalltau


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for evaluating sorting quality.

    Attributes:
        kendall_tau: Kendall's tau rank correlation coefficient (-1 to 1)
        top_10_accuracy: Proportion of expected top 10 in actual top 10
        top_50_accuracy: Proportion of expected top 50 in actual top 50
        top_100_accuracy: Proportion of expected top 100 in actual top 100
        correct_pair_ratio: Proportion of pairs in correct relative order
    """

    kendall_tau: float
    top_10_accuracy: float
    top_50_accuracy: float
    top_100_accuracy: float
    correct_pair_ratio: float


def flatten_rankings(rankings: list[tuple[int, list[str]]]) -> list[str]:
    """Flatten rankings into a single ordered list.

    Args:
        rankings: List of (rank, [items]) tuples from SortResult

    Returns:
        Flat list of items in rank order
    """
    result = []
    for _, items in rankings:
        result.extend(items)
    return result


def calculate_kendall_tau(actual: list[str], expected: list[str]) -> float:
    """Calculate Kendall's tau rank correlation coefficient.

    Args:
        actual: Actual ranking (list of items)
        expected: Expected/ground truth ranking

    Returns:
        Kendall's tau value (-1 to 1, 1 = perfect correlation)
    """
    if len(actual) != len(expected):
        raise ValueError("Lists must have same length")

    if len(actual) <= 1:
        return 1.0

    # Create position maps
    actual_pos = {item: i for i, item in enumerate(actual)}
    expected_pos = {item: i for i, item in enumerate(expected)}

    # Convert to numeric ranks for scipy
    actual_ranks = [actual_pos[item] for item in expected]
    expected_ranks = list(range(len(expected)))

    tau, _ = kendalltau(actual_ranks, expected_ranks)
    return tau


def calculate_top_k_accuracy(
    actual: list[str],
    expected: list[str],
    k: int
) -> float:
    """Calculate Top-K accuracy.

    Measures the proportion of expected top-K items that appear
    in the actual top-K positions.

    Args:
        actual: Actual ranking (list of items)
        expected: Expected/ground truth ranking
        k: Number of top items to consider

    Returns:
        Accuracy value (0 to 1)
    """
    # Handle edge cases
    actual_k = min(k, len(actual))
    expected_k = min(k, len(expected))

    if expected_k == 0:
        return 1.0

    actual_top_k = set(actual[:actual_k])
    expected_top_k = set(expected[:expected_k])

    # Count how many expected top-K are in actual top-K
    matches = len(actual_top_k & expected_top_k)
    return matches / expected_k


def calculate_correct_pair_ratio(
    actual: list[str],
    expected: list[str]
) -> float:
    """Calculate the ratio of correctly ordered pairs.

    For all pairs (i, j) where i < j in the expected ranking,
    counts how many are also ordered correctly (i before j) in actual.

    Args:
        actual: Actual ranking (list of items)
        expected: Expected/ground truth ranking

    Returns:
        Ratio of correct pairs (0 to 1)
    """
    if len(actual) <= 1:
        return 1.0

    # Create position map for actual ranking
    actual_pos = {item: i for i, item in enumerate(actual)}

    correct_pairs = 0
    total_pairs = 0

    # Check all pairs from expected ranking
    for i in range(len(expected)):
        for j in range(i + 1, len(expected)):
            item_i = expected[i]
            item_j = expected[j]

            # Skip if items not in actual
            if item_i not in actual_pos or item_j not in actual_pos:
                continue

            total_pairs += 1

            # Check if order is preserved in actual
            if actual_pos[item_i] < actual_pos[item_j]:
                correct_pairs += 1

    if total_pairs == 0:
        return 1.0

    return correct_pairs / total_pairs


def calculate_all_metrics(
    actual: list[str],
    expected: list[str]
) -> AccuracyMetrics:
    """Calculate all accuracy metrics.

    Args:
        actual: Actual ranking (list of items)
        expected: Expected/ground truth ranking

    Returns:
        AccuracyMetrics with all calculated values
    """
    return AccuracyMetrics(
        kendall_tau=calculate_kendall_tau(actual, expected),
        top_10_accuracy=calculate_top_k_accuracy(actual, expected, k=10),
        top_50_accuracy=calculate_top_k_accuracy(actual, expected, k=50),
        top_100_accuracy=calculate_top_k_accuracy(actual, expected, k=100),
        correct_pair_ratio=calculate_correct_pair_ratio(actual, expected),
    )
