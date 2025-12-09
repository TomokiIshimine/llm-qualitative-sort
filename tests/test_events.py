"""Tests for event types and progress events."""

import pytest
from llm_qualitative_sort.events import EventType, ProgressEvent


class TestEventType:
    """Tests for EventType enum."""

    def test_match_start_exists(self):
        assert EventType.MATCH_START is not None

    def test_match_end_exists(self):
        assert EventType.MATCH_END is not None

    def test_round_end_exists(self):
        assert EventType.ROUND_END is not None

    def test_bracket_change_exists(self):
        assert EventType.BRACKET_CHANGE is not None

    def test_event_types_are_distinct(self):
        types = [
            EventType.MATCH_START,
            EventType.MATCH_END,
            EventType.ROUND_END,
            EventType.BRACKET_CHANGE,
        ]
        assert len(types) == len(set(types))


class TestProgressEvent:
    """Tests for ProgressEvent dataclass."""

    def test_create_progress_event(self):
        event = ProgressEvent(
            type=EventType.MATCH_START,
            message="Match 1 starting",
            completed=0,
            total=10,
            data=None
        )
        assert event.type == EventType.MATCH_START
        assert event.message == "Match 1 starting"
        assert event.completed == 0
        assert event.total == 10
        assert event.data is None

    def test_create_progress_event_with_data(self):
        event = ProgressEvent(
            type=EventType.MATCH_END,
            message="Match complete",
            completed=5,
            total=10,
            data={"winner": "A", "item_a": "text1", "item_b": "text2"}
        )
        assert event.type == EventType.MATCH_END
        assert event.data["winner"] == "A"

    def test_create_bracket_change_event(self):
        event = ProgressEvent(
            type=EventType.BRACKET_CHANGE,
            message="Item moved to losers bracket",
            completed=3,
            total=10,
            data={"item": "text1", "new_bracket": 1}
        )
        assert event.type == EventType.BRACKET_CHANGE
        assert event.data["new_bracket"] == 1
