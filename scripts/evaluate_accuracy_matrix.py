#!/usr/bin/env python3
"""Accuracy evaluation with N value and noise variance matrix.

This script evaluates sorting accuracy across different combinations of:
- N values (elimination_count): 1 to max_n
- Noise standard deviation: controls comparison randomness

Higher noise = more uncertainty in each comparison (simulating qualitative evaluation)

Usage:
    python scripts/evaluate_accuracy_matrix.py [--items N] [--seed S]
"""

import asyncio
import argparse
import sys
import time
from dataclasses import dataclass

sys.path.insert(0, "src")

from llm_qualitative_sort import (
    QualitativeSorter,
    MockLLMProvider,
    flatten_rankings,
    calculate_all_metrics,
    AccuracyMetrics,
)


@dataclass
class EvaluationResult:
    """Result of a single evaluation run."""

    n: int
    noise_stddev: float
    metrics: AccuracyMetrics
    total_matches: int
    elapsed_time: float


async def evaluate_single(
    n: int,
    noise_stddev: float,
    items: list[str],
    expected: list[str],
    seed: int,
) -> EvaluationResult:
    """Evaluate sorting accuracy with specific N and noise values."""
    provider = MockLLMProvider(seed=seed, noise_stddev=noise_stddev)
    sorter = QualitativeSorter(
        provider=provider,
        criteria="larger is better",
        elimination_count=n,
        seed=seed,
    )

    start = time.time()
    result = await sorter.sort(items.copy())
    elapsed = time.time() - start

    actual = flatten_rankings(result.rankings)
    metrics = calculate_all_metrics(actual, expected)

    return EvaluationResult(
        n=n,
        noise_stddev=noise_stddev,
        metrics=metrics,
        total_matches=result.statistics.total_matches,
        elapsed_time=elapsed,
    )


async def run_matrix_evaluation(
    num_items: int,
    seed: int,
    n_values: list[int],
    noise_values: list[float],
):
    """Run evaluation across N x noise_stddev matrix."""
    print("=" * 80)
    print("Sorting Accuracy Matrix Evaluation")
    print("=" * 80)
    print(f"Items: {num_items} (0 to {num_items - 1})")
    print(f"Expected order: {num_items - 1} > ... > 0 (descending)")
    print(f"Seed: {seed}")
    print(f"N values: {n_values}")
    print(f"Noise stddev values: {noise_values}")
    print()
    print("Noise interpretation:")
    print("  - stddev=3.33: ~99.7% of noise within ±10 (low randomness)")
    print("  - stddev=10:   ~99.7% of noise within ±30 (medium randomness)")
    print("  - stddev=33.3: ~99.7% of noise within ±100 (high randomness)")
    print("=" * 80)
    print()

    items = [str(i) for i in range(num_items)]
    expected = [str(i) for i in range(num_items - 1, -1, -1)]

    # Store results in a matrix
    results: dict[tuple[int, float], EvaluationResult] = {}

    total_runs = len(n_values) * len(noise_values)
    current_run = 0

    for noise in noise_values:
        for n in n_values:
            current_run += 1
            print(f"[{current_run}/{total_runs}] N={n}, noise_stddev={noise}...", end=" ", flush=True)
            result = await evaluate_single(n, noise, items, expected, seed)
            results[(n, noise)] = result
            print(f"tau={result.metrics.kendall_tau:.4f}")

    print()
    print_kendall_tau_matrix(results, n_values, noise_values)
    print()
    print_top_k_matrices(results, n_values, noise_values)
    print()
    print_correct_pair_matrix(results, n_values, noise_values)
    print()
    print_analysis(results, n_values, noise_values)

    return results


def print_kendall_tau_matrix(
    results: dict[tuple[int, float], EvaluationResult],
    n_values: list[int],
    noise_values: list[float],
):
    """Print Kendall's tau as a matrix."""
    print("=" * 80)
    print("Kendall's Tau Matrix (rows=noise_stddev, cols=N)")
    print("=" * 80)

    # Header
    header = "noise\\N |"
    for n in n_values:
        header += f" N={n:2d} |"
    print(header)
    print("-" * len(header))

    # Rows
    for noise in noise_values:
        row = f"{noise:6.1f} |"
        for n in n_values:
            tau = results[(n, noise)].metrics.kendall_tau
            row += f" {tau:5.3f} |"
        print(row)

    print("=" * 80)


