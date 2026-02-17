"""Test suite for StoragePresenter.show_history() functionality.

Tests verify displaying the complete scan history with formatting.
"""

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


class TestStorageShowHistory:
    """Tests for StoragePresenter.show_history()."""

    @patch("statsvy.storage.storage_presenter.HistoryFormatter")
    def test_show_history_prints_formatted_data(
        self, mock_formatter: MagicMock, tmp_path: Path
    ) -> None:
        """Test that show_history() reads history.json and prints formatted output."""
        d = _statsvy_dir(tmp_path)
        (d / "history.json").write_text('[{"time": "test_time"}]')

        mock_instance = mock_formatter.return_value
        mock_instance.format.return_value = "Formatted History Content"

        with (
            patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path),
            patch("builtins.print") as mock_print,
        ):
            StoragePresenter.show_history()

        mock_instance.format.assert_called_once()
        mock_print.assert_called_once_with("Formatted History Content")
