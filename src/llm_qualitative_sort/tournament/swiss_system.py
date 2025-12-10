"""Swiss-system tournament implementation."""

import random
from dataclasses import dataclass

from llm_qualitative_sort.utils import group_by


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


class SwissSystemTournament:
    """Swiss-system tournament manager.

    Implements a Swiss-system tournament where participants are
    eliminated after N losses. Rankings are determined by win count.

    Attributes:
        elimination_count: Number of losses before elimination
        participants: Dictionary of participants by item
    """

    def __init__(
        self,
        items: list[str],
        elimination_count: int = 2,
        seed: int | None = None,
    ) -> None:
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
        return group_by(participants, lambda p: p.losses)

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
        used_participants: set[str] = set()

        for loss_count in sorted(brackets.keys()):
            bracket = [p for p in brackets[loss_count] if p.item not in used_participants]
            self._rng.shuffle(bracket)

            # Pair up participants within bracket
            paired_matches = self._pair_within_bracket(bracket)
            matches.extend(paired_matches)
            for p1_item, p2_item in paired_matches:
                used_participants.add(p1_item)
                used_participants.add(p2_item)

            # Handle odd participant by matching with next bracket
            if len(bracket) % 2 == 1:
                cross_match = self._match_odd_participant(
                    bracket[-1], loss_count, brackets, used_participants
                )
                if cross_match:
                    matches.append(cross_match)
                    used_participants.add(cross_match[0])
                    used_participants.add(cross_match[1])

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
        brackets: dict[int, list[Participant]],
        used_participants: set[str]
    ) -> tuple[str, str] | None:
        """Try to match an odd participant with someone from the next bracket.

        Args:
            remaining: The participant without a pair
            current_loss_count: The loss count of the current bracket
            brackets: All loss brackets
            used_participants: Set of participant items already matched

        Returns:
            Match tuple if an opponent was found, None otherwise
        """
        next_loss_count = current_loss_count + 1
        if next_loss_count not in brackets:
            return None

        # Find an available opponent from the next bracket
        available = [
            p for p in brackets[next_loss_count]
            if p.item not in used_participants
        ]
        if not available:
            return None

        opponent = available[-1]
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
        by_wins = group_by(
            list(self.participants.values()),
            lambda p: p.wins
        )

        # Sort by wins descending and build rankings
        sorted_wins = sorted(by_wins.keys(), reverse=True)
        rankings: list[tuple[int, list[str]]] = []
        current_rank = 1

        for wins in sorted_wins:
            items = [p.item for p in by_wins[wins]]
            rankings.append((current_rank, items))
            current_rank += len(items)

        return rankings
