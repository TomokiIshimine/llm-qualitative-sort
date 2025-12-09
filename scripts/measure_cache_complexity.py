#!/usr/bin/env python3
"""Cache complexity measurement script.

This script measures the average computational complexity (number of comparisons)
when using cache functionality in the qualitative sorter.

Metrics measured:
- Total comparisons per run (API calls + cache hits)
- Cache hit rate within single run
- Cache hit rate across multiple runs
- Effect of N (elimination_count) on comparison count

Usage:
    python scripts/measure_cache_complexity.py [--items N] [--seed S] [--runs R]
"""

import asyncio
import argparse
import sys
from dataclasses import dataclass
from typing import Optional

# Add src to path for development
sys.path.insert(0, "src")

from llm_qualitative_sort import (
    QualitativeSorter,
    MockLLMProvider,
)
from llm_qualitative_sort.cache.memory import MemoryCache


@dataclass
class ComplexityResult:
    """Result of a single complexity measurement."""
    n: int  # elimination_count
    run_number: int
    total_matches: int
    total_api_calls: int
    cache_hits: int
    total_comparisons: int  # api_calls + cache_hits
    cache_hit_rate: float


@dataclass
class AggregatedResult:
    """Aggregated results across multiple runs."""
    n: int
    num_runs: int
    avg_matches: float
    avg_api_calls: float
    avg_cache_hits: float
    avg_total_comparisons: float
    avg_cache_hit_rate: float
    # First run (no cache) vs subsequent runs
    first_run_api_calls: int
    subsequent_avg_api_calls: float
    cache_efficiency: float  # reduction in API calls due to cache


async def run_single_sort(
    items: list[str],
    n: int,
    seed: int,
    cache: Optional[MemoryCache],
) -> ComplexityResult:
    """Run a single sort and return complexity metrics."""
    provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
    sorter = QualitativeSorter(
        provider=provider,
        criteria="larger is better",
        elimination_count=n,
        seed=seed,
        cache=cache,
    )

    result = await sorter.sort(items.copy())
    stats = result.statistics

    total_comparisons = stats.total_api_calls + stats.cache_hits
    cache_hit_rate = stats.cache_hits / total_comparisons if total_comparisons > 0 else 0

    return ComplexityResult(
        n=n,
        run_number=0,  # Will be set by caller
        total_matches=stats.total_matches,
        total_api_calls=stats.total_api_calls,
        cache_hits=stats.cache_hits,
        total_comparisons=total_comparisons,
        cache_hit_rate=cache_hit_rate,
    )


async def measure_with_n(
    n: int,
    items: list[str],
    seed: int,
    num_runs: int,
) -> tuple[list[ComplexityResult], AggregatedResult]:
    """Measure complexity for a specific N value across multiple runs."""
    results: list[ComplexityResult] = []

    # Use shared cache across runs
    shared_cache = MemoryCache()

    for run in range(num_runs):
        result = await run_single_sort(items, n, seed, shared_cache)
        result.run_number = run + 1
        results.append(result)

    # Calculate aggregates
    avg_matches = sum(r.total_matches for r in results) / len(results)
    avg_api_calls = sum(r.total_api_calls for r in results) / len(results)
    avg_cache_hits = sum(r.cache_hits for r in results) / len(results)
    avg_total_comparisons = sum(r.total_comparisons for r in results) / len(results)
    avg_cache_hit_rate = sum(r.cache_hit_rate for r in results) / len(results)

    first_run_api_calls = results[0].total_api_calls
    subsequent_runs = results[1:] if len(results) > 1 else results
    subsequent_avg_api_calls = sum(r.total_api_calls for r in subsequent_runs) / len(subsequent_runs)

    cache_efficiency = 1 - (subsequent_avg_api_calls / first_run_api_calls) if first_run_api_calls > 0 else 0

    aggregated = AggregatedResult(
        n=n,
        num_runs=num_runs,
        avg_matches=avg_matches,
        avg_api_calls=avg_api_calls,
        avg_cache_hits=avg_cache_hits,
        avg_total_comparisons=avg_total_comparisons,
        avg_cache_hit_rate=avg_cache_hit_rate,
        first_run_api_calls=first_run_api_calls,
        subsequent_avg_api_calls=subsequent_avg_api_calls,
        cache_efficiency=cache_efficiency,
    )

    return results, aggregated


