"""Data models for output formatting."""

from dataclasses import dataclass


@dataclass
class SortingOutput:
    """Sorted items in rank order.

    Attributes:
        items: List of items sorted by rank (1st place first).
               Tied items maintain their original input order.
    """
    items: list[str]


@dataclass
class RankingEntry:
    """Single entry in the ranking output.

    Attributes:
        rank: Rank number (1-based, ties share the same rank)
        item: The item
        wins: Number of wins in the tournament
        is_tied: Whether this item is tied with others at the same rank
    """
    rank: int
    item: str
    wins: int
    is_tied: bool


@dataclass
class RankingOutput:
    """Complete ranking output.

    Attributes:
        entries: List of ranking entries ordered by rank
        total_items: Total number of items
    """
    entries: list[RankingEntry]
    total_items: int


@dataclass
class PercentileEntry:
    """Single entry in the percentile output.

    Attributes:
        item: The item
        percentile: Percentile score (0.0-100.0, higher is better)
        rank: Rank number
        tier: Tier classification (S/A/B/C/D)
    """
    item: str
    percentile: float
    rank: int
    tier: str


@dataclass
class PercentileOutput:
    """Complete percentile output.

    Attributes:
        entries: List of percentile entries ordered by percentile (descending)
        total_items: Total number of items
    """
    entries: list[PercentileEntry]
    total_items: int
