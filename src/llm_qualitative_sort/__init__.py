"""LLM Qualitative Sort - LLM-based qualitative sorting using multi-elimination tournament."""

from llm_qualitative_sort.models import (
    ComparisonResult,
    RoundResult,
    MatchResult,
    SortResult,
    Statistics,
)
from llm_qualitative_sort.events import EventType, ProgressEvent
from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.openai import OpenAIProvider
from llm_qualitative_sort.providers.google import GoogleProvider
from llm_qualitative_sort.providers.mock import MockLLMProvider
from llm_qualitative_sort.cache.base import Cache
from llm_qualitative_sort.cache.memory import MemoryCache
from llm_qualitative_sort.cache.file import FileCache
from llm_qualitative_sort.sorter import QualitativeSorter
from llm_qualitative_sort.metrics import (
    AccuracyMetrics,
    flatten_rankings,
    calculate_kendall_tau,
    calculate_top_k_accuracy,
    calculate_correct_pair_ratio,
    calculate_all_metrics,
)
from llm_qualitative_sort.output import (
    to_sorting,
    to_ranking,
    to_percentile,
    SortingOutput,
    RankingOutput,
    RankingEntry,
    PercentileOutput,
    PercentileEntry,
    DEFAULT_TIER_THRESHOLDS,
)

__all__ = [
    # Models
    "ComparisonResult",
    "RoundResult",
    "MatchResult",
    "SortResult",
    "Statistics",
    # Events
    "EventType",
    "ProgressEvent",
    # Providers
    "LLMProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "MockLLMProvider",
    # Cache
    "Cache",
    "MemoryCache",
    "FileCache",
    # Sorter
    "QualitativeSorter",
    # Metrics
    "AccuracyMetrics",
    "flatten_rankings",
    "calculate_kendall_tau",
    "calculate_top_k_accuracy",
    "calculate_correct_pair_ratio",
    "calculate_all_metrics",
    # Output
    "to_sorting",
    "to_ranking",
    "to_percentile",
    "SortingOutput",
    "RankingOutput",
    "RankingEntry",
    "PercentileOutput",
    "PercentileEntry",
    "DEFAULT_TIER_THRESHOLDS",
]