def print_top_k_matrices(
    results: dict[tuple[int, float], EvaluationResult],
    n_values: list[int],
    noise_values: list[float],
):
    """Print Top-K accuracy matrices."""
    for k, attr in [(10, "top_10_accuracy"), (50, "top_50_accuracy"), (100, "top_100_accuracy")]:
        print(f"Top-{k} Accuracy Matrix (rows=noise_stddev, cols=N)")
        print("-" * 60)

        header = "noise\\N |"
        for n in n_values:
            header += f" N={n:2d} |"
        print(header)
        print("-" * len(header))

        for noise in noise_values:
            row = f"{noise:6.1f} |"
            for n in n_values:
                val = getattr(results[(n, noise)].metrics, attr)
                row += f" {val:5.3f} |"
            print(row)
        print()


def print_correct_pair_matrix(
    results: dict[tuple[int, float], EvaluationResult],
    n_values: list[int],
    noise_values: list[float],
):
    """Print correct pair ratio matrix."""
    print("=" * 80)
    print("Correct Pair Ratio Matrix (rows=noise_stddev, cols=N)")
    print("=" * 80)

    header = "noise\\N |"
    for n in n_values:
        header += f" N={n:2d} |"
    print(header)
    print("-" * len(header))

    for noise in noise_values:
        row = f"{noise:6.1f} |"
        for n in n_values:
            ratio = results[(n, noise)].metrics.correct_pair_ratio
            row += f" {ratio:5.3f} |"
        print(row)

    print("=" * 80)


def print_analysis(
    results: dict[tuple[int, float], EvaluationResult],
    n_values: list[int],
    noise_values: list[float],
):
    """Print analysis of the results."""
    print("=" * 80)
    print("Analysis")
    print("=" * 80)

    # Effect of N (averaged across noise levels)
    print("\n1. Effect of N value (averaged across noise levels):")
    for n in n_values:
        avg_tau = sum(results[(n, noise)].metrics.kendall_tau for noise in noise_values) / len(noise_values)
        avg_pair = sum(results[(n, noise)].metrics.correct_pair_ratio for noise in noise_values) / len(noise_values)
        print(f"   N={n:2d}: avg_tau={avg_tau:.4f}, avg_pair_ratio={avg_pair:.4f}")

    # Effect of noise (averaged across N values)
    print("\n2. Effect of noise (averaged across N values):")
    for noise in noise_values:
        avg_tau = sum(results[(n, noise)].metrics.kendall_tau for n in n_values) / len(n_values)
        avg_pair = sum(results[(n, noise)].metrics.correct_pair_ratio for n in n_values) / len(n_values)
        print(f"   noise={noise:5.1f}: avg_tau={avg_tau:.4f}, avg_pair_ratio={avg_pair:.4f}")

    # Best and worst combinations
    print("\n3. Best and worst combinations:")
    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1].metrics.kendall_tau,
        reverse=True
    )
    best = sorted_results[0]
    worst = sorted_results[-1]
    print(f"   Best:  N={best[0][0]}, noise={best[0][1]:.1f} -> tau={best[1].metrics.kendall_tau:.4f}")
    print(f"   Worst: N={worst[0][0]}, noise={worst[0][1]:.1f} -> tau={worst[1].metrics.kendall_tau:.4f}")

    # How much N helps at high noise
    print("\n4. N value benefit at different noise levels:")
    for noise in noise_values:
        tau_n1 = results[(n_values[0], noise)].metrics.kendall_tau
        tau_nmax = results[(n_values[-1], noise)].metrics.kendall_tau
        improvement = tau_nmax - tau_n1
        print(f"   noise={noise:5.1f}: N={n_values[0]}->N={n_values[-1]} improvement = {improvement:+.4f}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate sorting accuracy across N and noise variance matrix"
    )
    parser.add_argument(
        "--items",
        type=int,
        default=100,
        help="Number of items to sort (default: 100)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--n-values",
        type=str,
        default="1,2,3,5,7,10",
        help="Comma-separated N values to test (default: 1,2,3,5,7,10)",
    )
    parser.add_argument(
        "--noise-values",
        type=str,
        default="3.33,10,20,33.3,50",
        help="Comma-separated noise stddev values (default: 3.33,10,20,33.3,50)",
    )

    args = parser.parse_args()

    n_values = [int(x.strip()) for x in args.n_values.split(",")]
    noise_values = [float(x.strip()) for x in args.noise_values.split(",")]

    asyncio.run(run_matrix_evaluation(args.items, args.seed, n_values, noise_values))


if __name__ == "__main__":
    main()
