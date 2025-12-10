# CLAUDE.md

このファイルはClaude Codeがこのリポジトリで作業する際のガイドラインです。

## プロジェクト概要

**llm-qualitative-sort** - LLMを用いた定性的ソーティングパッケージ

スイス式トーナメント方式で、定量的に比較できない評価観点（文章の良さ、キャラクターの強さなど）に基づき、複数のテキストデータを順位付けします。

## 開発方針

### テスト駆動開発（TDD）を厳守

すべての機能実装において、以下のサイクルを必ず守ること：

1. **Red**: 失敗するテストを先に書く
2. **Green**: テストをパスする最小限のコードを実装
3. **Refactor**: コードを改善（テストは常にパス状態を維持）

```bash
# テスト実行
python -m pytest tests/ -v

# 特定のテストファイル
python -m pytest tests/test_sorter.py -v

# カバレッジ付き
python -m pytest tests/ --cov=src/llm_qualitative_sort
```

### 保守性の高いコードを書く

- **単一責任の原則**: 各クラス・関数は1つの責任のみを持つ
- **明確な型ヒント**: すべての関数に型アノテーションを付ける
- **適切な抽象化**: ABC（抽象基底クラス）を使用してインターフェースを定義
- **依存性注入**: プロバイダーやキャッシュは外部から注入可能に
- **dataclassの活用**: データ構造には`@dataclass`を使用

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

tests/                    # テストファイル（対応するsrcと同じ構造）
```

## コーディング規約

### 命名規則

- クラス: `PascalCase` (例: `QualitativeSorter`)
- 関数・変数: `snake_case` (例: `get_rankings`)
- 定数: `UPPER_SNAKE_CASE` (例: `DEFAULT_BASE_URL`)
- プライベート: `_prefix` (例: `_cache`, `_emit_progress`)

### インポート順序

```python
# 1. 標準ライブラリ
import asyncio
from dataclasses import dataclass

# 2. サードパーティ
import aiohttp

# 3. ローカル
from llm_qualitative_sort.models import ComparisonResult
```

### 非同期処理

- すべてのLLM呼び出しは`async/await`を使用
- `asyncio.Semaphore`で同時リクエスト数を制御
- `asyncio.gather`で並列実行

## 新機能追加の手順

1. `tests/`に新しいテストファイルまたはテストケースを追加
2. テストを実行して失敗を確認（Red）
3. `src/`に最小限の実装を追加
4. テストをパス（Green）
5. 必要に応じてリファクタリング
6. `__init__.py`にエクスポートを追加（公開APIの場合）

## 重要なコマンド

```bash
# パッケージインストール（開発モード）
pip install -e ".[dev]"

# 全テスト実行
python -m pytest tests/ -v

# 特定のテストのみ
python -m pytest tests/test_sorter.py::TestQualitativeSorterSort -v

# Lint（将来追加予定）
# ruff check src/ tests/

# 型チェック（将来追加予定）
# mypy src/
```

## 要件定義書

詳細な仕様は `llm_qualitative_sort_requirements_v2.docx` を参照してください。

主な機能：
- ペア比較機能（LLMによる2項目比較）
- スイス式トーナメント（N回負けで敗退）
- 非同期処理（asyncio）
- キャッシュ機能（メモリ/ファイル）
- 進捗コールバック
