#!/usr/bin/env python3
"""GPT統合テスト - 実際のGPTモデルを使用した動作確認スクリプト"""

import asyncio
import os
import sys
import json
import urllib.request
from typing import Optional
from dataclasses import dataclass

# プロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_qualitative_sort import (
    QualitativeSorter,
    MemoryCache,
    EventType,
)
from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.models import ComparisonResult


class OpenAIProviderSync(LLMProvider):
    """同期HTTPを使用したOpenAIプロバイダー（テスト用）

    Note: aiohttp のDNS解決に問題がある環境向けのワークアラウンド実装
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            model=model or self.DEFAULT_MODEL
        )

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using OpenAI API."""
        prompt = self._build_prompt(item_a, item_b, criteria)

        # 同期的なHTTPリクエスト（スレッドプールで実行）
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_request, prompt
        )

    def _sync_request(self, prompt: str) -> ComparisonResult:
        """同期的なHTTPリクエスト"""
        url = f"{self.base_url}/chat/completions"

        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                raw_response = json.loads(response.read())
                return self._parse_response(raw_response)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return ComparisonResult(
                winner=None,
                reasoning=f"API error: {e.code} - {error_body}",
                raw_response={"error": error_body}
            )
        except Exception as e:
            return ComparisonResult(
                winner=None,
                reasoning=f"Request error: {e}",
                raw_response={"error": str(e)}
            )

    def _parse_response(self, raw_response: dict) -> ComparisonResult:
        """Parse OpenAI response into ComparisonResult."""
        try:
            content = raw_response["choices"][0]["message"]["content"]
            # Try to parse JSON from response
            data = json.loads(content)
            winner = data.get("winner")
            reasoning = data.get("reasoning", "")

            if winner not in ("A", "B"):
                return ComparisonResult(
                    winner=None,
                    reasoning=f"Invalid winner: {winner}",
                    raw_response=raw_response
                )

            return ComparisonResult(
                winner=winner,
                reasoning=reasoning,
                raw_response=raw_response
            )
        except (KeyError, json.JSONDecodeError) as e:
            return ComparisonResult(
                winner=None,
                reasoning=f"Failed to parse response: {e}",
                raw_response=raw_response
            )


def progress_callback(event):
    """進捗コールバック"""
    if event.type == EventType.MATCH_START:
        item_a = event.data['item_a'][:40] + ('...' if len(event.data['item_a']) > 40 else '')
        item_b = event.data['item_b'][:40] + ('...' if len(event.data['item_b']) > 40 else '')
        print(f"  🔄 対戦開始: {item_a} vs {item_b}")
    elif event.type == EventType.MATCH_END:
        winner = event.data.get('winner', 'draw')
        print(f"  ✅ 対戦終了: 勝者 = {winner}")


async def test_basic_sorting():
    """基本的なソートテスト - 短い文章の比較"""
    print("=" * 60)
    print("テスト1: プログラミング言語の説明文（わかりやすさでソート）")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("エラー: OPENAI_API_KEY環境変数が設定されていません")
        return False

    provider = OpenAIProviderSync(
        api_key=api_key,
        model="gpt-4o-mini"
    )

    cache = MemoryCache()

    sorter = QualitativeSorter(
        provider=provider,
        criteria="初心者にとってのわかりやすさ",
        elimination_count=2,
        comparison_rounds=2,
        max_concurrent_requests=3,
        cache=cache,
        on_progress=progress_callback,
    )

    # テストデータ: プログラミング言語の説明
    items = [
        "Pythonはシンプルな文法で読みやすく、初心者にも学びやすいプログラミング言語です。",
        "Rustは所有権システムによりメモリ安全性を保証する、高性能なシステムプログラミング言語です。",
        "JavaScriptはWebブラウザで動作し、動的な型付けを持つスクリプト言語です。",
        "Haskellは純粋関数型言語で、遅延評価と強力な型システムを特徴とします。",
    ]

    print("\n📝 テストデータ:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")

    print("\n🏆 ソート実行中...")
    result = await sorter.sort(items)

    print("\n📊 結果:")
    print("  順位:")
    for rank, tier_items in result.rankings:
        for item in tier_items:
            print(f"    {rank}位: {item}")

    print(f"\n  統計情報:")
    print(f"    総マッチ数: {result.statistics.total_matches}")
    print(f"    APIコール数: {result.statistics.total_api_calls}")
    print(f"    キャッシュヒット: {result.statistics.cache_hits}")
    print(f"    実行時間: {result.statistics.elapsed_time:.2f}秒")

    return True


