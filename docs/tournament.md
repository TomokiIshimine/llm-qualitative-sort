# Swiss-System Tournament

[日本語版](tournament.ja.md)

## Overview

A Swiss-system tournament is a format where participants are eliminated after losing a specified number of times (N losses). Unlike single elimination (elimination after 1 loss), allowing multiple losses enables fairer ranking determination.

## How the Tournament Works

### Basic Rules

1. All participants start with 0 losses
2. Each match loss increments the loss count by 1
3. Participants reaching `elimination_count` losses are eliminated
4. Continue until 1 or fewer active participants remain
5. Final rankings determined by win count

```mermaid
flowchart TD
    Start([Tournament Start]) --> Init[All participants: 0 wins, 0 losses]
    Init --> Check{Active<br/>participants > 1?}

    Check -->|No| End([Tournament End])
    Check -->|Yes| Bracket[Group by loss count]

    Bracket --> Pair[Pair within same bracket]
    Pair --> Odd{Odd number?}

    Odd -->|Yes| Cross[Match with different bracket]
    Odd -->|No| Match[Execute matches]

    Cross --> Match
    Match --> Record[Record results]
    Record --> Update[Update win/loss counts]
    Update --> Eliminate{Reached N losses?}

    Eliminate -->|Yes| Remove[Eliminate]
    Eliminate -->|No| Check

    Remove --> Check
```

### Bracket System

Participants are classified into brackets (groups) based on loss count, with priority matching within the same bracket.

```mermaid
graph TD
    subgraph "Bracket 0 (0 losses)"
        A1[Participant A]
        A2[Participant B]
        A3[Participant C]
        A4[Participant D]
    end

    subgraph "Bracket 1 (1 loss)"
        B1[Participant E]
        B2[Participant F]
        B3[Participant G]
    end

    subgraph "Bracket 2 (2 losses = Eliminated)"
        C1[Participant H x]
        C2[Participant I x]
    end

    A1 -.->|match| A2
    A3 -.->|match| A4
    B1 -.->|match| B2
    B3 -.->|cross-bracket| A1
```

## Match Execution Flow

### Position Bias Mitigation

Since LLMs may exhibit bias based on presentation order, each match executes multiple rounds with alternating order.

```mermaid
sequenceDiagram
    participant S as Sorter
    participant P as Provider
    participant C as Cache

    Note over S: Match Start: A vs B

    rect rgb(240, 248, 255)
        Note over S: Round 1 (Order: AB)
        S->>C: Check cache (A, B, "AB")
        C-->>S: Cache miss
        S->>P: compare(A, B, criteria)
        P-->>S: winner: "A"
        S->>C: Save to cache
    end

    rect rgb(255, 248, 240)
        Note over S: Round 2 (Order: BA)
        S->>C: Check cache (B, A, "BA")
        C-->>S: Cache miss
        S->>P: compare(B, A, criteria)
        P-->>S: winner: "B" -> converted to "A"
        S->>C: Save to cache
    end

    Note over S: Tally: A=2 wins, B=0 wins
    Note over S: Winner: A
```

### Win/Loss Determination Logic

```mermaid
flowchart TD
    Start([Match Start]) --> Round1[Round 1: Compare in AB order]
    Round1 --> Result1{Result}

    Result1 -->|A wins| WinA1[A win count +1]
    Result1 -->|B wins| WinB1[B win count +1]
    Result1 -->|Error| Skip1[Skip]

    WinA1 --> Round2
    WinB1 --> Round2
    Skip1 --> Round2

    Round2[Round 2: Compare in BA order] --> Result2{Result}

    Result2 -->|A wins| WinA2[A win count +1]
    Result2 -->|B wins| WinB2[B win count +1]
    Result2 -->|Error| Skip2[Skip]

    WinA2 --> Judge
    WinB2 --> Judge
    Skip2 --> Judge

    Judge{Determine Winner} --> |A wins > B wins| WinnerA[Winner: A]
    Judge --> |B wins > A wins| WinnerB[Winner: B]
    Judge --> |Tied| Draw[Draw: None]

    WinnerA --> End([Match End])
    WinnerB --> End
    Draw --> End
```

