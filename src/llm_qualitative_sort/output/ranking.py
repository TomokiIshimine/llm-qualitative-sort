"""Ranking output mode implementation."""

from llm_qualitative_sort.models import SortResult
from llm_qualitative_sort.output.models import RankingEntry, RankingOutput


def to_ranking(result: SortResult) -> RankingOutput:
    """Convert sort result to ranking format with detailed entries.

    Args:
        result: The sort result from QualitativeSorter

    Returns:
        RankingOutput with entries containing rank, wins, and tie status.
    """
    if not result.rankings:
        return RankingOutput(entries=[], total_items=0)

    # Calculate wins from match history
    wins_by_item = _calculate_wins(result)

    entries: list[RankingEntry] = []

    for rank, items in result.rankings:
        is_tied = len(items) > 1

        for item in items:
            entries.append(
                RankingEntry(
                    rank=rank,
                    item=item,
                    wins=wins_by_item.get(item, 0),
                    is_tied=is_tied,
                )
            )

    # Sort entries by rank
    entries.sort(key=lambda e: e.rank)

    total_items = sum(len(items) for _rank, items in result.rankings)

    return RankingOutput(entries=entries, total_items=total_items)


def _calculate_wins(result: SortResult) -> dict[str, int]:
    """Calculate wins for each item from match history.

    Args:
        result: The sort result

    Returns:
        Dictionary mapping item to win count.
    """
    wins: dict[str, int] = {}

    for match in result.match_history:
        if match.winner == "A":
            wins[match.item_a] = wins.get(match.item_a, 0) + 1
        elif match.winner == "B":
            wins[match.item_b] = wins.get(match.item_b, 0) + 1
        # Draws don't add wins

    return wins
