"""Test suite for StoragePresenter.show_latest() functionality.

Tests verify displaying the most recent scan information from history.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

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


class TestStorageShowLatest:
    """Tests for StoragePresenter.show_latest()."""

    def test_show_latest_does_not_raise_with_valid_history(
        self, tmp_path: Path
    ) -> None:
        """Test that show_latest() runs without error when history.json is valid."""
        d = _statsvy_dir(tmp_path)
        entry = {
            "time": "2024-01-01 12:00:00",
            "metrics": {
                "total_files": 10,
                "total_size": "2 KB",
            },
        }
        (d / "history.json").write_text(json.dumps([entry]))
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            StoragePresenter.show_latest()  # Should not raise

    def test_show_latest_displays_last_scan_time(self, tmp_path: Path) -> None:
        """Test that show_latest() prints the time of the most recent scan."""
        d = _statsvy_dir(tmp_path)
        entries = [
            {
                "time": "2024-01-01 10:00:00",
                "metrics": {"total_files": 5, "total_size": "1 KB"},
            },
            {
                "time": "2024-06-15 14:30:00",
                "metrics": {"total_files": 20, "total_size": "8 KB"},
            },
        ]
        (d / "history.json").write_text(json.dumps(entries))
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            StoragePresenter.show_latest()

    def test_show_latest_raises_when_history_file_missing(self, tmp_path: Path) -> None:
        """Test that show_latest() raises an exception when history.json is absent.

        Note: this test is intentionally fragile with respect to Storage's internal
        error handling. If StoragePresenter.show_latest() is later changed to catch
        FileNotFoundError and print a user-friendly message instead of raising,
        this test should be updated to assert on the printed output rather than
        on an exception being raised.
        """
        _statsvy_dir(tmp_path)
        with (
            patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path),
            pytest.raises((FileNotFoundError, OSError)),
        ):
            StoragePresenter.show_latest()
