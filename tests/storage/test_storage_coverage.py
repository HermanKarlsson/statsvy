"""Tests for storage edge cases and error handling."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from statsvy.storage.history_storage import HistoryStorage
from statsvy.storage.project_metadata_storage import ProjectMetadataStorage
from statsvy.storage.storage_presenter import StoragePresenter


class TestStorageErrorHandling:
    """Test error handling and edge cases in storage module."""

    def test_load_history_with_corrupted_json(self) -> None:
        """Test load_history returns empty list on JSONDecodeError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "corrupted.json"

            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(Path, "read_text", return_value="invalid json {"),
            ):
                result = HistoryStorage.load_history(history_file)

            assert result == []

    def test_load_history_with_empty_file(self) -> None:
        """Test load_history with empty file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "empty.json"

            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(Path, "read_text", return_value=""),
            ):
                result = HistoryStorage.load_history(history_file)

            assert result == []

    def test_load_history_with_legacy_dict_format(self) -> None:
        """Test load_history handles legacy single-entry dict format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            legacy_data = {"time": "2024-01-01", "metrics": {}}

            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(Path, "read_text", return_value=json.dumps(legacy_data)),
            ):
                result = HistoryStorage.load_history(history_file)

        # Should convert dict to list
        assert isinstance(result, list)
        assert result == [legacy_data]

    def test_load_history_with_non_list_non_dict(self) -> None:
        """Test load_history with invalid JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"

            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(Path, "read_text", return_value='"just a string"'),
            ):
                result = HistoryStorage.load_history(history_file)

            assert result == []

    def test_update_project_last_scan_with_no_stats_dir(self) -> None:
        """Test update_last_scan when project file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"

            # Should not raise when file doesn't exist
            ProjectMetadataStorage.update_last_scan(project_file, "2024-01-01")

    def test_update_project_last_scan_with_no_project_file(self) -> None:
        """Test update_last_scan when project file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"

            # Should not raise
            ProjectMetadataStorage.update_last_scan(project_file, "2024-01-01")

    def test_update_project_last_scan_with_corrupted_json(self) -> None:
        """Test update_last_scan with corrupted project.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"
            project_file.write_text("invalid json {")

            # Should not raise
            ProjectMetadataStorage.update_last_scan(project_file, "2024-01-01")

    def test_update_project_last_scan_with_non_dict_json(self) -> None:
        """Test update_last_scan with non-dict JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"
            project_file.write_text('"just a string"')

            # Should not raise
            ProjectMetadataStorage.update_last_scan(project_file, "2024-01-01")

    def test_update_project_last_scan_with_valid_project(self) -> None:
        """Test update_last_scan with valid project file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"
            project_data = {"name": "TestProject"}
            project_file.write_text(json.dumps(project_data))

            # Should not raise
            ProjectMetadataStorage.update_last_scan(project_file, "2024-01-01")

            # Verify last_scan was added
            updated_data = json.loads(project_file.read_text())
            assert updated_data["last_scan"] == "2024-01-01"

    def test_load_project_data_with_corrupted_json(self) -> None:
        """Test load_project_data returns None on JSONDecodeError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"
            project_file.write_text("invalid json {")

            result = ProjectMetadataStorage.load_project_data(project_file)

            assert result is None

    def test_load_project_data_with_non_dict_json(self) -> None:
        """Test load_project_data returns None when JSON is not a dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"
            project_file.write_text('"just a string"')

            result = ProjectMetadataStorage.load_project_data(project_file)

            assert result is None

    def test_load_project_data_with_valid_dict(self) -> None:
        """Test load_project_data returns dict for valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = Path(tmpdir) / "project.json"
            project_data = {"name": "TestProject", "path": "/path/to/project"}
            project_file.write_text(json.dumps(project_data))

            result = ProjectMetadataStorage.load_project_data(project_file)

            assert result == project_data

    def test_show_current_with_no_stats_dir(self) -> None:
        """Test show_current when stats directory doesn't exist."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch(
                "statsvy.storage.storage_presenter.Path.cwd", return_value=Path(tmpdir)
            ),
            patch("statsvy.storage.storage_presenter.console") as mock_console,
        ):
            StoragePresenter.show_current()
            # Should print a message
            assert mock_console.print.called

    def test_show_current_with_no_project_file(self) -> None:
        """Test show_current when project file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_dir = Path(tmpdir) / ".statsvy"
            stats_dir.mkdir()

            with (
                patch(
                    "statsvy.storage.storage_presenter.Path.cwd",
                    return_value=Path(tmpdir),
                ),
                patch("statsvy.storage.storage_presenter.console") as mock_console,
            ):
                StoragePresenter.show_current()
                # Should print a message
                assert mock_console.print.called

    def test_show_current_with_corrupted_project_file(self) -> None:
        """Test show_current with corrupted project file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_dir = Path(tmpdir) / ".statsvy"
            stats_dir.mkdir()
            project_file = stats_dir / "project.json"
            project_file.write_text("invalid json {")

            with (
                patch(
                    "statsvy.storage.storage_presenter.Path.cwd",
                    return_value=Path(tmpdir),
                ),
                patch("statsvy.storage.storage_presenter.console") as mock_console,
            ):
                StoragePresenter.show_current()
                # Should print error message
                assert mock_console.print.called