## Tournament Progression Example

### 4 Items, elimination_count=2

```mermaid
graph TB
    subgraph "Round 1"
        M1[A vs B] --> R1[A wins]
        M2[C vs D] --> R2[C wins]
    end

    subgraph "State 1"
        S1A[A: 1W 0L]
        S1B[B: 0W 1L]
        S1C[C: 1W 0L]
        S1D[D: 0W 1L]
    end

    subgraph "Round 2"
        M3[A vs C<br/>0 losses each] --> R3[A wins]
        M4[B vs D<br/>1 loss each] --> R4[D wins]
    end

    subgraph "State 2"
        S2A[A: 2W 0L]
        S2B["B: 0W 2L x"]
        S2C[C: 1W 1L]
        S2D[D: 1W 1L]
    end

    subgraph "Round 3"
        M5[C vs D<br/>1 loss each] --> R5[C wins]
    end

    subgraph "State 3"
        S3A[A: 2W 0L]
        S3C[C: 2W 1L]
        S3D["D: 1W 2L x"]
    end

    subgraph "Round 4"
        M6[A vs C] --> R6[A wins]
    end

    subgraph "Final State"
        FA[A: 3W 0L]
        FC["C: 2W 2L x"]
    end

    R1 --> S1A
    R1 --> S1B
    R2 --> S1C
    R2 --> S1D

    S1A --> M3
    S1C --> M3
    S1B --> M4
    S1D --> M4

    R3 --> S2A
    R3 --> S2C
    R4 --> S2B
    R4 --> S2D

    S2C --> M5
    S2D --> M5

    R5 --> S3A
    R5 --> S3C
    R5 --> S3D

    S3A --> M6
    S3C --> M6

    R6 --> FA
    R6 --> FC
```

### Final Rankings (by Win Count)

| Rank | Item | Wins | Losses |
|------|------|------|--------|
| 1st  | A    | 3    | 0      |
| 2nd  | C    | 2    | 2      |
| 3rd  | D    | 1    | 2      |
| 4th  | B    | 0    | 2      |

## Cache Key Structure

Caching enables reuse of comparisons, but order information is included in the key to account for position bias.

```mermaid
flowchart LR
    subgraph "Cache Key Generation"
        A[item_a] --> H
        B[item_b] --> H
        C[criteria] --> H
        O[order: AB/BA] --> H
        H[SHA256 Hash] --> K[Cache Key]
    end
```

**Important**: `compare(A, B)` and `compare(B, A)` have different cache keys. This ensures LLM position bias is correctly reflected in the cache.

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `elimination_count` | 2 | Number of losses required for elimination |
| `comparison_rounds` | 2 | Number of rounds per match (even number recommended) |
| `seed` | None | Random seed (for reproducibility) |

## Matching Strategy

```mermaid
flowchart TD
    Start([Matching Start]) --> Group[Group by loss count]
    Group --> Sort[Sort by loss count ascending]
    Sort --> Loop{All brackets processed?}

    Loop -->|No| Shuffle[Shuffle within bracket]
    Shuffle --> Pair[Pair in twos]
    Pair --> Odd{Odd number?}

    Odd -->|Yes| Save[Carry over to next bracket]
    Odd -->|No| Next[Next bracket]

    Save --> Next
    Next --> Loop

    Loop -->|Yes| Return[Return match list]
    Return --> End([Matching End])
```

### Matching Example

Active participants: A(0 losses), B(0 losses), C(0 losses), D(1 loss), E(1 loss)

1. Bracket 0 (0 losses): [A, B, C] -> Shuffle -> [B, A, C]
   - Match 1: B vs A
   - Odd one out: C -> Carry over
2. Bracket 1 (1 loss): [D, E] + [C] -> Shuffle -> [E, C, D]
   - Match 2: E vs C
   - Odd one out: D (no opponent, wait for next round)

Result: [(B, A), (E, C)]
