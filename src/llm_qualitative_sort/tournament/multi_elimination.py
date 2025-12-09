"""Multi-elimination tournament implementation."""

import random
from dataclasses import dataclass


@dataclass
class Participant:
    """Tournament participant.

    Attributes:
        item: The item being compared
        wins: Number of wins
        losses: Number of losses
    """
    item: str
    wins: int = 0
    losses: int = 0

    def is_eliminated(self, elimination_count: int) -> bool:
        """Check if participant is eliminated."""
        return self.losses >= elimination_count


class MultiEliminationTournament:
    """Multi-elimination tournament manager.

    Implements a simplified multi-elimination tournament where
    participants are eliminated after N losses. Rankings are
    determined by win count.

    Attributes:
        elimination_count: Number of losses before elimination
        participants: Dictionary of participants by item
    """

    def __init__(
        self,
        items: list[str],
        elimination_count: int = 2,
        seed: int | None = None
    ):
        self.elimination_count = elimination_count
        self._rng = random.Random(seed)

        # Create participants
        self.participants: dict[str, Participant] = {
            item: Participant(item=item)
            for item in items
        }

        # Shuffle initial order
        self._items = list(items)
        self._rng.shuffle(self._items)

        # Track match history to avoid repeated matches
        self._match_history: set[tuple[str, str]] = set()

    def get_participant(self, item: str) -> Participant:
        """Get participant by item."""
        return self.participants[item]

    def get_active_participants(self) -> list[Participant]:
        """Get all non-eliminated participants."""
        return [
            p for p in self.participants.values()
            if not p.is_eliminated(self.elimination_count)
        ]

    def record_match_result(
        self,
        item_a: str,
        item_b: str,
        winner: str | None
    ) -> None:
        """Record the result of a match.

        Args:
            item_a: First item
            item_b: Second item
            winner: Winning item, or None for draw
        """
        p_a = self.participants[item_a]
        p_b = self.participants[item_b]

        if winner is None:
            # Draw: both get a loss
            p_a.losses += 1
            p_b.losses += 1
        elif winner == item_a:
            p_a.wins += 1
            p_b.losses += 1
        elif winner == item_b:
            p_b.wins += 1
            p_a.losses += 1

        # Track match
        match_key = tuple(sorted([item_a, item_b]))
        self._match_history.add(match_key)

    def get_next_matches(self) -> list[tuple[str, str]]:
        """Get the next set of matches to play.

        Returns pairs of items for the next round of matches.
        Pairs are formed within loss brackets (same loss count).
        """
        active = self.get_active_participants()

        if len(active) < 2:
            return []

        # Group by loss count (brackets)
        brackets: dict[int, list[Participant]] = {}
        for p in active:
            if p.losses not in brackets:
                brackets[p.losses] = []
            brackets[p.losses].append(p)

        matches = []

        # Process each bracket
        for loss_count in sorted(brackets.keys()):
            bracket = brackets[loss_count]
            self._rng.shuffle(bracket)

            # Pair up participants
            for i in range(0, len(bracket) - 1, 2):
                p1, p2 = bracket[i], bracket[i + 1]
                matches.append((p1.item, p2.item))

            # If odd number, the remaining participant waits
            # or can be matched with someone from another bracket
            if len(bracket) % 2 == 1 and loss_count + 1 in brackets:
                remaining = bracket[-1]
                next_bracket = brackets[loss_count + 1]
                if next_bracket:
                    opponent = next_bracket.pop()
                    matches.append((remaining.item, opponent.item))

        return matches

    def is_complete(self) -> bool:
        """Check if tournament is complete.

        Tournament is complete when only one participant remains
        or no more matches can be played.
        """
        active = self.get_active_participants()
        return len(active) <= 1

    def get_rankings(self) -> list[tuple[int, list[str]]]:
        """Get final rankings based on win count.

        Returns list of (rank, [items]) tuples.
        Items with same win count share the same rank.
        """
        # Group by wins
        by_wins: dict[int, list[str]] = {}
        for p in self.participants.values():
            if p.wins not in by_wins:
                by_wins[p.wins] = []
            by_wins[p.wins].append(p.item)

        # Sort by wins descending
        sorted_wins = sorted(by_wins.keys(), reverse=True)

        rankings = []
        current_rank = 1

        for wins in sorted_wins:
            items = by_wins[wins]
            rankings.append((current_rank, items))
            current_rank += len(items)

        return rankings
