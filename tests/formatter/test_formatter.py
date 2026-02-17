"""Tests for the Formatter coordinator."""

import json
from unittest.mock import MagicMock

import pytest

from statsvy.core.formatter import Formatter


class TestFormatter:
    """Tests for the Formatter coordinator."""

    def test_default_format_type(self, minimal_metrics: MagicMock) -> None:
        """Calling format() without a type should not raise."""
        try:
            Formatter.format(minimal_metrics)
        except ValueError:
            pytest.fail("Formatter raised ValueError for default format_type")

    def test_none_format_type(self, minimal_metrics: MagicMock) -> None:
        """Passing None as format_type should be equivalent to 'cli'."""
        try:
            Formatter.format(minimal_metrics, format_type=None)
        except ValueError:
            pytest.fail("Formatter raised ValueError for None format_type")

    def test_json_format_type(self, minimal_metrics: MagicMock) -> None:
        """format_type='json' must return valid JSON."""
        result = Formatter.format(minimal_metrics, format_type="json")
        parsed = json.loads(result)
        assert parsed["name"] == "my_project"

    def test_markdown_format_type(self, minimal_metrics: MagicMock) -> None:
        """format_type='markdown' must return a Markdown string."""
        result = Formatter.format(minimal_metrics, format_type="markdown")
        assert "# Scan:" in result

    def test_unknown_format_type_raises(self, minimal_metrics: MagicMock) -> None:
        """An unknown format_type must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown format type: xml"):
            Formatter.format(minimal_metrics, format_type="xml")
