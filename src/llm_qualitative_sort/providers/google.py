"""Google Gemini provider implementation using the official google-genai SDK."""

import json

from google import genai
from google.genai import types

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.models import ComparisonResult


class GoogleProvider(LLMProvider):
    """Google Gemini API provider for LLM comparisons.

    Uses the official Google Gen AI SDK (google-genai) for API calls.
    This is the recommended SDK as of 2025.
    """

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
        self._client = genai.Client(api_key=api_key)

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using Google Gemini API."""
        prompt = self._build_prompt(item_a, item_b, criteria)

        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                ),
            )

            raw_response = {
                "text": response.text,
                "candidates": response.candidates,
            }
            return self._parse_response(raw_response)

        except Exception as e:
            return ComparisonResult(
                winner=None,
                reasoning=f"API error: {e}",
                raw_response={"error": str(e)}
            )

    def _parse_response(self, raw_response: dict) -> ComparisonResult:
        """Parse Google Gemini response into ComparisonResult."""
        try:
            content = raw_response["text"]
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
