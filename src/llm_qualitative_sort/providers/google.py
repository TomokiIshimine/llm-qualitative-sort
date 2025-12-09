"""Google Gemini provider implementation using the official google-genai SDK with Structured Outputs."""

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.errors import create_error_result
from llm_qualitative_sort.models import ComparisonResult, ComparisonResponse


class GoogleProvider(LLMProvider):
    """Google Gemini API provider for LLM comparisons.

    Uses the official Google Gen AI SDK (google-genai) with Structured Outputs
    for reliable JSON responses.
    """

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
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
        """Compare two items using Google Gemini API with Structured Outputs."""
        prompt = self._build_prompt(item_a, item_b, criteria)

        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=ComparisonResponse,
                ),
            )

            raw_response = {
                "text": response.text,
                "candidates": response.candidates,
            }

            # Parse the structured JSON response
            parsed = ComparisonResponse.model_validate_json(response.text)

            return ComparisonResult(
                winner=parsed.winner,
                reasoning=parsed.reasoning,
                raw_response=raw_response
            )

        except ClientError as e:
            return create_error_result(e, "client", "Client error")
        except ServerError as e:
            return create_error_result(e, "server", "Server error")
        except ValueError as e:
            # JSON parsing errors
            return create_error_result(e, "parse", "Parse error")
