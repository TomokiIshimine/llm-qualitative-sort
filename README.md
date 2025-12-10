# llm-qualitative-sort

LLMを用いた定性的ソーティングPythonパッケージ

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

### 基本的な使用例

```python
import asyncio
from llm_qualitative_sort import QualitativeSorter, OpenAIProvider

async def main():
    # プロバイダーを設定
    provider = OpenAIProvider(
        api_key="your-api-key",
        model="gpt-4o"  # デフォルト
    )

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
from llm_qualitative_sort import QualitativeSorter, GoogleProvider

provider = GoogleProvider(
    api_key="your-google-api-key",
    model="gemini-1.5-flash"  # デフォルト
)

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
from llm_qualitative_sort import QualitativeSorter, OpenAIProvider, ProgressEvent

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

| プロバイダー | クラス | デフォルトモデル |
|-------------|--------|-----------------|
| OpenAI | `OpenAIProvider` | `gpt-4o` |
| Google | `GoogleProvider` | `gemini-1.5-flash` |
| テスト用 | `MockLLMProvider` | - |

### キャッシュ

| キャッシュ | クラス | 説明 |
|-----------|--------|------|
| メモリ | `MemoryCache` | インメモリキャッシュ |
| ファイル | `FileCache` | ファイルベースの永続化キャッシュ |

## プロジェクト構造

```
src/llm_qualitative_sort/
├── __init__.py           # パブリックAPI
├── models.py             # データ構造（dataclass）
├── events.py             # イベント定義
├── sorter.py             # メインクラス
├── providers/            # LLMプロバイダー
│   ├── base.py           # 抽象基底クラス
│   ├── openai.py
│   ├── google.py
│   └── mock.py           # テスト用
├── tournament/           # トーナメント処理
│   └── swiss_system.py
└── cache/                # キャッシュ機能
    ├── base.py           # 抽象基底クラス
    ├── memory.py
    └── file.py
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

## 必要要件

- Python >= 3.10
- aiohttp >= 3.8.0

## ライセンス

MIT License
