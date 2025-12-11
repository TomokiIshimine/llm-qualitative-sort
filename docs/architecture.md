# LLM Qualitative Sort - Architecture Document

[日本語版](architecture.ja.md)

## Overview

**llm-qualitative-sort** is a Python package that sorts text data based on qualitative criteria using LLMs (Large Language Models).

Using a Swiss-system tournament format, it ranks multiple items based on evaluation criteria that cannot be quantitatively compared, such as "writing quality" or "character strength."

## System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        User[User]
    end

    subgraph "Core Layer"
        Sorter[QualitativeSorter<br/>Main Orchestrator]
    end

    subgraph "Tournament Layer"
        Tournament[SwissSystemTournament<br/>Tournament Management]
        Participant[Participant<br/>Participant Management]
    end

    subgraph "Provider Layer"
        Provider[LLMProvider<br/>Abstract Base Class]
        LangChain[LangChainProvider<br/>LangChain Integration]
        Mock[MockLLMProvider<br/>For Testing]
    end

    subgraph "Cache Layer"
        Cache[Cache<br/>Abstract Base Class]
        Memory[MemoryCache<br/>Memory Cache]
        File[FileCache<br/>File Cache]
    end

    subgraph "Output Layer"
        Formatters[Formatters<br/>Output Formatters]
        Sorting[SortingOutput]
        Ranking[RankingOutput]
        Percentile[PercentileOutput]
    end

    User --> Sorter
    Sorter --> Tournament
    Tournament --> Participant
    Sorter --> Provider
    Provider --> LangChain
    Provider --> Mock
    Sorter --> Cache
    Cache --> Memory
    Cache --> File
    Sorter --> Formatters
    Formatters --> Sorting
    Formatters --> Ranking
    Formatters --> Percentile
```

## Component Structure

```mermaid
classDiagram
    class QualitativeSorter {
        -LLMProvider provider
        -str criteria
        -int elimination_count
        -int comparison_rounds
        -int max_concurrent_requests
        -Cache cache
        -Callable on_progress
        -int seed
        +sort(items) SortResult
        -_run_match(item_a, item_b) MatchResult
        -_compare_with_cache(first, second, order) tuple
    }

    class SwissSystemTournament {
        -dict participants
        -int elimination_count
        -set _match_history
        -Random _rng
        +get_next_matches() list
        +record_match_result(a, b, winner)
        +get_rankings() list
        +is_complete() bool
    }

    class Participant {
        +str item
        +int wins
        +int losses
        +is_eliminated(count) bool
    }

    class LLMProvider {
        <<abstract>>
        +compare(item_a, item_b, criteria)* ComparisonResult
    }

    class LangChainProvider {
        -BaseChatModel model
        +compare(item_a, item_b, criteria) ComparisonResult
    }

    class Cache {
        <<abstract>>
        +get(a, b, criteria, order)* ComparisonResult
        +set(a, b, criteria, order, result)*
        -_make_key(a, b, criteria, order) str
    }

    QualitativeSorter --> LLMProvider
    QualitativeSorter --> Cache
    QualitativeSorter --> SwissSystemTournament
    SwissSystemTournament --> Participant
    LangChainProvider --|> LLMProvider
```

## Data Flow

```mermaid
flowchart TD
    Start([Start]) --> Input[Input item list]
    Input --> Validate{Validation}
    Validate -->|Failure| Error[Return error]
    Validate -->|Success| Init[Initialize tournament]

    Init --> CheckComplete{Tournament<br/>complete?}
    CheckComplete -->|Yes| Compile[Compile results]
    CheckComplete -->|No| GetMatches[Get next matches]

    GetMatches --> RunMatches[Execute matches in parallel]
    RunMatches --> RecordResults[Record results]
    RecordResults --> EmitProgress[Emit progress event]
    EmitProgress --> CheckComplete

    Compile --> CreateResult[Create SortResult]
    CreateResult --> FormatOutput{Output format}

    FormatOutput -->|Sorting| SortOut[SortingOutput]
    FormatOutput -->|Ranking| RankOut[RankingOutput]
    FormatOutput -->|Percentile| PercOut[PercentileOutput]

    SortOut --> End([End])
    RankOut --> End
    PercOut --> End
    Error --> End
```

## Key Components

### 1. QualitativeSorter

Main orchestrator class. Integrates all components and controls the entire sorting process.

**Responsibilities:**
- Item validation
- Tournament execution control
- Concurrent request limiting (Semaphore)
- Progress event emission
- Result aggregation

### 2. SwissSystemTournament

Implements Swiss-system tournament logic.

**Responsibilities:**
- Participant management (win/loss tracking)
- Bracket (loss count group) matching
- Match history tracking
- Final ranking calculation

### 3. LLMProvider

Interface abstracting LLM communication.

**Implementations:**
- `LangChainProvider`: Generic provider using LangChain
- `MockLLMProvider`: Mock provider for testing

### 4. Cache

Caches comparison results to prevent redundant LLM calls.

**Implementations:**
- `MemoryCache`: In-memory cache (session-limited)
- `FileCache`: File-based persistent cache

## Design Principles

### Dependency Injection

```python
# Provider and cache are injected externally
sorter = QualitativeSorter(
    provider=LangChainProvider(model),  # Injected
    criteria="Text quality",
    cache=FileCache("./cache"),          # Injected
)
```

### Async Processing

All LLM calls use `async/await`, with `asyncio.Semaphore` controlling concurrent request count.

```python
async with self._semaphore:
    result = await self._provider.compare(first, second, self._criteria)
```

### Event-Driven Progress Reporting

```python
def on_progress(event: ProgressEvent):
    print(f"{event.completed}/{event.total}: {event.message}")

sorter = QualitativeSorter(..., on_progress=on_progress)
```

## File Structure

```
src/llm_qualitative_sort/
├── __init__.py              # Public API
├── models.py                # Data structures
├── events.py                # Event system
├── sorter.py                # Main class
├── metrics.py               # Evaluation metrics
├── providers/               # LLM providers
│   ├── base.py             # Abstract base class
│   ├── langchain.py        # LangChain integration
│   ├── mock.py             # For testing
│   └── errors.py           # Error handling
├── tournament/              # Tournament processing
│   └── swiss_system.py
├── cache/                   # Cache functionality
│   └── __init__.py
└── output/                  # Output formatting
    ├── models.py
    ├── formatters.py
    └── calculators.py
```
