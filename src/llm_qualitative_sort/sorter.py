"""Main QualitativeSorter class."""

import asyncio
import time
from typing import Callable, Literal

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

# Type aliases for clarity
WinnerType = Literal["A", "B"] | None
OrderType = Literal["AB", "BA"]

# Presentation orders for position bias mitigation
PRESENTATION_ORDERS: tuple[OrderType, OrderType] = ("AB", "BA")


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
    ) -> None:
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

        match_history, total_matches = await self._execute_tournament(tournament, items)

        return SortResult(
            rankings=tournament.get_rankings(),
            match_history=match_history,
            statistics=self._create_statistics(total_matches, start_time)
        )

    async def _execute_tournament(
        self,
        tournament: MultiEliminationTournament,
        items: list[str]
    ) -> tuple[list[MatchResult], int]:
        """Execute all tournament rounds until completion.

        Args:
            tournament: The tournament instance to execute
            items: List of items being sorted

        Returns:
            Tuple of (match_history, total_matches)
        """
        match_history: list[MatchResult] = []
        total_matches = 0
        completed_matches = 0
        estimated_matches = self._estimate_total_matches(len(items))

        while not tournament.is_complete():
            matches = tournament.get_next_matches()
            if not matches:
                break

            results = await self._run_round_matches(
                matches, completed_matches, estimated_matches
            )

            for (item_a, item_b), match_result in zip(matches, results):
                match_history.append(match_result)
                winner = self._determine_winner(item_a, item_b, match_result)
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
                "Round complete",
                completed_matches,
                estimated_matches,
                None
            )

        return match_history, total_matches

    async def _run_round_matches(
        self,
        matches: list[tuple[str, str]],
        completed_matches: int,
        estimated_matches: int
    ) -> list[MatchResult]:
        """Run all matches in a single round concurrently.

        Args:
            matches: List of (item_a, item_b) tuples to compare
            completed_matches: Number of matches completed so far
            estimated_matches: Estimated total matches

        Returns:
            List of MatchResult objects
        """
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

        return await asyncio.gather(*tasks)

    def _estimate_total_matches(self, item_count: int) -> int:
        """Estimate the total number of matches in the tournament.

        Args:
            item_count: Number of items in the tournament

        Returns:
            Estimated number of matches
        """
        return self.elimination_count * item_count - self.elimination_count

    def _determine_winner(
        self,
        item_a: str,
        item_b: str,
        match_result: MatchResult
    ) -> str | None:
        """Determine the actual winner item from a match result.

        Args:
            item_a: First item in the match
            item_b: Second item in the match
            match_result: Result of the match

        Returns:
            The winning item string, or None for a draw
        """
        if match_result.winner == "A":
            return item_a
        elif match_result.winner == "B":
            return item_b
        return None

    def _create_statistics(self, total_matches: int, start_time: float) -> Statistics:
        """Create statistics for the completed sort.

        Args:
            total_matches: Total number of matches executed
            start_time: Timestamp when sorting started

        Returns:
            Statistics object with sort metrics
        """
        return Statistics(
            total_matches=total_matches,
            total_api_calls=self._total_api_calls,
            cache_hits=self._cache_hits,
            elapsed_time=time.time() - start_time
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
            order: OrderType = PRESENTATION_ORDERS[i % 2]
            if order == "AB":
                first, second = item_a, item_b
            else:
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

    def _translate_winner(self, winner: str | None, order: OrderType) -> WinnerType:
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
            return winner  # type: ignore[return-value]
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
