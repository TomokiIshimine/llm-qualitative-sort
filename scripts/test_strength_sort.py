"""Test script for sorting creatures by strength using LLM."""

import asyncio
import os
import time

from llm_qualitative_sort import QualitativeSorter
from llm_qualitative_sort.providers.openai import OpenAIProvider


# 50+ diverse items: real animals, mythical creatures, famous characters
ITEMS = [
    # Real animals (weak to strong)
    "アリ",
    "カエル",
    "ネズミ",
    "ウサギ",
    "ネコ",
    "イヌ",
    "オオカミ",
    "ヒョウ",
    "ライオン",
    "トラ",
    "クマ",
    "サイ",
    "カバ",
    "ゾウ",
    "シロナガスクジラ",

    # Mythical creatures
    "ゴブリン",
    "コボルト",
    "オーク",
    "トロール",
    "ミノタウロス",
    "グリフォン",
    "キメラ",
    "ヒドラ",
    "フェニックス",
    "ドラゴン",
    "東洋龍",
    "バハムート",

    # Japanese mythology
    "河童",
    "天狗",
    "鬼",
    "八岐大蛇",
    "麒麟",

    # Famous characters - anime/manga
    "のび太",
    "ドラえもん",
    "ルフィ (ワンピース)",
    "ナルト",
    "悟空 (ドラゴンボール)",
    "サイタマ (ワンパンマン)",
    "全王 (ドラゴンボール超)",

    # Famous characters - games
    "スライム (ドラクエ)",
    "ピカチュウ",
    "リンク (ゼルダの伝説)",
    "マリオ",
    "クラウド (FF7)",
    "セフィロス (FF7)",

    # Famous characters - Western
    "スパイダーマン",
    "バットマン",
    "スーパーマン",
    "ソー (マーベル)",
    "ハルク",
    "サノス",

    # Cosmic/Abstract entities
    "デスノートのリューク",
    "死神 (一般的な概念)",
    "宇宙の創造神",
]

# Expected rough order (subjective, for reference)
EXPECTED_ROUGH_ORDER = [
    "アリ", "カエル", "ネズミ", "ウサギ", "スライム (ドラクエ)", "ネコ", "イヌ",
    "のび太", "マリオ", "ピカチュウ", "オオカミ", "ヒョウ", "ライオン", "トラ",
    "河童", "ゴブリン", "コボルト", "クマ", "オーク", "バットマン", "サイ",
    "カバ", "リンク (ゼルダの伝説)", "ゾウ", "トロール", "スパイダーマン",
    "天狗", "ミノタウロス", "鬼", "クラウド (FF7)", "ドラえもん",
    "グリフォン", "キメラ", "シロナガスクジラ", "ハルク", "ソー (マーベル)",
    "ヒドラ", "セフィロス (FF7)", "フェニックス", "スーパーマン", "ナルト",
    "麒麟", "ルフィ (ワンピース)", "八岐大蛇", "ドラゴン", "悟空 (ドラゴンボール)",
    "東洋龍", "サノス", "サイタマ (ワンパンマン)", "デスノートのリューク",
    "バハムート", "死神 (一般的な概念)", "全王 (ドラゴンボール超)", "宇宙の創造神",
]


def print_progress(event):
    """Print progress events."""
    from llm_qualitative_sort.events import EventType
    if event.type == EventType.MATCH_END:
        data = event.data
        print(f"  Match: {data['item_a'][:15]:15} vs {data['item_b'][:15]:15} -> Winner: {data['winner']}")
    elif event.type == EventType.BRACKET_CHANGE:
        data = event.data
        print(f"\n[Bracket Change] Remaining: {data['remaining_count']}, Eliminated: {data['eliminated_count']}")


async def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    print("=" * 60)
    print("LLM Qualitative Sort - Strength Ranking Test")
    print("=" * 60)
    print(f"Model: gpt-5-mini-2025-08-07")
    print(f"Items: {len(ITEMS)}")
    print(f"Criteria: 戦闘能力・強さ")
    print("=" * 60)

    provider = OpenAIProvider(
        api_key=api_key,
        model="gpt-5-mini-2025-08-07"
    )

    sorter = QualitativeSorter(
        provider=provider,
        criteria="戦闘能力・強さ（1対1で戦った場合にどちらが勝つか）",
        elimination_count=5,  # 5回負けで脱落
        comparison_rounds=2,  # 各マッチ2回の比較（偶数必須）
        max_concurrent_requests=5,  # 並列リクエスト数
        on_progress=print_progress,
    )

    print("\nStarting sort...\n")
    start_time = time.time()

    result = await sorter.sort(ITEMS)

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("RESULTS - Strength Ranking (Strongest to Weakest)")
    print("=" * 60)

    for rank, items in result.rankings:
        if len(items) == 1:
            print(f"  {rank:2}位: {items[0]}")
        else:
            print(f"  {rank:2}位: {', '.join(items)} (同率)")

    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"  Total matches: {result.statistics.total_matches}")
    print(f"  Total API calls: {result.statistics.total_api_calls}")
    print(f"  Cache hits: {result.statistics.cache_hits}")
    print(f"  Elapsed time: {elapsed:.2f}s")
    print(f"  Avg time per API call: {elapsed / max(result.statistics.total_api_calls, 1):.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
