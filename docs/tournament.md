# スイス式トーナメント

## 概要

スイス式トーナメントは、参加者が指定された回数（N回）負けると脱落する方式のトーナメントです。シングルイリミネーション（1回負けで脱落）と異なり、複数回の敗北を許容することで、より公平な順位付けが可能になります。

## トーナメントの仕組み

### 基本ルール

1. 全参加者は0敗からスタート
2. 各マッチで負けると敗北数が1増加
3. 敗北数が `elimination_count` に達した参加者は脱落
4. アクティブな参加者が1人以下になるまで継続
5. 最終順位は勝利数で決定

```mermaid
flowchart TD
    Start([トーナメント開始]) --> Init[全参加者: 0勝0敗]
    Init --> Check{アクティブ<br/>参加者 > 1?}

    Check -->|No| End([トーナメント終了])
    Check -->|Yes| Bracket[敗北数でブラケット分け]

    Bracket --> Pair[同ブラケット内でペアリング]
    Pair --> Odd{端数あり?}

    Odd -->|Yes| Cross[異ブラケットとマッチング]
    Odd -->|No| Match[マッチ実行]

    Cross --> Match
    Match --> Record[結果記録]
    Record --> Update[勝敗数更新]
    Update --> Eliminate{N敗到達?}

    Eliminate -->|Yes| Remove[脱落処理]
    Eliminate -->|No| Check

    Remove --> Check
```

### ブラケットシステム

参加者は敗北数によってブラケット（グループ）に分類され、同じブラケット内で優先的にマッチングされます。

```mermaid
graph TD
    subgraph "ブラケット 0（0敗）"
        A1[参加者A]
        A2[参加者B]
        A3[参加者C]
        A4[参加者D]
    end

    subgraph "ブラケット 1（1敗）"
        B1[参加者E]
        B2[参加者F]
        B3[参加者G]
    end

    subgraph "ブラケット 2（2敗=脱落）"
        C1[参加者H ×]
        C2[参加者I ×]
    end

    A1 -.->|対戦| A2
    A3 -.->|対戦| A4
    B1 -.->|対戦| B2
    B3 -.->|異ブラケット| A1
```

## マッチの実行フロー

### 位置バイアスの軽減

LLMは提示順序によってバイアスが生じる可能性があるため、各マッチでは複数ラウンドを実行し、順序を交互に入れ替えます。

```mermaid
sequenceDiagram
    participant S as Sorter
    participant P as Provider
    participant C as Cache

    Note over S: マッチ開始: A vs B

    rect rgb(240, 248, 255)
        Note over S: ラウンド1（順序: AB）
        S->>C: キャッシュ確認 (A, B, "AB")
        C-->>S: キャッシュミス
        S->>P: compare(A, B, criteria)
        P-->>S: winner: "A"
        S->>C: キャッシュ保存
    end

    rect rgb(255, 248, 240)
        Note over S: ラウンド2（順序: BA）
        S->>C: キャッシュ確認 (B, A, "BA")
        C-->>S: キャッシュミス
        S->>P: compare(B, A, criteria)
        P-->>S: winner: "B" → 変換後 "A"
        S->>C: キャッシュ保存
    end

    Note over S: 集計: A=2勝, B=0勝
    Note over S: 勝者: A
```

### 勝敗判定ロジック

```mermaid
flowchart TD
    Start([マッチ開始]) --> Round1[ラウンド1: AB順序で比較]
    Round1 --> Result1{結果}

    Result1 -->|A勝利| WinA1[A勝利数 +1]
    Result1 -->|B勝利| WinB1[B勝利数 +1]
    Result1 -->|エラー| Skip1[スキップ]

    WinA1 --> Round2
    WinB1 --> Round2
    Skip1 --> Round2

    Round2[ラウンド2: BA順序で比較] --> Result2{結果}

    Result2 -->|A勝利| WinA2[A勝利数 +1]
    Result2 -->|B勝利| WinB2[B勝利数 +1]
    Result2 -->|エラー| Skip2[スキップ]

    WinA2 --> Judge
    WinB2 --> Judge
    Skip2 --> Judge

    Judge{勝敗判定} --> |A勝利数 > B勝利数| WinnerA[勝者: A]
    Judge --> |B勝利数 > A勝利数| WinnerB[勝者: B]
    Judge --> |同数| Draw[引き分け: None]

    WinnerA --> End([マッチ終了])
    WinnerB --> End
    Draw --> End
```

