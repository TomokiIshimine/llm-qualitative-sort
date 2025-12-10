"""Tests for utility functions."""

import pytest
from dataclasses import dataclass

from llm_qualitative_sort.utils import group_by


class TestGroupBy:
    """Tests for the group_by function."""

    def test_group_by_basic(self):
        """Test basic grouping by a simple key."""
        items = [1, 2, 3, 4, 5, 6]
        result = group_by(items, lambda x: x % 2)

        assert result == {0: [2, 4, 6], 1: [1, 3, 5]}

    def test_group_by_string_key(self):
        """Test grouping by string key."""
        items = ["apple", "banana", "apricot", "blueberry"]
        result = group_by(items, lambda x: x[0])

        assert result == {"a": ["apple", "apricot"], "b": ["banana", "blueberry"]}

    def test_group_by_empty_list(self):
        """Test grouping empty list returns empty dict."""
        result = group_by([], lambda x: x)
        assert result == {}

    def test_group_by_single_item(self):
        """Test grouping single item."""
        result = group_by([42], lambda x: "key")
        assert result == {"key": [42]}

    def test_group_by_all_same_key(self):
        """Test when all items have the same key."""
        items = [1, 2, 3]
        result = group_by(items, lambda x: "same")

        assert result == {"same": [1, 2, 3]}

    def test_group_by_dataclass(self):
        """Test grouping dataclass objects."""
        @dataclass
        class Item:
            name: str
            category: str

        items = [
            Item("apple", "fruit"),
            Item("carrot", "vegetable"),
            Item("banana", "fruit"),
        ]
        result = group_by(items, lambda x: x.category)

        assert len(result["fruit"]) == 2
        assert len(result["vegetable"]) == 1
        assert result["fruit"][0].name == "apple"
        assert result["fruit"][1].name == "banana"

    def test_group_by_preserves_order(self):
        """Test that grouping preserves insertion order within groups."""
        items = [3, 1, 4, 1, 5, 9, 2, 6]
        result = group_by(items, lambda x: x % 3)

        assert result[0] == [3, 9, 6]
        assert result[1] == [1, 4, 1]
        assert result[2] == [5, 2]
