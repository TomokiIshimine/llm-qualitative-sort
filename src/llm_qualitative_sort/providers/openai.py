"""OpenAI provider implementation using the official SDK."""

import json

from openai import AsyncOpenAI

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.models import ComparisonResult


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for LLM comparisons.

    Uses the official OpenAI Python SDK for API calls.
    Supports OpenAI API and compatible endpoints.
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
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL
        )

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using OpenAI API."""
        prompt = self._build_prompt(item_a, item_b, criteria)

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            raw_response = response.model_dump()
            return self._parse_response(raw_response)

        except Exception as e:
            return ComparisonResult(
                winner=None,
                reasoning=f"API error: {e}",
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
