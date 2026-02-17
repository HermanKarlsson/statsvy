"""Test suite for StoragePresenter.show_current() functionality.

Tests verify displaying tracked project details and latest scan metadata.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from statsvy.storage.storage_presenter import StoragePresenter


def _statsvy_dir(tmp_path: Path) -> Path:
    """Create and return a .statsvy directory inside *tmp_path*.

    Args:
        tmp_path: Root temporary directory.

    Returns:
        Path to the created .statsvy subdirectory.
    """
    d = tmp_path / ".statsvy"
    d.mkdir()
    return d


class TestStorageShowCurrent:
    """Tests for StoragePresenter.show_current()."""

    @patch("statsvy.storage.storage_presenter.SummaryFormatter.format")
    def test_show_current_calls_summary_formatter(
        self, mock_format: MagicMock, tmp_path: Path
    ) -> None:
        """Test that show_current() delegates to SummaryFormatter.format()."""
        d = _statsvy_dir(tmp_path)
        (d / "project.json").write_text(
            json.dumps(
                {
                    "name": "statsvy",
                    "path": str(tmp_path),
                    "date_added": "2026-02-14",
                    "last_scan": "2026-02-14 10:00:00",
                }
            )
        )
        (d / "history.json").write_text(
            json.dumps(
                [
                    {
                        "time": "2026-02-14 10:00:00",
                        "metrics": {
                            "total_files": 123,
                            "total_size": "10 MB (10240 KB)",
                            "total_lines": 4567,
                        },
                    }
                ]
            )
        )

        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            StoragePresenter.show_current()

        mock_format.assert_called_once()
        call_kwargs = mock_format.call_args[1]
        assert call_kwargs["project_data"]["name"] == "statsvy"
        assert len(call_kwargs["history_data"]) == 1
        assert call_kwargs["last_scan"] == "2026-02-14 10:00:00"

    def test_show_current_warns_when_statsvy_directory_missing(
        self, tmp_path: Path
    ) -> None:
        """Test that show_current() warns if .statsvy directory does not exist."""
        with (
            patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path),
            patch("statsvy.storage.storage_presenter.console.print") as mock_print,
        ):
            StoragePresenter.show_current()

        _assert_print_contains(mock_print, "No tracked project found")

    def test_show_current_warns_when_project_metadata_missing(
        self, tmp_path: Path
    ) -> None:
        """Test that show_current() warns if project.json is missing."""
        _statsvy_dir(tmp_path)
        with (
            patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path),
            patch("statsvy.storage.storage_presenter.console.print") as mock_print,
        ):
            StoragePresenter.show_current()

        _assert_print_contains(mock_print, "No project metadata found")

    @patch("statsvy.storage.storage_presenter.SummaryFormatter.format")
    def test_show_current_uses_history_time_when_last_scan_is_missing(
        self, mock_format: MagicMock, tmp_path: Path
    ) -> None:
        """Test that show_current() falls back to latest history time."""
        d = _statsvy_dir(tmp_path)
        (d / "project.json").write_text(
            json.dumps(
                {
                    "name": "statsvy",
                    "path": str(tmp_path),
                    "date_added": "2026-02-14",
                    "last_scan": None,
                }
            )
        )
        (d / "history.json").write_text(
            json.dumps(
                [
                    {
                        "time": "2026-02-14 11:30:00",
                        "metrics": {
                            "total_files": 7,
                            "total_size": "1 MB (1024 KB)",
                            "total_lines": 200,
                        },
                    }
                ]
            )
        )

        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            StoragePresenter.show_current()

        call_kwargs = mock_format.call_args[1]
        assert call_kwargs["last_scan"] == "2026-02-14 11:30:00"


def _assert_print_contains(mock_print: MagicMock, expected: str) -> None:
    """Assert any captured print call contains the expected text.

    Args:
        mock_print: Mocked ``console.print`` method.
        expected: Substring expected in at least one print call.
    """
    printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list)
    assert expected in printed
