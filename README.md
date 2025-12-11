# llm-qualitative-sort

A Python package for qualitative sorting using LLMs

[日本語版 README](README.ja.md)

## Overview

**llm-qualitative-sort** is a Python package that ranks multiple text items based on qualitative criteria (such as writing quality, character strength, etc.) that cannot be quantitatively compared, using a Swiss-system tournament approach.

LLMs perform pairwise comparisons, and winners are determined through a tournament format, enabling consistent ranking even with subjective evaluation criteria.

## Features

- **Swiss-System Tournament**: Fair tournament format with elimination after N losses
- **Multiple LLM Providers**: Supports OpenAI, Google Gemini, Anthropic Claude
- **Async Processing**: Efficient parallel comparisons using asyncio
- **Position Bias Mitigation**: Multiple comparisons with swapped order to reduce bias
- **Caching**: Memory and file-based caching to reduce redundant API calls
- **Progress Callbacks**: Real-time progress tracking
- **Extensibility**: Custom providers and caches via abstract base classes

## Installation

```bash
pip install llm-qualitative-sort
```

Install with development dependencies:

```bash
pip install llm-qualitative-sort[dev]
```

## Usage

### Basic Example (OpenAI)

```python
import asyncio
from langchain_openai import ChatOpenAI
from llm_qualitative_sort import QualitativeSorter, LangChainProvider

async def main():
    # Configure LangChain model
    llm = ChatOpenAI(model="gpt-5-nano", api_key="your-api-key")
    provider = LangChainProvider(llm=llm)

    # Create sorter
    sorter = QualitativeSorter(
        provider=provider,
        criteria="Readability and persuasiveness of the text",
        elimination_count=2,  # Eliminated after 2 losses
        comparison_rounds=2,  # 2 comparisons per match (position bias mitigation)
    )

    # Items to sort
    items = [
        "Short sentences are easy to read.",
        "Long sentences with detailed explanations are informative and persuasive.",
        "Sentences of moderate length that cover key points are best.",
    ]

    # Execute sorting
    result = await sorter.sort(items)

    # Display results
    print("Rankings:")
    for rank, tied_items in result.rankings:
        for item in tied_items:
            print(f"  Rank {rank}: {item[:30]}...")

    print(f"\nStatistics:")
    print(f"  Total matches: {result.statistics.total_matches}")
    print(f"  API calls: {result.statistics.total_api_calls}")
    print(f"  Elapsed time: {result.statistics.elapsed_time:.2f}s")

asyncio.run(main())
```

### Using Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from llm_qualitative_sort import QualitativeSorter, LangChainProvider

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key="your-google-api-key")
provider = LangChainProvider(llm=llm)

sorter = QualitativeSorter(
    provider=provider,
    criteria="Your evaluation criteria",
)
```

### Using Anthropic Claude

```python
from langchain_anthropic import ChatAnthropic
from llm_qualitative_sort import QualitativeSorter, LangChainProvider

llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key="your-anthropic-api-key")
provider = LangChainProvider(llm=llm)

sorter = QualitativeSorter(
    provider=provider,
    criteria="Your evaluation criteria",
)
```

### Using Cache

```python
from llm_qualitative_sort import QualitativeSorter, LangChainProvider, MemoryCache, FileCache

# Memory cache
memory_cache = MemoryCache()

# File cache (persistent)
file_cache = FileCache(cache_dir="./cache")

sorter = QualitativeSorter(
    provider=provider,
    criteria="Your evaluation criteria",
    cache=memory_cache,  # or file_cache
)
```

### Progress Callbacks

```python
from llm_qualitative_sort import QualitativeSorter, LangChainProvider, ProgressEvent

def on_progress(event: ProgressEvent):
    print(f"[{event.type.name}] {event.message} ({event.completed}/{event.total})")

sorter = QualitativeSorter(
    provider=provider,
    criteria="Your evaluation criteria",
    on_progress=on_progress,
)
```

## API Reference

### QualitativeSorter

Main sorting class.

```python
QualitativeSorter(
    provider: LLMProvider,           # LLM provider (required)
    criteria: str,                   # Evaluation criteria (required)
    elimination_count: int = 2,      # Losses before elimination
    comparison_rounds: int = 2,      # Comparisons per match (even number)
    max_concurrent_requests: int = 10,  # Max concurrent requests
    cache: Cache | None = None,      # Cache
    on_progress: Callable | None = None,  # Progress callback
    seed: int | None = None,         # Random seed (for reproducibility)
)
```

**Methods:**

- `async sort(items: list[str]) -> SortResult`: Sort items

### SortResult

Data class for sort results.

```python
@dataclass
class SortResult:
    rankings: list[tuple[int, list[str]]]  # List of (rank, [items])
    match_history: list[MatchResult]       # History of all matches
    statistics: Statistics                  # Statistics
