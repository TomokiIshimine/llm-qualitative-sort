"""OpenAI provider implementation using the official SDK with Structured Outputs."""

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.errors import create_error_result
from llm_qualitative_sort.models import ComparisonResult, ComparisonResponse


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for LLM comparisons.

    Uses the official OpenAI Python SDK with Structured Outputs
    for reliable JSON responses.
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = 0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            model=model or self.DEFAULT_MODEL
        )
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL
        )
        self._temperature = temperature

    async def compare(
        self,
        item_a: str,
        item_b: str,
        criteria: str
    ) -> ComparisonResult:
        """Compare two items using OpenAI API with Structured Outputs."""
        prompt = self._build_prompt(item_a, item_b, criteria)

        try:
            # Build kwargs, only include temperature if specified
            kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": ComparisonResponse,
            }
            if self._temperature is not None:
                kwargs["temperature"] = self._temperature

            response = await self._client.beta.chat.completions.parse(**kwargs)

            raw_response = response.model_dump()
            parsed = response.choices[0].message.parsed

            # Check for refusal
            if response.choices[0].message.refusal:
                return ComparisonResult(
                    winner=None,
                    reasoning=f"Model refused: {response.choices[0].message.refusal}",
                    raw_response=raw_response
                )

            # parsed is already validated as ComparisonResponse
            if parsed is None:
                return ComparisonResult(
                    winner=None,
                    reasoning="Failed to parse structured output",
                    raw_response=raw_response
                )

            return ComparisonResult(
                winner=parsed.winner,
                reasoning=parsed.reasoning,
                raw_response=raw_response
            )

        except RateLimitError as e:
            return create_error_result(e, "rate_limit", "Rate limit exceeded")
        except APITimeoutError as e:
            return create_error_result(e, "timeout", "Request timeout")
        except APIConnectionError as e:
            return create_error_result(e, "connection", "Connection error")
        except APIError as e:
            return create_error_result(e, "api", "API error")