async def test_numeric_sorting():
    """数値の大小比較テスト"""
    print("\n" + "=" * 60)
    print("テスト2: 数値の大小比較（大きい順にソート）")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return False

    provider = OpenAIProviderSync(
        api_key=api_key,
        model="gpt-4o-mini"
    )

    sorter = QualitativeSorter(
        provider=provider,
        criteria="数値として大きい方を選んでください",
        elimination_count=2,
        comparison_rounds=2,
        max_concurrent_requests=3,
        on_progress=progress_callback,
    )

    # テストデータ: 数値（正しい順序が明確）
    items = ["100", "42", "7", "999", "256"]
    expected_order = ["999", "256", "100", "42", "7"]

    print("\n📝 テストデータ:", items)
    print("📌 期待される順序:", expected_order)

    print("\n🏆 ソート実行中...")
    result = await sorter.sort(items)

    print("\n📊 結果:")
    actual_order = []
    for rank, tier_items in result.rankings:
        for item in tier_items:
            actual_order.append(item)
            print(f"    {rank}位: {item}")

    # 結果検証
    print(f"\n  実際の順序: {actual_order}")
    print(f"  期待される順序: {expected_order}")

    # 上位3つが正しいか確認
    top3_correct = actual_order[:3] == expected_order[:3]
    print(f"  上位3つの正確性: {'✅ 正しい' if top3_correct else '❌ 異なる'}")

    return True


async def test_character_strength():
    """キャラクターの強さ比較テスト"""
    print("\n" + "=" * 60)
    print("テスト3: 架空キャラクターの戦闘力（強さ順にソート）")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return False

    provider = OpenAIProviderSync(
        api_key=api_key,
        model="gpt-4o-mini"
    )

    sorter = QualitativeSorter(
        provider=provider,
        criteria="戦闘能力や強さの観点で、より強いキャラクターを選んでください。一般的な認識や作中の描写を参考にしてください。",
        elimination_count=2,
        comparison_rounds=2,
        max_concurrent_requests=3,
        on_progress=progress_callback,
    )

    # テストデータ: 有名なキャラクター
    items = [
        "孫悟空（ドラゴンボール）",
        "ルフィ（ワンピース）",
        "ナルト（NARUTO）",
        "一般的な成人男性",
    ]

    print("\n📝 テストデータ:")
    for item in items:
        print(f"  - {item}")

    print("\n🏆 ソート実行中...")
    result = await sorter.sort(items)

    print("\n📊 結果:")
    for rank, tier_items in result.rankings:
        for item in tier_items:
            print(f"    {rank}位: {item}")

    print(f"\n  統計情報:")
    print(f"    総マッチ数: {result.statistics.total_matches}")
    print(f"    APIコール数: {result.statistics.total_api_calls}")
    print(f"    実行時間: {result.statistics.elapsed_time:.2f}秒")

    return True


async def main():
    """メイン関数"""
    print("🚀 GPT統合テスト開始")
    print("=" * 60)
    print(f"使用モデル: gpt-4o-mini")
    print("=" * 60)

    success = True

    try:
        # テスト1: 基本的なソート
        if not await test_basic_sorting():
            success = False

        # テスト2: 数値比較
        if not await test_numeric_sorting():
            success = False

        # テスト3: キャラクター強さ
        if not await test_character_strength():
            success = False

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ 全てのテストが完了しました")
    else:
        print("❌ 一部のテストが失敗しました")
    print("=" * 60)

    return success


if __name__ == "__main__":
    asyncio.run(main())
