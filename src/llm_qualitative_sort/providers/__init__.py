"""LLM providers for qualitative comparison."""

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.openai import OpenAIProvider
from llm_qualitative_sort.providers.mock import MockLLMProvider


def get_google_provider():
    """Lazily import GoogleProvider to avoid cryptography dependency issues.

    Returns:
        GoogleProvider class

    Raises:
        ImportError: If google-genai or its dependencies are not available
    """
    from llm_qualitative_sort.providers.google import GoogleProvider
    return GoogleProvider


__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "get_google_provider",
    "MockLLMProvider",
]
