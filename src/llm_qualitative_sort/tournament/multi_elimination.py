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

        brackets = self._group_by_losses(active)
        return self._create_matches_from_brackets(brackets)

    def _group_by_losses(
        self, participants: list[Participant]
    ) -> dict[int, list[Participant]]:
        """Group participants by their loss count.

        Args:
            participants: List of active participants

        Returns:
            Dictionary mapping loss count to list of participants
        """
        brackets: dict[int, list[Participant]] = {}
        for p in participants:
            if p.losses not in brackets:
                brackets[p.losses] = []
            brackets[p.losses].append(p)
        return brackets

    def _create_matches_from_brackets(
        self, brackets: dict[int, list[Participant]]
    ) -> list[tuple[str, str]]:
        """Create match pairings from loss brackets.

        Pairs participants within the same bracket first.
        If a bracket has an odd number, the remaining participant
        may be matched with someone from the next bracket.

        Args:
            brackets: Dictionary mapping loss count to participants

        Returns:
            List of (item_a, item_b) match tuples
        """
        matches: list[tuple[str, str]] = []

        for loss_count in sorted(brackets.keys()):
            bracket = brackets[loss_count]
            self._rng.shuffle(bracket)

            # Pair up participants within bracket
            paired_matches = self._pair_within_bracket(bracket)
            matches.extend(paired_matches)

            # Handle odd participant by matching with next bracket
            if len(bracket) % 2 == 1:
                cross_match = self._match_odd_participant(
                    bracket[-1], loss_count, brackets
                )
                if cross_match:
                    matches.append(cross_match)

        return matches

    def _pair_within_bracket(
        self, bracket: list[Participant]
    ) -> list[tuple[str, str]]:
        """Pair up participants within a single bracket.

        Args:
            bracket: List of participants (already shuffled)

        Returns:
            List of (item_a, item_b) match tuples
        """
        matches: list[tuple[str, str]] = []
        for i in range(0, len(bracket) - 1, 2):
            p1, p2 = bracket[i], bracket[i + 1]
            matches.append((p1.item, p2.item))
        return matches

    def _match_odd_participant(
        self,
        remaining: Participant,
        current_loss_count: int,
        brackets: dict[int, list[Participant]]
    ) -> tuple[str, str] | None:
        """Try to match an odd participant with someone from the next bracket.

        Args:
            remaining: The participant without a pair
            current_loss_count: The loss count of the current bracket
            brackets: All loss brackets

        Returns:
            Match tuple if an opponent was found, None otherwise
        """
        next_loss_count = current_loss_count + 1
        if next_loss_count not in brackets:
            return None

        next_bracket = brackets[next_loss_count]
        if not next_bracket:
            return None

        opponent = next_bracket.pop()
        return (remaining.item, opponent.item)

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