```

### LLM Providers

| Class | Description |
|-------|-------------|
| `LangChainProvider` | Generic provider using LangChain BaseChatModel |
| `MockLLMProvider` | Mock provider for testing |

`LangChainProvider` supports the following LangChain models:
- `langchain_openai.ChatOpenAI` (OpenAI)
- `langchain_google_genai.ChatGoogleGenerativeAI` (Google Gemini)
- `langchain_anthropic.ChatAnthropic` (Anthropic Claude)
- Other LangChain models that support `with_structured_output()`

### Cache

| Cache | Class | Description |
|-------|-------|-------------|
| Memory | `MemoryCache` | In-memory cache |
| File | `FileCache` | File-based persistent cache |

### Output Formatters

Convert sort results to various formats.

```python
from llm_qualitative_sort import to_sorting, to_ranking, to_percentile

# Simple sorted list
sorting_output = to_sorting(result)
print(sorting_output.items)  # ["1st place item", "2nd place item", ...]

# Detailed ranking (with win count, tie information)
ranking_output = to_ranking(result)
for entry in ranking_output.entries:
    print(f"Rank {entry.rank}: {entry.item} (wins: {entry.wins})")

# Percentile (with tier classification)
percentile_output = to_percentile(result)
for entry in percentile_output.entries:
    print(f"{entry.item}: {entry.percentile:.0f}% ({entry.tier})")
```

### Accuracy Metrics

Evaluate sorting accuracy against expected values.

```python
from llm_qualitative_sort import (
    flatten_rankings,
    calculate_kendall_tau,
    calculate_all_metrics,
)

# Convert rankings to flat list
actual = flatten_rankings(result.rankings)
expected = ["expected 1st", "expected 2nd", "expected 3rd"]

# Kendall's tau correlation coefficient (-1 to 1, 1 is perfect match)
tau = calculate_kendall_tau(actual, expected)

# Calculate all metrics at once
metrics = calculate_all_metrics(actual, expected)
print(f"Kendall's tau: {metrics.kendall_tau:.3f}")
print(f"Top-10 accuracy: {metrics.top_10_accuracy:.1%}")
print(f"Pairwise accuracy: {metrics.correct_pair_ratio:.1%}")
```

## Project Structure

```
src/llm_qualitative_sort/
├── __init__.py           # Public API
├── models.py             # Data structures (dataclass)
├── events.py             # Event definitions
├── sorter.py             # Main class
├── metrics.py            # Accuracy metrics
├── utils.py              # Utility functions
├── providers/            # LLM providers
│   ├── __init__.py
│   ├── base.py           # Abstract base class (LLMProvider)
│   ├── langchain.py      # LangChain integration provider
│   ├── mock.py           # For testing
│   └── errors.py         # Error handling
├── tournament/           # Tournament processing
│   ├── __init__.py
│   └── swiss_system.py
├── output/               # Output formatters
│   ├── __init__.py
│   ├── models.py         # Output data structures
│   ├── calculators.py    # Calculation logic
│   └── formatters.py     # Format conversion
└── cache/                # Caching
    └── __init__.py       # Cache, MemoryCache, FileCache
```

## How It Works

### Swiss-System Tournament

1. All participants start with 0 losses
2. Participants with the same number of losses (bracket) are randomly paired
3. LLM performs pairwise comparison based on specified criteria
4. Loser's loss count is incremented
5. Eliminated after N losses (default: 2)
6. Repeat until one participant remains
7. Rankings determined by win count

### Position Bias Mitigation

LLMs have position biases such as preferring items presented first. To mitigate this, each match performs multiple comparisons with swapped presentation order, and the winner is determined by majority vote.

## Development Setup

### Environment Setup

```bash
# Clone repository
git clone https://github.com/TomokiIshimine/llm-qualitative-sort.git
cd llm-qualitative-sort

# Install in development mode (includes dev dependencies)
pip install -e ".[dev]"

# Verify with tests
python -m pytest tests/ -v
```

### Development Dependencies

- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `scipy>=1.10.0` - Statistical processing

### Test Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_sorter.py -v

# Specific test class
python -m pytest tests/test_sorter.py::TestQualitativeSorterSort -v

# With coverage
python -m pytest tests/ --cov=src/llm_qualitative_sort
```

### Development Philosophy

This project follows Test-Driven Development (TDD):

1. **Red**: Write a failing test first
2. **Green**: Implement minimal code to pass the test
3. **Refactor**: Improve code (keeping tests passing)

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture and design principles |
| [Swiss-System Tournament](docs/tournament.md) | Tournament algorithm and matching strategy |
| [API Reference](docs/api-reference.md) | Detailed API documentation with examples |

Japanese versions are also available (`*.ja.md`).

## Deployment

### Publishing to PyPI

This package uses GitHub Actions for automated PyPI publishing with trusted publishing (no API tokens required).

**Release Process:**

1. Update version in `pyproject.toml`
2. Create and push a version tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. GitHub Actions will automatically:
   - Run tests on Python 3.10, 3.11, 3.12
   - Build the package
   - Publish to PyPI

**Requirements:**
- Configure PyPI trusted publishing in your PyPI project settings
- Set up the `pypi` environment in your GitHub repository

## Requirements

- Python >= 3.10
- aiohttp >= 3.8.0

## License

MIT License
