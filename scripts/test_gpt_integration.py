"""Integration test script for OpenAI GPT provider.

This script tests the QualitativeSorter with actual OpenAI API calls.
Requires OPENAI_API_KEY environment variable to be set.
"""

import asyncio
import os
import sys

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_qualitative_sort import (
    QualitativeSorter,
    OpenAIProvider,
    MemoryCache,
    ProgressEvent,
    to_ranking,
)


def progress_callback(event: ProgressEvent) -> None:
    """Print progress events."""
    print(f"[{event.type.value}] {event.message} ({event.completed}/{event.total})")


async def test_number_sorting():
    """Test sorting numbers by their value (simple, verifiable test)."""
    print("\n" + "=" * 60)
    print("Test 1: Number Sorting")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return False

    provider = OpenAIProvider(api_key=api_key)
    cache = MemoryCache()

    # Test data: numbers as strings
    items = ["5", "2", "8", "1", "9", "3"]
    expected_order = ["9", "8", "5", "3", "2", "1"]  # Descending order

    sorter = QualitativeSorter(
        provider=provider,
        criteria="Compare these two numbers. Choose the LARGER number. Return JSON with 'winner' ('A' or 'B') and 'reasoning'.",
        elimination_count=2,
        comparison_rounds=2,
        max_concurrent_requests=3,
        cache=cache,
        on_progress=progress_callback,
    )

    print(f"Items to sort: {items}")
    print(f"Expected order (largest first): {expected_order}")
    print()

    result = await sorter.sort(items)

    print("\n--- Results ---")
    print(f"Rankings: {result.rankings}")
    print(f"Total matches: {result.statistics.total_matches}")
    print(f"Total API calls: {result.statistics.total_api_calls}")
    print(f"Cache hits: {result.statistics.cache_hits}")
    print(f"Elapsed time: {result.statistics.elapsed_time:.2f}s")

    # Convert to ranking output
    ranking_output = to_ranking(result)
    print("\nRanking output:")
    for entry in ranking_output.entries:
        print(f"  Rank {entry.rank}: {entry.item}")

    # Check accuracy
    actual_top3 = [r[0] for r in result.rankings[:3]]
    expected_top3 = expected_order[:3]

    print(f"\nExpected top 3: {expected_top3}")
    print(f"Actual top 3: {actual_top3}")

    return True


async def test_programming_language_sorting():
    """Test sorting programming languages by popularity (subjective test)."""
    print("\n" + "=" * 60)
    print("Test 2: Programming Language Popularity")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return False

    provider = OpenAIProvider(api_key=api_key)
    cache = MemoryCache()

    # Test data: programming languages
    items = ["Python", "JavaScript", "Rust", "Go", "COBOL"]

    sorter = QualitativeSorter(
        provider=provider,
        criteria="Compare these two programming languages by their current popularity and usage in 2024. Choose the MORE POPULAR language. Return JSON with 'winner' ('A' or 'B') and 'reasoning'.",
        elimination_count=2,
        comparison_rounds=2,
        max_concurrent_requests=3,
        cache=cache,
        on_progress=progress_callback,
    )

    print(f"Items to sort: {items}")
    print()

    result = await sorter.sort(items)

    print("\n--- Results ---")
    print(f"Rankings: {result.rankings}")
    print(f"Total matches: {result.statistics.total_matches}")
    print(f"Total API calls: {result.statistics.total_api_calls}")
    print(f"Elapsed time: {result.statistics.elapsed_time:.2f}s")

    # Convert to ranking output
    ranking_output = to_ranking(result)
    print("\nRanking output:")
    for entry in ranking_output.entries:
        print(f"  Rank {entry.rank}: {entry.item}")

    # Show some match details
    print("\nSample match reasoning:")
    for i, match in enumerate(result.match_history[:2]):
        print(f"\n  Match {i+1}: {match.item_a} vs {match.item_b}")
        print(f"  Winner: {match.winner}")
        for j, round_result in enumerate(match.rounds):
            print(f"    Round {j+1} ({round_result.order}): {round_result.winner}")
            print(f"      Reasoning: {round_result.reasoning[:100]}...")

    return True


async def test_anime_character_strength():
    """Test sorting anime characters by strength."""
    print("\n" + "=" * 60)
    print("Test 3: Anime Character Strength")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return False

    provider = OpenAIProvider(api_key=api_key)
    cache = MemoryCache()

    # Test data: anime characters
    items = [
        "Goku (Dragon Ball)",
        "Naruto Uzumaki (Naruto)",
        "Monkey D. Luffy (One Piece)",
        "Saitama (One Punch Man)",
        "Tanjiro Kamado (Demon Slayer)",
    ]

    sorter = QualitativeSorter(
        provider=provider,
        criteria="Compare the strength/power level of these two anime characters at their peak. Choose the STRONGER character. Return JSON with 'winner' ('A' or 'B') and 'reasoning'.",
        elimination_count=2,
        comparison_rounds=2,
        max_concurrent_requests=3,
        cache=cache,
        on_progress=progress_callback,
    )

    print(f"Items to sort: {items}")
    print()

    result = await sorter.sort(items)

    print("\n--- Results ---")
    print(f"Rankings: {result.rankings}")
    print(f"Total matches: {result.statistics.total_matches}")
    print(f"Total API calls: {result.statistics.total_api_calls}")
    print(f"Elapsed time: {result.statistics.elapsed_time:.2f}s")

    # Convert to ranking output
    ranking_output = to_ranking(result)
    print("\nStrength Ranking:")
    for entry in ranking_output.entries:
        print(f"  #{entry.rank}: {entry.item}")

    return True


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("OpenAI GPT Integration Test")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")

    tests = [
        ("Number Sorting", test_number_sorting),
        ("Programming Language Popularity", test_programming_language_sorting),
        ("Anime Character Strength", test_anime_character_strength),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
