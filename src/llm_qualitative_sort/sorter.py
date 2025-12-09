"""Main QualitativeSorter class."""

import asyncio
import time
from typing import Callable

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.cache import Cache
from llm_qualitative_sort.tournament.multi_elimination import MultiEliminationTournament
from llm_qualitative_sort.models import (
    ComparisonResult,
    RoundResult,
    MatchResult,
    SortResult,
    Statistics,
)
from llm_qualitative_sort.events import EventType, ProgressEvent


class QualitativeSorter:
    """Main class for qualitative sorting using LLM comparisons.

    Uses multi-elimination tournament to rank items based on
    qualitative criteria evaluated by an LLM.

    Attributes:
        provider: LLM provider for comparisons
        elimination_count: Number of losses before elimination (default: 2)
        comparison_rounds: Number of comparison rounds per match (default: 2, must be even)
        criteria: Evaluation criteria for comparisons
        max_concurrent_requests: Maximum concurrent API requests
        cache: Optional cache for comparison results
        on_progress: Optional progress callback function
    """

    def __init__(
        self,
        provider: LLMProvider,
        criteria: str,
        elimination_count: int = 2,
        comparison_rounds: int = 2,
        max_concurrent_requests: int = 10,
        cache: Cache | None = None,
        on_progress: Callable[[ProgressEvent], None] | None = None,
        seed: int | None = None,
    ):
        if comparison_rounds % 2 != 0:
            raise ValueError("comparison_rounds must be even")

        self.provider = provider
        self.criteria = criteria
        self.elimination_count = elimination_count
        self.comparison_rounds = comparison_rounds
        self.max_concurrent_requests = max_concurrent_requests
        self.cache = cache
        self.on_progress = on_progress
        self.seed = seed

        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._total_api_calls = 0
        self._cache_hits = 0

    async def sort(self, items: list[str]) -> SortResult:
        """Sort items using multi-elimination tournament.

        Args:
            items: List of items to sort

        Returns:
            SortResult with rankings, match history, and statistics

        Raises:
            ValueError: If items list is empty or contains invalid items
            TypeError: If items is not a list or contains non-string items
        """
        self._validate_items(items)
        start_time = time.time()
        self._total_api_calls = 0
        self._cache_hits = 0

        tournament = MultiEliminationTournament(
            items=items,
            elimination_count=self.elimination_count,
            seed=self.seed,
        )

        match_history: list[MatchResult] = []
        total_matches = 0
        completed_matches = 0

        # Estimate total matches
        n = len(items)
        estimated_matches = self.elimination_count * n - self.elimination_count

        while not tournament.is_complete():
            matches = tournament.get_next_matches()

            if not matches:
                break

            # Run matches concurrently
            tasks = []
            for item_a, item_b in matches:
                self._emit_progress(
                    EventType.MATCH_START,
                    f"Starting match: {item_a} vs {item_b}",
                    completed_matches,
                    estimated_matches,
                    {"item_a": item_a, "item_b": item_b}
                )
                tasks.append(self._run_match(item_a, item_b))

            results = await asyncio.gather(*tasks)

            for (item_a, item_b), match_result in zip(matches, results):
                match_history.append(match_result)

                # Determine winner
                if match_result.winner == "A":
                    winner = item_a
                elif match_result.winner == "B":
                    winner = item_b
                else:
                    winner = None

                tournament.record_match_result(item_a, item_b, winner)
                completed_matches += 1
                total_matches += 1

                self._emit_progress(
                    EventType.MATCH_END,
                    f"Match complete: {item_a} vs {item_b} -> {winner or 'draw'}",
                    completed_matches,
                    estimated_matches,
                    {"item_a": item_a, "item_b": item_b, "winner": winner}
                )

            self._emit_progress(
                EventType.ROUND_END,
                f"Round complete",
                completed_matches,
                estimated_matches,
                None
            )

        elapsed_time = time.time() - start_time

        statistics = Statistics(
            total_matches=total_matches,
            total_api_calls=self._total_api_calls,
            cache_hits=self._cache_hits,
            elapsed_time=elapsed_time
        )

        return SortResult(
            rankings=tournament.get_rankings(),
            match_history=match_history,
            statistics=statistics
        )

    async def _run_match(self, item_a: str, item_b: str) -> MatchResult:
        """Run a single match between two items.

        Performs multiple comparison rounds with order reversal
        to mitigate position bias.
        """
        rounds: list[RoundResult] = []
        a_wins = 0
        b_wins = 0

        for i in range(self.comparison_rounds):
            # Alternate order to reduce position bias
            if i % 2 == 0:
                order = "AB"
                first, second = item_a, item_b
            else:
                order = "BA"
                first, second = item_b, item_a

            result, cached = await self._compare_with_cache(first, second, order)

            # Translate winner back to original A/B
            actual_winner = self._translate_winner(result.winner, order)

            if actual_winner == "A":
                a_wins += 1
            elif actual_winner == "B":
                b_wins += 1
            # If actual_winner is None (error/draw), neither gets a win

            rounds.append(RoundResult(
                order=order,
                winner=actual_winner,
                reasoning=result.reasoning,
                cached=cached
            ))

        # Determine overall winner
        if a_wins > b_wins:
            winner = "A"
        elif b_wins > a_wins:
            winner = "B"
        else:
            winner = None  # Draw

        return MatchResult(
            item_a=item_a,
            item_b=item_b,
            winner=winner,
            rounds=rounds
        )

    async def _compare_with_cache(
        self,
        item_a: str,
        item_b: str,
        order: str
    ) -> tuple[ComparisonResult, bool]:
        """Compare two items, using cache if available.

        Returns:
            Tuple of (ComparisonResult, cached) where cached is True if from cache.
        """
        # Check cache
        if self.cache:
            cached = await self.cache.get(item_a, item_b, self.criteria, order)
            if cached:
                self._cache_hits += 1
                return cached, True

        # Make API call
        async with self._semaphore:
            result = await self.provider.compare(item_a, item_b, self.criteria)
            self._total_api_calls += 1

        # Store in cache
        if self.cache:
            await self.cache.set(item_a, item_b, self.criteria, order, result)

        return result, False

    def _validate_items(self, items: list[str]) -> None:
        """Validate input items for sorting.

        Args:
            items: List of items to validate

        Raises:
            TypeError: If items is not a list or contains non-string items
            ValueError: If items list is empty or has fewer than 2 items
        """
        if not isinstance(items, list):
            raise TypeError("items must be a list")

        if len(items) < 2:
            raise ValueError("items must contain at least 2 items to sort")

        for i, item in enumerate(items):
            if not isinstance(item, str):
                raise TypeError(f"Item at index {i} is not a string: {type(item).__name__}")

    def _translate_winner(self, winner: str | None, order: str) -> str | None:
        """Translate winner from presentation order to original item order.

        Args:
            winner: The winner as reported ("A", "B", or None)
            order: The presentation order ("AB" or "BA")

        Returns:
            The winner translated to original order, or None if winner is invalid/None.
        """
        if winner not in ("A", "B"):
            return None

        if order == "AB":
            return winner
        # order == "BA": swap A and B
        return "B" if winner == "A" else "A"

    def _emit_progress(
        self,
        event_type: EventType,
        message: str,
        completed: int,
        total: int,
        data: dict | None
    ) -> None:
        """Emit a progress event."""
        if self.on_progress:
            event = ProgressEvent(
                type=event_type,
                message=message,
                completed=completed,
                total=total,
                data=data
            )
            self.on_progress(event)
