"""Output modes for LLM Qualitative Sort.

This module provides various output formats for sort results:
- Sorting: Simple sorted list of items
- Ranking: Detailed ranking with wins and tie status
- Percentile: Percentile scores with tier classification
"""

from llm_qualitative_sort.output.models import (
    SortingOutput,
    RankingEntry,
    RankingOutput,
    PercentileEntry,
    PercentileOutput,
)
from llm_qualitative_sort.output.calculators import DEFAULT_TIER_THRESHOLDS
from llm_qualitative_sort.output.formatters import (
    to_sorting,
    to_ranking,
    to_percentile,
)


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
