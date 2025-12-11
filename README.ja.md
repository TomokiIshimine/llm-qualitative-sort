# llm-qualitative-sort

LLMを用いた定性的ソーティングPythonパッケージ

[English README](README.md)

## 概要

**llm-qualitative-sort**は、スイス式トーナメント方式を用いて、定量的に比較できない評価観点（文章の良さ、キャラクターの強さなど）に基づき、複数のテキストデータを順位付けするPythonパッケージです。

LLMがペアごとに比較を行い、トーナメント形式で勝ち残りを決定することで、主観的な評価基準でも一貫した順位付けを実現します。

## 特徴

- **スイス式トーナメント**: N回負けで敗退する公平なトーナメント方式
- **複数のLLMプロバイダー対応**: OpenAI、Google Gemini をサポート
- **非同期処理**: asyncioによる効率的な並列比較
- **位置バイアス軽減**: 比較順序を入れ替えて複数回比較
- **キャッシュ機能**: メモリキャッシュ・ファイルキャッシュで重複呼び出しを削減
- **進捗コールバック**: リアルタイムで進捗状況を取得可能
- **拡張性**: 抽象基底クラスによるカスタムプロバイダー・キャッシュの実装が可能

## インストール

```bash
pip install llm-qualitative-sort
```

開発用依存関係を含めてインストール:

```bash
pip install llm-qualitative-sort[dev]
```

## 使用方法

### 基本的な使用例（OpenAI）

```python
import asyncio
from langchain_openai import ChatOpenAI
from llm_qualitative_sort import QualitativeSorter, LangChainProvider

async def main():
    # LangChainモデルを設定
    llm = ChatOpenAI(model="gpt-5-nano", api_key="your-api-key")
    provider = LangChainProvider(llm=llm)

    # ソーターを作成
    sorter = QualitativeSorter(
        provider=provider,
        criteria="文章の読みやすさと説得力",
        elimination_count=2,  # 2回負けで敗退
        comparison_rounds=2,  # 各マッチで2回比較（位置バイアス軽減）
    )

    # ソート対象のアイテム
    items = [
        "短い文章は読みやすい。",
        "詳細な説明を含む長い文章は、情報量が多く説得力がある。",
        "適度な長さで要点を押さえた文章がベストである。",
    ]

    # ソートを実行
    result = await sorter.sort(items)

    # 結果を表示
    print("ランキング:")
    for rank, tied_items in result.rankings:
        for item in tied_items:
            print(f"  {rank}位: {item[:30]}...")

    print(f"\n統計:")
    print(f"  総マッチ数: {result.statistics.total_matches}")
    print(f"  API呼び出し数: {result.statistics.total_api_calls}")
    print(f"  処理時間: {result.statistics.elapsed_time:.2f}秒")

asyncio.run(main())
```

### Google Gemini を使用

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from llm_qualitative_sort import QualitativeSorter, LangChainProvider

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key="your-google-api-key")
provider = LangChainProvider(llm=llm)

sorter = QualitativeSorter(
    provider=provider,
    criteria="評価基準",
)
```

### Anthropic Claude を使用

```python
from langchain_anthropic import ChatAnthropic
from llm_qualitative_sort import QualitativeSorter, LangChainProvider

llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key="your-anthropic-api-key")
provider = LangChainProvider(llm=llm)

sorter = QualitativeSorter(
    provider=provider,
    criteria="評価基準",
)
```

### キャッシュを使用

```python
from llm_qualitative_sort import QualitativeSorter, OpenAIProvider, MemoryCache, FileCache

# メモリキャッシュ
memory_cache = MemoryCache()

# ファイルキャッシュ（永続化）
file_cache = FileCache(cache_dir="./cache")

sorter = QualitativeSorter(
    provider=provider,
    criteria="評価基準",
    cache=memory_cache,  # または file_cache
)
```

### 進捗コールバック

```python
from llm_qualitative_sort import QualitativeSorter, LangChainProvider, ProgressEvent

