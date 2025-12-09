"""Gemini connection test."""

import os
import pytest


@pytest.mark.asyncio
async def test_gemini_connection():
    """Test that we can connect to Gemini API and get a response."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set")

    # Use lazy import to avoid cryptography issues
    try:
        from llm_qualitative_sort.providers.google import GoogleProvider
    except ImportError as e:
        pytest.skip(f"GoogleProvider not available: {e}")

    provider = GoogleProvider(api_key=api_key)

    result = await provider.compare(
        item_a="Python is a versatile programming language.",
        item_b="JavaScript is widely used for web development.",
        criteria="Which is better for beginners learning to code?"
    )

    # Check that we got a valid response
    assert result.winner in ("A", "B"), f"Invalid winner: {result.winner}, reasoning: {result.reasoning}"
    assert result.reasoning, "No reasoning provided"
    print(f"Winner: {result.winner}")
    print(f"Reasoning: {result.reasoning}")
