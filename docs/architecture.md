# LLM Qualitative Sort - アーキテクチャドキュメント

## 概要

**llm-qualitative-sort** は、LLM（大規模言語モデル）を用いて定性的な基準でテキストデータをソートするPythonパッケージです。

マルチイリミネーショントーナメント方式を採用し、「文章の良さ」「キャラクターの強さ」など、定量的に比較できない評価観点に基づいて複数の項目を順位付けします。

## システムアーキテクチャ

```mermaid
graph TB
    subgraph "User Interface"
        User[ユーザー]
    end

    subgraph "Core Layer"
        Sorter[QualitativeSorter<br/>メインオーケストレーター]
    end

    subgraph "Tournament Layer"
        Tournament[MultiEliminationTournament<br/>トーナメント管理]
        Participant[Participant<br/>参加者管理]
    end

    subgraph "Provider Layer"
        Provider[LLMProvider<br/>抽象基底クラス]
        LangChain[LangChainProvider<br/>LangChain統合]
        Mock[MockLLMProvider<br/>テスト用]
    end

    subgraph "Cache Layer"
        Cache[Cache<br/>抽象基底クラス]
        Memory[MemoryCache<br/>メモリキャッシュ]
        File[FileCache<br/>ファイルキャッシュ]
    end

    subgraph "Output Layer"
        Formatters[Formatters<br/>出力フォーマッター]
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

## コンポーネント構成

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

    class MultiEliminationTournament {
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
    QualitativeSorter --> MultiEliminationTournament
    MultiEliminationTournament --> Participant
    LangChainProvider --|> LLMProvider
```

## データフロー

```mermaid
flowchart TD
    Start([開始]) --> Input[アイテムリスト入力]
    Input --> Validate{バリデーション}
    Validate -->|失敗| Error[エラー返却]
    Validate -->|成功| Init[トーナメント初期化]

    Init --> CheckComplete{トーナメント<br/>完了？}
    CheckComplete -->|Yes| Compile[結果コンパイル]
    CheckComplete -->|No| GetMatches[次のマッチ取得]

    GetMatches --> RunMatches[マッチ並列実行]
    RunMatches --> RecordResults[結果記録]
    RecordResults --> EmitProgress[進捗イベント発行]
    EmitProgress --> CheckComplete

    Compile --> CreateResult[SortResult作成]
    CreateResult --> FormatOutput{出力形式}

    FormatOutput -->|Sorting| SortOut[SortingOutput]
    FormatOutput -->|Ranking| RankOut[RankingOutput]
    FormatOutput -->|Percentile| PercOut[PercentileOutput]

    SortOut --> End([終了])
    RankOut --> End
    PercOut --> End
    Error --> End
```

## 主要コンポーネント

### 1. QualitativeSorter

メインオーケストレータークラス。すべてのコンポーネントを統合し、ソート処理全体を制御します。

**責務:**
- アイテムのバリデーション
- トーナメントの実行制御
- 並行リクエストの制限（Semaphore）
- 進捗イベントの発行
- 結果の集計

### 2. MultiEliminationTournament

マルチイリミネーション方式のトーナメントロジックを実装します。

**責務:**
- 参加者の管理（勝敗記録）
- ブラケット（敗北数グループ）によるマッチング
- 対戦履歴の追跡
- 最終順位の算出

### 3. LLMProvider

LLMとの通信を抽象化したインターフェース。

**実装:**
- `LangChainProvider`: LangChainを使用した汎用プロバイダー
- `MockLLMProvider`: テスト用のモックプロバイダー

### 4. Cache

比較結果をキャッシュし、重複したLLM呼び出しを防ぎます。

**実装:**
- `MemoryCache`: メモリ上のキャッシュ（セッション限定）
- `FileCache`: ファイルベースの永続キャッシュ

## 設計原則

### 依存性注入

```python
# プロバイダーとキャッシュは外部から注入
sorter = QualitativeSorter(
    provider=LangChainProvider(model),  # 注入
    criteria="文章の品質",
    cache=FileCache("./cache"),          # 注入
)
```

### 非同期処理

すべてのLLM呼び出しは `async/await` を使用し、`asyncio.Semaphore` で同時リクエスト数を制御します。

```python
async with self._semaphore:
    result = await self._provider.compare(first, second, self._criteria)
```

### イベント駆動の進捗報告

```python
def on_progress(event: ProgressEvent):
    print(f"{event.completed}/{event.total}: {event.message}")

sorter = QualitativeSorter(..., on_progress=on_progress)
```

## ファイル構成

```
src/llm_qualitative_sort/
├── __init__.py              # パブリックAPI
├── models.py                # データ構造
├── events.py                # イベントシステム
├── sorter.py                # メインクラス
├── metrics.py               # 評価メトリクス
├── providers/               # LLMプロバイダー
│   ├── base.py             # 抽象基底クラス
│   ├── langchain.py        # LangChain統合
│   ├── mock.py             # テスト用
│   └── errors.py           # エラーハンドリング
├── tournament/              # トーナメント処理
│   └── multi_elimination.py
├── cache/                   # キャッシュ機能
│   └── __init__.py
└── output/                  # 出力フォーマット
    ├── models.py
    ├── formatters.py
    └── calculators.py
```
