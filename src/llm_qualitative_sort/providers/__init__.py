"""LLM providers for qualitative comparison."""

from __future__ import annotations

from typing import TYPE_CHECKING

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.openai import OpenAIProvider
from llm_qualitative_sort.providers.mock import MockLLMProvider

if TYPE_CHECKING:
    from llm_qualitative_sort.providers.google import GoogleProvider


def get_google_provider() -> type[GoogleProvider]:
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