async def measure_without_cache(
    n: int,
    items: list[str],
    seed: int,
    num_runs: int,
) -> list[ComplexityResult]:
    """Measure complexity without cache for baseline comparison."""
    results: list[ComplexityResult] = []

    for run in range(num_runs):
        result = await run_single_sort(items, n, seed, cache=None)
        result.run_number = run + 1
        results.append(result)

    return results


async def run_measurement(
    num_items: int,
    seed: int,
    num_runs: int,
    max_n: int = 5,
):
    """Run full complexity measurement."""
    print("=" * 80)
    print("Cache Complexity Measurement")
    print("=" * 80)
    print(f"Items: {num_items}")
    print(f"Seed: {seed}")
    print(f"Runs per N: {num_runs}")
    print(f"N values: 1 to {max_n}")
    print(f"Comparison rounds per match: 2 (default)")
    print("=" * 80)
    print()

    items = [str(i) for i in range(num_items)]

    all_results: dict[int, AggregatedResult] = {}
    all_detailed: dict[int, list[ComplexityResult]] = {}
    baseline_results: dict[int, list[ComplexityResult]] = {}

    # Run measurements for each N value
    for n in range(1, max_n + 1):
        print(f"\n--- Measuring N={n} ---")

        # Baseline without cache
        print(f"  Without cache...", end=" ", flush=True)
        baseline = await measure_without_cache(n, items, seed, num_runs)
        baseline_results[n] = baseline
        print(f"avg API calls: {sum(r.total_api_calls for r in baseline) / len(baseline):.1f}")

        # With cache
        print(f"  With cache...", end=" ", flush=True)
        detailed, aggregated = await measure_with_n(n, items, seed, num_runs)
        all_results[n] = aggregated
        all_detailed[n] = detailed
        print(f"avg API calls: {aggregated.avg_api_calls:.1f}, cache efficiency: {aggregated.cache_efficiency:.1%}")

    # Print detailed results
    print("\n")
    print_baseline_comparison(baseline_results, all_results, num_runs)
    print()
    print_detailed_results(all_detailed)
    print()
    print_aggregated_results(all_results)
    print()
    print_analysis(all_results, baseline_results, num_items)


def print_baseline_comparison(
    baseline: dict[int, list[ComplexityResult]],
    with_cache: dict[int, AggregatedResult],
    num_runs: int,
):
    """Print comparison between with and without cache."""
    print("=" * 100)
    print("Baseline Comparison (Without Cache vs With Cache)")
    print("=" * 100)
    print(
        f"{'N':>3} | {'Without Cache':>15} | {'With Cache (avg)':>18} | "
        f"{'Cache Hits (avg)':>18} | {'Reduction':>12}"
    )
    print(f"{'':>3} | {'API Calls':>15} | {'API Calls':>18} | {'':>18} | {'':>12}")
    print("-" * 100)

    for n in sorted(baseline.keys()):
        baseline_avg = sum(r.total_api_calls for r in baseline[n]) / len(baseline[n])
        cached = with_cache[n]
        reduction = (baseline_avg - cached.avg_api_calls) / baseline_avg if baseline_avg > 0 else 0

        print(
            f"{n:>3} | {baseline_avg:>15.1f} | {cached.avg_api_calls:>18.1f} | "
            f"{cached.avg_cache_hits:>18.1f} | {reduction:>11.1%}"
        )

    print("=" * 100)


def print_detailed_results(results: dict[int, list[ComplexityResult]]):
    """Print detailed run-by-run results."""
    print("=" * 100)
    print("Detailed Results (Run-by-Run with Shared Cache)")
    print("=" * 100)

    for n in sorted(results.keys()):
        print(f"\nN={n}:")
        print(
            f"  {'Run':>4} | {'Matches':>8} | {'API Calls':>10} | "
            f"{'Cache Hits':>12} | {'Total Comp.':>12} | {'Hit Rate':>10}"
        )
        print("  " + "-" * 70)

        for r in results[n]:
            print(
                f"  {r.run_number:>4} | {r.total_matches:>8} | {r.total_api_calls:>10} | "
                f"{r.cache_hits:>12} | {r.total_comparisons:>12} | {r.cache_hit_rate:>10.1%}"
            )


