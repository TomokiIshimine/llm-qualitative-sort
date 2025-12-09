#!/usr/bin/env python3
"""Cache complexity measurement script.

This script measures the average computational complexity (number of comparisons)
when using cache functionality in the qualitative sorter.

The cache is designed to reuse comparison results when the same pair
re-matches in the losers bracket (N >= 2).

Metrics measured:
- Total comparisons per single run (API calls + cache hits)
- Cache hit rate within a single tournament run
- Effect of N (elimination_count) on cache effectiveness

Usage:
    python scripts/measure_cache_complexity.py [--items N] [--seed S] [--runs R]
"""

import asyncio
import argparse
import sys
from dataclasses import dataclass

# Add src to path for development
sys.path.insert(0, "src")

from llm_qualitative_sort import (
    QualitativeSorter,
    MockLLMProvider,
)
from llm_qualitative_sort.cache.memory import MemoryCache


@dataclass
class SingleRunResult:
    """Result of a single sorting run."""
    n: int  # elimination_count
    seed: int
    total_matches: int
    total_api_calls: int
    cache_hits: int
    total_comparisons: int  # api_calls + cache_hits
    cache_hit_rate: float
    api_call_reduction: float  # reduction due to cache (cache_hits / total_comparisons)


@dataclass
class AggregatedResult:
    """Aggregated results across multiple independent runs."""
    n: int
    num_runs: int
    avg_matches: float
    avg_api_calls: float
    avg_cache_hits: float
    avg_total_comparisons: float
    avg_cache_hit_rate: float
    avg_api_call_reduction: float
    # Min/Max for variance analysis
    min_cache_hits: int
    max_cache_hits: int


async def run_single_sort_with_fresh_cache(
    items: list[str],
    n: int,
    seed: int,
) -> SingleRunResult:
    """Run a single sort with a fresh cache instance.

    Each run gets its own cache to measure within-run cache effectiveness
    (i.e., losers bracket re-matches).
    """
    # Fresh cache for each run - measures only within-run cache hits
    cache = MemoryCache()

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
    api_call_reduction = stats.cache_hits / total_comparisons if total_comparisons > 0 else 0

    return SingleRunResult(
        n=n,
        seed=seed,
        total_matches=stats.total_matches,
        total_api_calls=stats.total_api_calls,
        cache_hits=stats.cache_hits,
        total_comparisons=total_comparisons,
        cache_hit_rate=cache_hit_rate,
        api_call_reduction=api_call_reduction,
    )


async def run_single_sort_without_cache(
    items: list[str],
    n: int,
    seed: int,
) -> SingleRunResult:
    """Run a single sort without cache for baseline comparison."""
    provider = MockLLMProvider(seed=seed, noise_stddev=3.33)
    sorter = QualitativeSorter(
        provider=provider,
        criteria="larger is better",
        elimination_count=n,
        seed=seed,
        cache=None,  # No cache
    )

    result = await sorter.sort(items.copy())
    stats = result.statistics

    return SingleRunResult(
        n=n,
        seed=seed,
        total_matches=stats.total_matches,
        total_api_calls=stats.total_api_calls,
        cache_hits=0,
        total_comparisons=stats.total_api_calls,
        cache_hit_rate=0,
        api_call_reduction=0,
    )


