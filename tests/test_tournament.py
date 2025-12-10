"""Tests for Swiss-system tournament."""

import pytest
from llm_qualitative_sort.tournament.swiss_system import (
    SwissSystemTournament,
    Participant,
)


class TestParticipant:
    """Tests for Participant class."""

    def test_create_participant(self):
        p = Participant(item="test", wins=0, losses=0)
        assert p.item == "test"
        assert p.wins == 0
        assert p.losses == 0

    def test_participant_is_eliminated(self):
        p = Participant(item="test", wins=0, losses=3)
        assert p.is_eliminated(elimination_count=3) is True

    def test_participant_not_eliminated(self):
        p = Participant(item="test", wins=0, losses=2)
        assert p.is_eliminated(elimination_count=3) is False


class TestSwissSystemTournament:
    """Tests for SwissSystemTournament."""

    def test_create_tournament(self):
        tournament = SwissSystemTournament(
            items=["a", "b", "c"],
            elimination_count=2
        )
        assert tournament is not None

    def test_create_tournament_with_items(self):
        items = ["item1", "item2", "item3", "item4"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=2
        )
        assert len(tournament.participants) == 4

    def test_get_active_participants(self):
        items = ["a", "b", "c"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=2
        )
        active = tournament.get_active_participants()
        assert len(active) == 3

    def test_record_match_winner(self):
        items = ["a", "b"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=2
        )
        # Simulate a match where "a" wins
        tournament.record_match_result("a", "b", "a")

        p_a = tournament.get_participant("a")
        p_b = tournament.get_participant("b")

        assert p_a.wins == 1
        assert p_a.losses == 0
        assert p_b.wins == 0
        assert p_b.losses == 1

    def test_record_match_draw(self):
        items = ["a", "b"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=2
        )
        # Simulate a draw
        tournament.record_match_result("a", "b", None)

        p_a = tournament.get_participant("a")
        p_b = tournament.get_participant("b")

        # Both get a loss on draw
        assert p_a.losses == 1
        assert p_b.losses == 1

    def test_elimination(self):
        items = ["a", "b"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=2
        )
        # Two losses eliminates
        tournament.record_match_result("a", "b", "a")
        tournament.record_match_result("a", "b", "a")

        assert tournament.get_participant("b").is_eliminated(2) is True
        assert tournament.get_participant("a").is_eliminated(2) is False

    def test_get_next_matches(self):
        items = ["a", "b", "c", "d"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=2,
            seed=42
        )
        matches = tournament.get_next_matches()
        assert len(matches) > 0
        # Each match should be a tuple of two items
        for match in matches:
            assert len(match) == 2

    def test_is_complete(self):
        items = ["a", "b"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=1  # Single elimination
        )
        assert tournament.is_complete() is False

        # One win eliminates the loser
        tournament.record_match_result("a", "b", "a")
        assert tournament.is_complete() is True

    def test_get_rankings(self):
        items = ["a", "b", "c"]
        tournament = SwissSystemTournament(
            items=items,
            elimination_count=1,
            seed=42
        )
        # Run until complete
        while not tournament.is_complete():
            matches = tournament.get_next_matches()
            for item_a, item_b in matches:
                # Always "a" wins if present, else first item
                winner = "a" if "a" in (item_a, item_b) else item_a
                tournament.record_match_result(item_a, item_b, winner)

        rankings = tournament.get_rankings()
        # Rankings should be list of (rank, [items])
        assert len(rankings) > 0
        # Winner should be ranked first
        first_rank, first_items = rankings[0]
        assert first_rank == 1

    def test_seed_reproducibility(self):
        items = ["a", "b", "c", "d"]
        t1 = SwissSystemTournament(items=items, elimination_count=2, seed=42)
        t2 = SwissSystemTournament(items=items, elimination_count=2, seed=42)

        matches1 = t1.get_next_matches()
        matches2 = t2.get_next_matches()

        assert matches1 == matches2
