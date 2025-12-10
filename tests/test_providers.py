"""Tests for LLM providers."""

import pytest
from abc import ABC

from llm_qualitative_sort.providers.base import LLMProvider
from llm_qualitative_sort.models import ComparisonResult


class TestLLMProviderBase:
    """Tests for LLMProvider abstract base class."""

    def test_is_abstract_class(self):
        assert issubclass(LLMProvider, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_has_compare_method(self):
        assert hasattr(LLMProvider, "compare")

    def test_has_build_prompt_method(self):
        assert hasattr(LLMProvider, "_build_prompt")
