"""Event types and progress events for LLM Qualitative Sort."""

from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """Types of progress events during sorting."""
    MATCH_START = auto()
    MATCH_END = auto()
    ROUND_END = auto()
    BRACKET_CHANGE = auto()


@dataclass
class ProgressEvent:
    """Progress event during sorting operation.

    Attributes:
        type: Type of the event
        message: Human-readable message
        completed: Number of completed items
        total: Total number of items
        data: Additional event-specific data
    """
    type: EventType
    message: str
    completed: int
    total: int
    data: dict | None