async def measure_complexity_for_n(
    n: int,
    items: list[str],
    base_seed: int,
    num_runs: int,
) -> tuple[list[SingleRunResult], list[SingleRunResult], AggregatedResult]:
    """Measure complexity for a specific N value across multiple runs.

    Each run uses a different seed to get statistical variance.
    Each run gets a fresh cache instance.
    """
    cached_results: list[SingleRunResult] = []
    nocache_results: list[SingleRunResult] = []

    for i in range(num_runs):
        run_seed = base_seed + i * 1000  # Different seed for each run

        # Run with fresh cache
        cached = await run_single_sort_with_fresh_cache(items, n, run_seed)
        cached_results.append(cached)

        # Run without cache for baseline
        nocache = await run_single_sort_without_cache(items, n, run_seed)
        nocache_results.append(nocache)

    # Calculate aggregates for cached runs
    avg_matches = sum(r.total_matches for r in cached_results) / len(cached_results)
    avg_api_calls = sum(r.total_api_calls for r in cached_results) / len(cached_results)
    avg_cache_hits = sum(r.cache_hits for r in cached_results) / len(cached_results)
    avg_total_comparisons = sum(r.total_comparisons for r in cached_results) / len(cached_results)
    avg_cache_hit_rate = sum(r.cache_hit_rate for r in cached_results) / len(cached_results)
    avg_api_call_reduction = sum(r.api_call_reduction for r in cached_results) / len(cached_results)
    min_cache_hits = min(r.cache_hits for r in cached_results)
    max_cache_hits = max(r.cache_hits for r in cached_results)

    aggregated = AggregatedResult(
        n=n,
        num_runs=num_runs,
        avg_matches=avg_matches,
        avg_api_calls=avg_api_calls,
        avg_cache_hits=avg_cache_hits,
        avg_total_comparisons=avg_total_comparisons,
        avg_cache_hit_rate=avg_cache_hit_rate,
        avg_api_call_reduction=avg_api_call_reduction,
        min_cache_hits=min_cache_hits,
        max_cache_hits=max_cache_hits,
    )

    return cached_results, nocache_results, aggregated


async def run_measurement(
    num_items: int,
    seed: int,
    num_runs: int,
    max_n: int = 5,
):
    """Run full complexity measurement."""
    print("=" * 80)
    print("Cache Complexity Measurement (Single Run Analysis)")
    print("=" * 80)
    print(f"Items: {num_items}")
    print(f"Base seed: {seed}")
    print(f"Independent runs per N: {num_runs}")
    print(f"N values: 1 to {max_n}")
    print(f"Comparison rounds per match: 2 (default)")
    print()
    print("Purpose: Measure cache effectiveness within a single tournament run")
    print("         (losers bracket re-matches reusing previous results)")
    print("=" * 80)
    print()

    items = [str(i) for i in range(num_items)]

    all_cached: dict[int, list[SingleRunResult]] = {}
    all_nocache: dict[int, list[SingleRunResult]] = {}
    all_aggregated: dict[int, AggregatedResult] = {}

    # Run measurements for each N value
    for n in range(1, max_n + 1):
        print(f"Measuring N={n}...", end=" ", flush=True)
        cached, nocache, aggregated = await measure_complexity_for_n(n, items, seed, num_runs)
        all_cached[n] = cached
        all_nocache[n] = nocache
        all_aggregated[n] = aggregated
        print(
            f"avg comparisons={aggregated.avg_total_comparisons:.0f}, "
            f"avg cache hits={aggregated.avg_cache_hits:.1f} "
            f"({aggregated.avg_cache_hit_rate:.1%})"
        )

    # Print results
    print("\n")
    print_summary_table(all_aggregated, num_items)
    print()
    print_detailed_runs(all_cached, all_nocache)
    print()
    print_analysis(all_aggregated, num_items)


def print_summary_table(results: dict[int, AggregatedResult], num_items: int):
    """Print summary table of results."""
    print("=" * 100)
    print("Summary: Average Complexity per Single Run (with Cache)")
    print("=" * 100)
    print(
        f"{'N':>3} | {'Matches':>10} | {'API Calls':>12} | {'Cache Hits':>12} | "
        f"{'Total Comp.':>12} | {'Hit Rate':>10} | {'Saved':>10}"
    )
    print("-" * 100)

    for n in sorted(results.keys()):
        r = results[n]
        saved = r.avg_cache_hits  # Cache hits = API calls saved
        print(
            f"{n:>3} | {r.avg_matches:>10.1f} | {r.avg_api_calls:>12.1f} | "
            f"{r.avg_cache_hits:>12.1f} | {r.avg_total_comparisons:>12.1f} | "
            f"{r.avg_cache_hit_rate:>10.1%} | {saved:>10.1f}"
        )

    print("=" * 100)
    print("Note: Each run uses a fresh cache. Cache hits come from losers bracket re-matches.")


