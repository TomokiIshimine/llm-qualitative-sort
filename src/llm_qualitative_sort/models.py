"""Data structures for LLM Qualitative Sort."""

from dataclasses import dataclass


@dataclass
class ComparisonResult:
    """Result of a single LLM comparison.

    Attributes:
        winner: "A", "B", or None (error)
        reasoning: LLM's explanation for the choice
        raw_response: Raw response from the LLM API
    """
    winner: str | None
    reasoning: str
    raw_response: dict


@dataclass
class RoundResult:
    """Result of a single comparison round.

    Attributes:
        order: "AB" or "BA" indicating presentation order
        winner: "A" or "B"
        reasoning: LLM's explanation
        cached: Whether this result was from cache
    """
    order: str
    winner: str
    reasoning: str
    cached: bool


@dataclass
class MatchResult:
    """Result of a complete match between two items.

    Attributes:
        item_a: First item text
        item_b: Second item text
        winner: "A", "B", or None (draw)
        rounds: List of individual round results
    """
    item_a: str
    item_b: str
    winner: str | None
    rounds: list[RoundResult]


@dataclass
class Statistics:
    """Statistics for the sorting operation.

    Attributes:
        total_matches: Number of matches played
        total_api_calls: Number of API calls made
        cache_hits: Number of cache hits
        elapsed_time: Total time in seconds
    """
    total_matches: int
    total_api_calls: int
    cache_hits: int
    elapsed_time: float


@dataclass
class SortResult:
    """Final result of the sorting operation.

    Attributes:
        rankings: List of (rank, [items]) tuples
        match_history: List of all match results
        statistics: Sorting statistics
    """
    rankings: list[tuple[int, list[str]]]
    match_history: list[MatchResult]
    statistics: Statistics
