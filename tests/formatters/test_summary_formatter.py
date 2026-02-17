"""Test suite for SummaryFormatter functionality.

Tests verify displaying project summaries with and without metrics.
"""

from unittest.mock import patch

from statsvy.formatters.summary_formatter import SummaryFormatter


class TestSummaryFormatter:
    """Tests for SummaryFormatter.format()."""

    def test_format_prints_project_metadata(self) -> None:
        """Test that format() prints project name and metadata."""
        with patch("statsvy.formatters.summary_formatter.console.print") as mock_print:
            SummaryFormatter.format(
                project_data={
                    "name": "statsvy",
                    "path": "/home/user/statsvy",
                    "date_added": "2026-02-14",
                },
                history_data=[],
                last_scan=None,
                latest_metrics={},
            )

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Current Project" in printed
        assert "Name: statsvy" in printed
        assert "Path: /home/user/statsvy" in printed
        assert "Date added: 2026-02-14" in printed

    def test_format_prints_last_scan_time(self) -> None:
        """Test that format() displays the last scan timestamp."""
        with patch("statsvy.formatters.summary_formatter.console.print") as mock_print:
            SummaryFormatter.format(
                project_data={
                    "name": "test",
                    "path": "/test",
                    "date_added": "2026-01-01",
                },
                history_data=[{"time": "2026-02-14 10:00:00"}],
                last_scan="2026-02-14 10:00:00",
                latest_metrics={},
            )

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Last scan: 2026-02-14 10:00:00" in printed

    def test_format_shows_total_scans_count(self) -> None:
        """Test that format() displays the total number of scans."""
        with patch("statsvy.formatters.summary_formatter.console.print") as mock_print:
            SummaryFormatter.format(
                project_data={
                    "name": "test",
                    "path": "/test",
                    "date_added": "2026-01-01",
                },
                history_data=[
                    {"time": "2026-02-10 10:00:00"},
                    {"time": "2026-02-12 10:00:00"},
                    {"time": "2026-02-14 10:00:00"},
                ],
                last_scan="2026-02-14 10:00:00",
                latest_metrics={},
            )

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Total scans: 3" in printed

    def test_format_prints_latest_metrics(self) -> None:
        """Test that format() displays latest scan metrics when available."""
        with patch("statsvy.formatters.summary_formatter.console.print") as mock_print:
            SummaryFormatter.format(
                project_data={
                    "name": "test",
                    "path": "/test",
                    "date_added": "2026-01-01",
                },
                history_data=[],
                last_scan="2026-02-14 10:00:00",
                latest_metrics={
                    "total_files": 150,
                    "total_size": "12 MB (12288 KB)",
                    "total_lines": 5000,
                },
            )

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Latest total files: 150" in printed
        assert "Latest total size: 12 MB (12288 KB)" in printed
        assert "Latest total lines: 5000" in printed

    def test_format_handles_missing_metrics_gracefully(self) -> None:
        """Test that format() handles missing metric values."""
        with patch("statsvy.formatters.summary_formatter.console.print") as mock_print:
            SummaryFormatter.format(
                project_data={
                    "name": "test",
                    "path": "/test",
                    "date_added": "2026-01-01",
                },
                history_data=[],
                last_scan=None,
                latest_metrics={},
            )

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Last scan: -" in printed
        assert "Latest total" not in printed

    def test_format_uses_dashes_for_missing_fields(self) -> None:
        """Test that format() displays dashes for undefined project fields."""
        with patch("statsvy.formatters.summary_formatter.console.print") as mock_print:
            SummaryFormatter.format(
                project_data={},
                history_data=[],
                last_scan=None,
                latest_metrics={},
            )

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
        assert "Name: -" in printed
        assert "Path: -" in printed
