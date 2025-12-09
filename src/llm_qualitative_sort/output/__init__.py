"""Output modes for LLM Qualitative Sort.

This module provides various output formats for sort results:
- Sorting: Simple sorted list of items
- Ranking: Detailed ranking with wins and tie status
- Percentile: Percentile scores with tier classification
"""

from llm_qualitative_sort.output.models import (
    DEFAULT_TIER_THRESHOLDS,
    PercentileEntry,
    PercentileOutput,
    RankingEntry,
    RankingOutput,
    SortingOutput,
)
from llm_qualitative_sort.output.percentile import to_percentile
from llm_qualitative_sort.output.ranking import to_ranking
from llm_qualitative_sort.output.sorting import to_sorting

__all__ = [
    # Functions
    "to_sorting",
    "to_ranking",
    "to_percentile",
    # Models
    "SortingOutput",
    "RankingOutput",
    "RankingEntry",
    "PercentileOutput",
    "PercentileEntry",
    # Constants
    "DEFAULT_TIER_THRESHOLDS",
]