def on_progress(event: ProgressEvent):
    print(f"[{event.type.name}] {event.message} ({event.completed}/{event.total})")

sorter = QualitativeSorter(
    provider=provider,
    criteria="評価基準",
    on_progress=on_progress,
)
```

## API リファレンス

### QualitativeSorter

メインのソートクラス。

```python
QualitativeSorter(
    provider: LLMProvider,           # LLMプロバイダー（必須）
    criteria: str,                   # 評価基準（必須）
    elimination_count: int = 2,      # 敗退までの負け数
    comparison_rounds: int = 2,      # マッチあたりの比較回数（偶数）
    max_concurrent_requests: int = 10,  # 最大同時リクエスト数
    cache: Cache | None = None,      # キャッシュ
    on_progress: Callable | None = None,  # 進捗コールバック
    seed: int | None = None,         # 乱数シード（再現性用）
)
```

**メソッド:**

- `async sort(items: list[str]) -> SortResult`: アイテムをソート

### SortResult

ソート結果を格納するデータクラス。

```python
@dataclass
class SortResult:
    rankings: list[tuple[int, list[str]]]  # (順位, [アイテム])のリスト
    match_history: list[MatchResult]       # 全マッチの履歴
    statistics: Statistics                  # 統計情報
```

### LLMプロバイダー

| クラス | 説明 |
|--------|------|
| `LangChainProvider` | LangChain BaseChatModel を使用する汎用プロバイダー |
| `MockLLMProvider` | テスト用モックプロバイダー |

`LangChainProvider` は以下のLangChainモデルをサポート:
- `langchain_openai.ChatOpenAI` (OpenAI)
- `langchain_google_genai.ChatGoogleGenerativeAI` (Google Gemini)
- `langchain_anthropic.ChatAnthropic` (Anthropic Claude)
- その他 `with_structured_output()` をサポートするLangChainモデル

### キャッシュ

| キャッシュ | クラス | 説明 |
|-----------|--------|------|
| メモリ | `MemoryCache` | インメモリキャッシュ |
| ファイル | `FileCache` | ファイルベースの永続化キャッシュ |

### 出力フォーマッター

ソート結果を様々な形式に変換できます。

```python
from llm_qualitative_sort import to_sorting, to_ranking, to_percentile

# シンプルなソート済みリスト
sorting_output = to_sorting(result)
print(sorting_output.items)  # ["1位のアイテム", "2位のアイテム", ...]

# 詳細なランキング（勝利数、同順位情報付き）
ranking_output = to_ranking(result)
for entry in ranking_output.entries:
    print(f"{entry.rank}位: {entry.item} (勝利数: {entry.wins})")

# パーセンタイル（ティア分類付き）
percentile_output = to_percentile(result)
for entry in percentile_output.entries:
    print(f"{entry.item}: {entry.percentile:.0f}% ({entry.tier})")
```

### 精度評価メトリクス

期待値と比較してソート精度を評価できます。

```python
from llm_qualitative_sort import (
    flatten_rankings,
    calculate_kendall_tau,
    calculate_all_metrics,
)

# ランキングをフラットなリストに変換
actual = flatten_rankings(result.rankings)
expected = ["期待1位", "期待2位", "期待3位"]

# Kendall's tau 相関係数 (-1〜1、1が完全一致)
tau = calculate_kendall_tau(actual, expected)

