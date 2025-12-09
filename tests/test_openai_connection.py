"""OpenAI connection test."""

import os
import pytest
from llm_qualitative_sort.providers.openai import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_connection():
    """Test that we can connect to OpenAI API and get a response."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    provider = OpenAIProvider(api_key=api_key)

    result = await provider.compare(
        item_a="Python is a versatile programming language.",
        item_b="JavaScript is widely used for web development.",
        criteria="Which is better for beginners learning to code?"
    )

    # Skip if there are environment-related connection issues
    if result.winner is None and result.reasoning:
        env_errors = [
            "CERTIFICATE_VERIFY_FAILED",
            "SSL",
            "TLS",
            "connection failure",
            "connect error",
        ]
        if any(err in result.reasoning for err in env_errors):
            pytest.skip(f"Network/SSL environment issue: {result.reasoning}")

    # Check that we got a valid response
    assert result.winner in ("A", "B"), f"Invalid winner: {result.winner}, reasoning: {result.reasoning}"
    assert result.reasoning, "No reasoning provided"
    print(f"Winner: {result.winner}")
    print(f"Reasoning: {result.reasoning}")
