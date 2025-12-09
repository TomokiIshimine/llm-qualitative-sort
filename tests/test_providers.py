"""Tests for LLM providers."""

import pytest
from abc import ABC

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.providers.openai import OpenAIProvider
from llm_qualitative_sort.providers.google import GoogleProvider
from llm_qualitative_sort.models import ComparisonResult


class TestLLMProviderBase:
    """Tests for LLMProvider abstract base class."""

    def test_is_abstract_class(self):
        assert issubclass(LLMProvider, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LLMProvider(api_key="test")

    def test_has_compare_method(self):
        assert hasattr(LLMProvider, "compare")


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_inherits_from_llm_provider(self):
        assert issubclass(OpenAIProvider, LLMProvider)

    def test_create_with_api_key(self):
        provider = OpenAIProvider(api_key="sk-test")
        assert provider.api_key == "sk-test"

    def test_create_with_custom_model(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4")
        assert provider.model == "gpt-4"

    def test_create_with_custom_base_url(self):
        provider = OpenAIProvider(
            api_key="sk-test",
            base_url="https://custom.api.com/v1"
        )
        assert provider.base_url == "https://custom.api.com/v1"

    def test_default_base_url(self):
        provider = OpenAIProvider(api_key="sk-test")
        assert provider.base_url == "https://api.openai.com/v1"


class TestGoogleProvider:
    """Tests for GoogleProvider."""

    def test_inherits_from_llm_provider(self):
        assert issubclass(GoogleProvider, LLMProvider)

    def test_create_with_api_key(self):
        provider = GoogleProvider(api_key="AIza-test")
        assert provider.api_key == "AIza-test"

    def test_create_with_custom_model(self):
        provider = GoogleProvider(api_key="AIza-test", model="gemini-pro")
        assert provider.model == "gemini-pro"

    def test_create_with_custom_base_url(self):
        provider = GoogleProvider(
            api_key="AIza-test",
            base_url="https://custom.googleapis.com/v1"
        )
        assert provider.base_url == "https://custom.googleapis.com/v1"

    def test_default_base_url(self):
        provider = GoogleProvider(api_key="AIza-test")
        assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