def print_aggregated_results(results: dict[int, AggregatedResult]):
    """Print aggregated results table."""
    print("=" * 100)
    print("Aggregated Results Summary")
    print("=" * 100)
    print(
        f"{'N':>3} | {'Avg Matches':>12} | {'Avg API':>10} | {'Avg Cache':>10} | "
        f"{'Avg Total':>10} | {'Hit Rate':>10} | {'Cache Eff.':>12}"
    )
    print(f"{'':>3} | {'':>12} | {'Calls':>10} | {'Hits':>10} | {'Comp.':>10} | {'':>10} | {'':>12}")
    print("-" * 100)

    for n in sorted(results.keys()):
        r = results[n]
        print(
            f"{r.n:>3} | {r.avg_matches:>12.1f} | {r.avg_api_calls:>10.1f} | "
            f"{r.avg_cache_hits:>10.1f} | {r.avg_total_comparisons:>10.1f} | "
            f"{r.avg_cache_hit_rate:>10.1%} | {r.cache_efficiency:>11.1%}"
        )

    print("=" * 100)


def print_analysis(
    results: dict[int, AggregatedResult],
    baseline: dict[int, list[ComplexityResult]],
    num_items: int,
):
    """Print analysis of the results."""
    print("Analysis")
    print("-" * 80)

    # Theoretical complexity
    print("\n1. Theoretical Match Complexity:")
    print(f"   Formula: matches = N * num_items - N = N * (num_items - 1)")
    print(f"   Where N = elimination_count, num_items = {num_items}")

    for n in sorted(results.keys()):
        theoretical = n * (num_items - 1)
        actual = results[n].avg_matches
        print(f"   N={n}: theoretical={theoretical}, actual={actual:.1f}")

    # Comparison complexity
    print("\n2. Comparison Complexity:")
    print("   Each match requires comparison_rounds (default=2) comparisons.")
    print("   Total comparisons = matches * comparison_rounds")

    for n in sorted(results.keys()):
        r = results[n]
        print(f"   N={n}: {r.avg_matches:.1f} matches * 2 = {r.avg_total_comparisons:.1f} comparisons")

    # Cache effectiveness
    print("\n3. Cache Effectiveness Analysis:")
    print("   Cache is effective when the same item pairs are compared again")
    print("   with the same presentation order.")

    for n in sorted(results.keys()):
        r = results[n]
        baseline_avg = sum(b.total_api_calls for b in baseline[n]) / len(baseline[n])
        savings = baseline_avg - r.avg_api_calls
        print(f"   N={n}: {savings:.1f} API calls saved ({r.cache_efficiency:.1%} efficiency)")

    # Average complexity summary
    print("\n4. Average Computational Complexity Summary:")
    print(f"   {'N':>3} | {'Avg Comparisons':>18} | {'Comparisons/Item':>18}")
    print("   " + "-" * 50)
    for n in sorted(results.keys()):
        r = results[n]
        per_item = r.avg_total_comparisons / num_items
        print(f"   {n:>3} | {r.avg_total_comparisons:>18.1f} | {per_item:>18.2f}")

    print("\n5. Key Findings:")
    if len(results) >= 2:
        first_n = min(results.keys())
        last_n = max(results.keys())
        ratio = results[last_n].avg_total_comparisons / results[first_n].avg_total_comparisons
        print(f"   - Comparisons increase {ratio:.1f}x from N={first_n} to N={last_n}")
        print(f"   - N=1 (single elimination): {results[first_n].avg_total_comparisons:.0f} comparisons")
        print(f"   - N={last_n} (multi-elimination): {results[last_n].avg_total_comparisons:.0f} comparisons")

    # Cache hit observation
    any_cache_hits = any(r.avg_cache_hits > 0 for r in results.values())
    if not any_cache_hits:
        print("   - Cache hits within single run are minimal because")
        print("     tournament avoids repeating the same match.")
        print("   - Cache is more effective across multiple sorting runs")
        print("     with the same data (e.g., re-ranking after data changes).")


def main():
    parser = argparse.ArgumentParser(
        description="Measure cache complexity for qualitative sorting"
    )
    parser.add_argument(
        "--items",
        type=int,
        default=30,
        help="Number of items to sort (default: 30)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of runs per N value (default: 3)",
    )
    parser.add_argument(
        "--max-n",
        type=int,
        default=5,
        help="Maximum N value to test (default: 5)",
    )

    args = parser.parse_args()

    asyncio.run(run_measurement(args.items, args.seed, args.runs, args.max_n))


if __name__ == "__main__":
    main()
