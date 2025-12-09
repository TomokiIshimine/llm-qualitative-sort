"""Google Gemini provider implementation."""

import json
import aiohttp

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.models import ComparisonResult


class GoogleProvider(LLMProvider):
    """Google Gemini API provider for LLM comparisons."""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-2.0-flash"

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
        """Compare two items using Google Gemini API."""
        prompt = self._build_prompt(item_a, item_b, criteria)

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0},
                },
            ) as response:
                raw_response = await response.json()

                if response.status != 200:
                    return ComparisonResult(
                        winner=None,
                        reasoning=f"API error: {raw_response}",
                        raw_response=raw_response
                    )

                return self._parse_response(raw_response)

    def _build_prompt(self, item_a: str, item_b: str, criteria: str) -> str:
        """Build comparison prompt."""
        return f"""Compare the following two items based on this criteria: {criteria}

Item A:
{item_a}

Item B:
{item_b}

You must respond with ONLY a JSON object in this exact format:
{{"winner": "A" or "B", "reasoning": "your explanation"}}

Choose which item is better based on the criteria. You must pick either A or B."""

    def _parse_response(self, raw_response: dict) -> ComparisonResult:
        """Parse Google Gemini response into ComparisonResult."""
        try:
            content = raw_response["candidates"][0]["content"]["parts"][0]["text"]
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