## トーナメント進行の例

### 4アイテム、elimination_count=2 の場合

```mermaid
graph TB
    subgraph "ラウンド1"
        M1[A vs B] --> R1[A勝利]
        M2[C vs D] --> R2[C勝利]
    end

    subgraph "状態1"
        S1A[A: 1勝0敗]
        S1B[B: 0勝1敗]
        S1C[C: 1勝0敗]
        S1D[D: 0勝1敗]
    end

    subgraph "ラウンド2"
        M3[A vs C<br/>0敗同士] --> R3[A勝利]
        M4[B vs D<br/>1敗同士] --> R4[D勝利]
    end

    subgraph "状態2"
        S2A[A: 2勝0敗]
        S2B["B: 0勝2敗 ×"]
        S2C[C: 1勝1敗]
        S2D[D: 1勝1敗]
    end

    subgraph "ラウンド3"
        M5[C vs D<br/>1敗同士] --> R5[C勝利]
    end

    subgraph "状態3"
        S3A[A: 2勝0敗]
        S3C[C: 2勝1敗]
        S3D["D: 1勝2敗 ×"]
    end

    subgraph "ラウンド4"
        M6[A vs C] --> R6[A勝利]
    end

    subgraph "最終状態"
        FA[A: 3勝0敗]
        FC["C: 2勝2敗 ×"]
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

### 最終順位（勝利数順）

| 順位 | アイテム | 勝利数 | 敗北数 |
|------|----------|--------|--------|
| 1位  | A        | 3      | 0      |
| 2位  | C        | 2      | 2      |
| 3位  | D        | 1      | 2      |
| 4位  | B        | 0      | 2      |

## キャッシュキーの構造

キャッシュは比較の再利用を可能にしますが、順序バイアスを考慮して順序情報もキーに含めます。

```mermaid
flowchart LR
    subgraph "キャッシュキー生成"
        A[item_a] --> H
        B[item_b] --> H
        C[criteria] --> H
        O[order: AB/BA] --> H
        H[SHA256ハッシュ] --> K[キャッシュキー]
    end
```

**重要**: `compare(A, B)` と `compare(B, A)` は異なるキャッシュキーを持ちます。これにより、LLMの位置バイアスがキャッシュに正しく反映されます。

## 設定パラメータ

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `elimination_count` | 2 | 脱落に必要な敗北数 |
| `comparison_rounds` | 2 | 1マッチあたりのラウンド数（偶数推奨） |
| `seed` | None | 乱数シード（再現性確保用） |

## マッチング戦略

```mermaid
flowchart TD
    Start([マッチング開始]) --> Group[敗北数でグループ化]
    Group --> Sort[敗北数昇順でソート]
    Sort --> Loop{全ブラケット処理?}

    Loop -->|No| Shuffle[ブラケット内シャッフル]
    Shuffle --> Pair[2人ずつペアリング]
    Pair --> Odd{端数あり?}

    Odd -->|Yes| Save[次ブラケットへ繰り越し]
    Odd -->|No| Next[次のブラケットへ]

    Save --> Next
    Next --> Loop

    Loop -->|Yes| Return[マッチリスト返却]
    Return --> End([マッチング終了])
```

### マッチング例

アクティブ参加者: A(0敗), B(0敗), C(0敗), D(1敗), E(1敗)

1. ブラケット0（0敗）: [A, B, C] → シャッフル → [B, A, C]
   - マッチ1: B vs A
   - 端数: C → 繰り越し
2. ブラケット1（1敗）: [D, E] + [C] → シャッフル → [E, C, D]
   - マッチ2: E vs C
   - 端数: D（対戦相手なし、次ラウンドへ）

結果: [(B, A), (E, C)]
