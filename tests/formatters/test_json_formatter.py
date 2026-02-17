"""Tests for JsonFormatter."""

import json
from unittest.mock import MagicMock

from statsvy.formatters.json_formatter import JsonFormatter


class TestJsonFormatter:
    """Tests for JsonFormatter."""

    def test_returns_valid_json(self, minimal_metrics: MagicMock) -> None:
        """Output must be parseable as JSON."""
        result = JsonFormatter().format(minimal_metrics)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_basic_fields_present(self, minimal_metrics: MagicMock) -> None:
        """Top-level scalar fields must all be present."""
        parsed = json.loads(JsonFormatter().format(minimal_metrics))
        assert parsed["name"] == "my_project"
        assert parsed["path"] == "/home/user/project"
        assert parsed["timestamp"] == "2024-06-01"
        assert parsed["total_files"] == 42
        assert parsed["total_size"] == "1.5 MB"
        assert parsed["total_lines"] == 1000

    def test_no_language_key_when_empty(self, minimal_metrics: MagicMock) -> None:
        """lines_by_language must be absent when there is no language data."""
        parsed = json.loads(JsonFormatter().format(minimal_metrics))
        assert "lines_by_language" not in parsed

    def test_no_category_key_when_empty(self, minimal_metrics: MagicMock) -> None:
        """lines_by_category must be absent when there is no category data."""
        parsed = json.loads(JsonFormatter().format(minimal_metrics))
        assert "lines_by_category" not in parsed

    def test_language_breakdown(self, full_metrics: MagicMock) -> None:
        """Language entries must contain code/comments/blank sub-fields."""
        parsed = json.loads(JsonFormatter().format(full_metrics))
        py = parsed["lines_by_language"]["Python"]
        assert py["total"] == 300
        assert py["comments"] == 40
        assert py["blank"] == 30
        assert py["code"] == 300 - 40 - 30

    def test_category_section(self, full_metrics: MagicMock) -> None:
        """Category totals must be preserved as-is in the JSON output."""
        parsed = json.loads(JsonFormatter().format(full_metrics))
        cats = parsed["lines_by_category"]
        assert cats["source"] == 350
        assert cats["test"] == 100
        assert cats["unknown"] == 50

    def test_pretty_printed(self, minimal_metrics: MagicMock) -> None:
        """Output must be indented (pretty-printed)."""
        result = JsonFormatter().format(minimal_metrics)
        assert "\n" in result

    def test_zero_total_lines(self, zero_lines_metrics: MagicMock) -> None:
        """Formatter must not raise when total_lines is zero."""
        parsed = json.loads(JsonFormatter().format(zero_lines_metrics))
        assert parsed["lines_by_language"]["Python"]["code"] == 0