def print_detailed_runs(
    cached: dict[int, list[SingleRunResult]],
    nocache: dict[int, list[SingleRunResult]],
):
    """Print detailed per-run results."""
    print("=" * 100)
    print("Detailed Results: Per-Run Comparison (With Cache vs Without Cache)")
    print("=" * 100)

    for n in sorted(cached.keys()):
        print(f"\nN={n}:")
        print(
            f"  {'Run':>4} | {'Seed':>8} | "
            f"{'With Cache':>35} | {'Without Cache':>15}"
        )
        print(
            f"  {'':>4} | {'':>8} | "
            f"{'API':>8} {'Hits':>8} {'Total':>8} {'Rate':>9} | "
            f"{'API Calls':>15}"
        )
        print("  " + "-" * 90)

        for i, (c, nc) in enumerate(zip(cached[n], nocache[n])):
            print(
                f"  {i+1:>4} | {c.seed:>8} | "
                f"{c.total_api_calls:>8} {c.cache_hits:>8} {c.total_comparisons:>8} {c.cache_hit_rate:>8.1%} | "
                f"{nc.total_api_calls:>15}"
            )


def print_analysis(results: dict[int, AggregatedResult], num_items: int):
    """Print analysis of results."""
    print("=" * 80)
    print("Analysis")
    print("=" * 80)

    print("\n1. Computational Complexity Formula:")
    print(f"   Total comparisons ≈ N × (num_items - 1) × comparison_rounds")
    print(f"   With num_items = {num_items}, comparison_rounds = 2:")
    for n in sorted(results.keys()):
        theoretical = n * (num_items - 1) * 2
        actual = results[n].avg_total_comparisons
        print(f"   N={n}: theoretical ≈ {theoretical}, actual = {actual:.0f}")

    print("\n2. Cache Effectiveness by N:")
    print("   Cache hits occur when the same pair re-matches in losers bracket.")
    print("   Higher N = more rounds in losers bracket = more potential re-matches.")
    print()
    for n in sorted(results.keys()):
        r = results[n]
        print(
            f"   N={n}: {r.avg_cache_hits:.1f} cache hits "
            f"(range: {r.min_cache_hits}-{r.max_cache_hits}), "
            f"saves {r.avg_cache_hit_rate:.1%} of comparisons"
        )

    print("\n3. Key Findings:")
    n1 = results.get(1)
    if n1:
        print(f"   - N=1 (single elimination): {n1.avg_cache_hits:.1f} cache hits")
        print("     (no losers bracket, minimal re-matches)")

    max_n = max(results.keys())
    r_max = results[max_n]
    print(
        f"   - N={max_n}: {r_max.avg_cache_hits:.1f} cache hits, "
        f"reduces API calls by {r_max.avg_cache_hit_rate:.1%}"
    )

    # Compare with/without cache savings
    if len(results) >= 2:
        total_without_cache = sum(r.avg_total_comparisons for r in results.values())
        total_with_cache = sum(r.avg_api_calls for r in results.values())
        overall_savings = (total_without_cache - total_with_cache) / total_without_cache
        print(f"\n   Overall API call reduction with cache: {overall_savings:.1%}")

    print("\n4. Complexity Summary (per item):")
    print(f"   {'N':>3} | {'Comparisons/Item':>18} | {'API Calls/Item':>16}")
    print("   " + "-" * 45)
    for n in sorted(results.keys()):
        r = results[n]
        comp_per_item = r.avg_total_comparisons / num_items
        api_per_item = r.avg_api_calls / num_items
        print(f"   {n:>3} | {comp_per_item:>18.2f} | {api_per_item:>16.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Measure cache complexity for qualitative sorting (single run analysis)"
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
        help="Base random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of independent runs per N value (default: 5)",
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