# 全メトリクスを一括計算
metrics = calculate_all_metrics(actual, expected)
print(f"Kendall's tau: {metrics.kendall_tau:.3f}")
print(f"Top-10 正解率: {metrics.top_10_accuracy:.1%}")
print(f"ペア正解率: {metrics.correct_pair_ratio:.1%}")
```

## プロジェクト構造

```
src/llm_qualitative_sort/
├── __init__.py           # パブリックAPI
├── models.py             # データ構造（dataclass）
├── events.py             # イベント定義
├── sorter.py             # メインクラス
├── metrics.py            # 精度評価メトリクス
├── utils.py              # ユーティリティ関数
├── providers/            # LLMプロバイダー
│   ├── __init__.py
│   ├── base.py           # 抽象基底クラス（LLMProvider）
│   ├── langchain.py      # LangChain統合プロバイダー
│   ├── mock.py           # テスト用
│   └── errors.py         # エラーハンドリング
├── tournament/           # トーナメント処理
│   ├── __init__.py
│   └── swiss_system.py
├── output/               # 出力フォーマッター
│   ├── __init__.py
│   ├── models.py         # 出力用データ構造
│   ├── calculators.py    # 計算ロジック
│   └── formatters.py     # フォーマット変換
└── cache/                # キャッシュ機能
    └── __init__.py       # Cache, MemoryCache, FileCache
```

## 動作原理

### スイス式トーナメント

1. 全参加者が0敗の状態でスタート
2. 同じ敗数のグループ（ブラケット）内でランダムにペアを組む
3. LLMが指定された評価基準でペア比較を実施
4. 敗者の敗数をインクリメント
5. N敗（デフォルト2敗）で敗退
6. 最後の1人が残るまで繰り返し
7. 勝利数に基づいてランキングを決定

### 位置バイアス軽減

LLMには「先に提示されたものを選びやすい」などの位置バイアスがあります。これを軽減するため、各マッチで提示順序を入れ替えて複数回比較を行い、多数決で勝者を決定します。

## 開発環境セットアップ

### 環境構築

```bash
# リポジトリをクローン
git clone https://github.com/TomokiIshimine/llm-qualitative-sort.git
cd llm-qualitative-sort

# 開発モードでインストール（開発用依存関係を含む）
pip install -e ".[dev]"

# テスト実行で動作確認
python -m pytest tests/ -v
```

### 開発用依存関係

- `pytest>=7.0.0` - テストフレームワーク
- `pytest-asyncio>=0.21.0` - 非同期テストサポート
- `scipy>=1.10.0` - 統計処理

### テストコマンド

```bash
# 全テスト実行
python -m pytest tests/ -v

# 特定のテストファイル
python -m pytest tests/test_sorter.py -v

# 特定のテストクラス
python -m pytest tests/test_sorter.py::TestQualitativeSorterSort -v

# カバレッジ付き
python -m pytest tests/ --cov=src/llm_qualitative_sort
```

### 開発方針

このプロジェクトではテスト駆動開発（TDD）を採用しています：

1. **Red**: 失敗するテストを先に書く
2. **Green**: テストをパスする最小限のコードを実装
3. **Refactor**: コードを改善（テストは常にパス状態を維持）

## ドキュメント

| ドキュメント | 説明 |
|-------------|------|
| [アーキテクチャ](docs/architecture.ja.md) | システムアーキテクチャと設計原則 |
| [スイス式トーナメント](docs/tournament.ja.md) | トーナメントアルゴリズムとマッチング戦略 |
| [APIリファレンス](docs/api-reference.ja.md) | 詳細なAPIドキュメントと使用例 |

英語版も利用可能です（`*.md`）。

## デプロイ

### PyPIへの公開

このパッケージはGitHub Actionsによる自動PyPI公開を使用しています（Trusted Publishing、APIトークン不要）。

**リリース手順:**

1. `pyproject.toml`のバージョンを更新
2. バージョンタグを作成してプッシュ:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. GitHub Actionsが自動的に:
   - Python 3.10, 3.11, 3.12でテストを実行
   - パッケージをビルド
   - PyPIに公開

**必要な設定:**
- PyPIプロジェクト設定でTrusted Publishingを設定
- GitHubリポジトリで`pypi`環境を設定

## 必要要件

- Python >= 3.10
- aiohttp >= 3.8.0

## ライセンス

MIT License
