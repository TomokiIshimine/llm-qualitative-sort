#!/usr/bin/env python3
"""Accuracy evaluation script for different N (elimination_count) values.

This script evaluates sorting accuracy with N values from 1 to 10,
using the MockLLMProvider with Gaussian noise to simulate
qualitative comparison uncertainty.

Usage:
    python scripts/evaluate_accuracy.py [--items N] [--seed S]
"""

import asyncio
import argparse
import sys
import time
from dataclasses import dataclass

# Add src to path for development
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
    metrics: AccuracyMetrics
    total_matches: int
    elapsed_time: float


async def evaluate_with_n(
    n: int,
    items: list[str],
    expected: list[str],
    seed: int,
) -> EvaluationResult:
    """Evaluate sorting accuracy with specific N value."""
    provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
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
        metrics=metrics,
        total_matches=result.statistics.total_matches,
        elapsed_time=elapsed,
    )


async def run_evaluation(num_items: int, seed: int, max_n: int = 10):
    """Run full evaluation with N values from 1 to max_n."""
    print(f"=" * 70)
    print(f"Sorting Accuracy Evaluation")
    print(f"=" * 70)
    print(f"Items: {num_items} (0 to {num_items - 1})")
    print(f"Expected order: {num_items - 1} > {num_items - 2} > ... > 1 > 0 (descending)")
    print(f"Noise: Gaussian with stddev=3.33 (99.7% within +/-10)")
    print(f"Seed: {seed}")
    print(f"N values: 1 to {max_n}")
    print(f"=" * 70)
    print()

    items = [str(i) for i in range(num_items)]
    expected = [str(i) for i in range(num_items - 1, -1, -1)]

    results: list[EvaluationResult] = []

    for n in range(1, max_n + 1):
        print(f"Evaluating N={n}...", end=" ", flush=True)
        result = await evaluate_with_n(n, items, expected, seed)
        results.append(result)
        print(
            f"tau={result.metrics.kendall_tau:.4f}, "
            f"matches={result.total_matches}, "
            f"time={result.elapsed_time:.2f}s"
        )

    print()
    print_results_table(results)
    print()
    print_analysis(results)

    return results


def print_results_table(results: list[EvaluationResult]):
    """Print results in a formatted table."""
    print("=" * 90)
    print("Results Table")
    print("=" * 90)
    print(
        f"{'N':>3} | {'Kendall τ':>10} | {'Top-10':>8} | {'Top-50':>8} | "
        f"{'Top-100':>8} | {'Pair Ratio':>10} | {'Matches':>8}"
    )
    print("-" * 90)

    for r in results:
        m = r.metrics
        print(
            f"{r.n:>3} | {m.kendall_tau:>10.4f} | {m.top_10_accuracy:>8.4f} | "
            f"{m.top_50_accuracy:>8.4f} | {m.top_100_accuracy:>8.4f} | "
            f"{m.correct_pair_ratio:>10.4f} | {r.total_matches:>8}"
        )

    print("=" * 90)


def print_analysis(results: list[EvaluationResult]):
    """Print analysis of the results."""
    print("Analysis")
    print("-" * 50)

    # Check if accuracy improves with N
    taus = [r.metrics.kendall_tau for r in results]

    if len(taus) >= 2:
        improvements = sum(1 for i in range(1, len(taus)) if taus[i] >= taus[i - 1])
        total_comparisons = len(taus) - 1

        print(f"Kendall's tau improvements: {improvements}/{total_comparisons}")
        print(f"N=1 tau: {taus[0]:.4f}")
        print(f"N={len(taus)} tau: {taus[-1]:.4f}")
        print(f"Improvement: {taus[-1] - taus[0]:.4f}")

    # Top-K analysis
    print()
    print("Top-K Accuracy Comparison (N=1 vs N=max):")
    first = results[0].metrics
    last = results[-1].metrics
    print(f"  Top-10:  {first.top_10_accuracy:.4f} -> {last.top_10_accuracy:.4f}")
    print(f"  Top-50:  {first.top_50_accuracy:.4f} -> {last.top_50_accuracy:.4f}")
    print(f"  Top-100: {first.top_100_accuracy:.4f} -> {last.top_100_accuracy:.4f}")

    # Match count analysis
    print()
    print("Match Count Analysis:")
    for r in results:
        expected_min = r.n * len(results[0].metrics.kendall_tau.__class__.__mro__) - r.n
        print(f"  N={r.n}: {r.total_matches} matches")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate sorting accuracy with different N values"
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
        "--max-n",
        type=int,
        default=10,
        help="Maximum N value to test (default: 10)",
    )

    args = parser.parse_args()

    asyncio.run(run_evaluation(args.items, args.seed, args.max_n))


if __name__ == "__main__":
    main()
