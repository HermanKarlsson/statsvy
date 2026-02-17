"""Test suite for Storage.save() functionality.

Tests cover saving metrics to history, handling existing history files,
and graceful error handling.
"""

import datetime
import json
from pathlib import Path
from typing import TypedDict, Unpack
from unittest.mock import patch

from statsvy.data.metrics import Metrics
from statsvy.storage.storage import Storage


class MetricsKwargs(TypedDict, total=False):
    """To please ty."""

    name: str
    path: Path
    timestamp: datetime.datetime
    total_files: int
    total_size_bytes: int
    total_size_kb: int
    total_size_mb: int
    total_lines: int
    lines_by_lang: dict[str, int]
    comment_lines: int
    blank_lines: int
    comment_lines_by_lang: dict[str, int]
    blank_lines_by_lang: dict[str, int]
    lines_by_category: dict[str, int]


def _make_metrics(**kwargs: Unpack[MetricsKwargs]) -> Metrics:
    """Return a minimal Metrics object, allowing field overrides via kwargs.

    Args:
        **kwargs: Any subset of Metrics fields to override.

    Returns:
        A Metrics instance suitable for use in tests.
    """
    return Metrics(
        name=kwargs.get("name", "test_project"),
        path=kwargs.get("path", Path("/tmp/project")),  # noqa: S108
        timestamp=kwargs.get("timestamp", datetime.datetime(2024, 1, 1, 12, 0, 0)),
        total_files=kwargs.get("total_files", 5),
        total_size_bytes=kwargs.get("total_size_bytes", 2048),
        total_size_kb=kwargs.get("total_size_kb", 2),
        total_size_mb=kwargs.get("total_size_mb", 0),
        total_lines=kwargs.get("total_lines", 100),
        lines_by_lang=kwargs.get("lines_by_lang", {"Python": 80, "JavaScript": 20}),
        comment_lines=kwargs.get("comment_lines", 10),
        blank_lines=kwargs.get("blank_lines", 15),
        comment_lines_by_lang=kwargs.get("comment_lines_by_lang", {"Python": 10}),
        blank_lines_by_lang=kwargs.get("blank_lines_by_lang", {"Python": 15}),
        lines_by_category=kwargs.get("lines_by_category", {"code": 100}),
    )


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


class TestStorageSave:
    """Tests for Storage.save()."""

    def test_save_creates_history_file_when_absent(self, tmp_path: Path) -> None:
        """Test that save() creates history.json when a tracked project exists.

        Storage now requires a valid `.statsvy/project.json` for the project to
        be considered "tracked". This test writes a minimal `project.json`
        and verifies history is created for that tracked project.
        """
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

        metrics = _make_metrics(path=tmp_path)
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)
        assert (tmp_path / ".statsvy" / "history.json").exists()

    def test_save_skips_when_project_json_missing(self, tmp_path: Path) -> None:
        """If `.statsvy` exists but `project.json` is absent, do not save."""
        _statsvy_dir(tmp_path)
        metrics = _make_metrics()
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)

        assert not (tmp_path / ".statsvy" / "history.json").exists()

    def test_save_writes_valid_json(self, tmp_path: Path) -> None:
        """Test that save() writes well-formed JSON to history.json."""
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
        metrics = _make_metrics(path=tmp_path)
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)
        content = (tmp_path / ".statsvy" / "history.json").read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, list)

    def test_save_records_correct_total_files(self, tmp_path: Path) -> None:
        """Test that the saved entry contains the correct total_files value."""
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
        metrics = _make_metrics(path=tmp_path, total_files=42)
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)
        data = json.loads((tmp_path / ".statsvy" / "history.json").read_text())
        assert data[0]["metrics"]["total_files"] == 42

    def test_save_appends_to_existing_history(self, tmp_path: Path) -> None:
        """Test that successive saves append entries rather than overwriting."""
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
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(_make_metrics(path=tmp_path, total_files=1))
            Storage.save(_make_metrics(path=tmp_path, total_files=2))
        data = json.loads((tmp_path / ".statsvy" / "history.json").read_text())
        assert len(data) == 2
        assert data[0]["metrics"]["total_files"] == 1
        assert data[1]["metrics"]["total_files"] == 2

    def test_save_does_nothing_when_statsvy_dir_absent(self, tmp_path: Path) -> None:
        """Test that save() silently does nothing when .statsvy dir does not exist.

        Note: tmp_path itself always exists — it is the .statsvy *subdirectory*
        that is intentionally absent here.
        """
        metrics = _make_metrics()
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)
        assert not (tmp_path / ".statsvy" / "history.json").exists()

    def test_save_recovers_from_corrupt_history_file(self, tmp_path: Path) -> None:
        """Test that save() overwrites corrupted history.json rather than crashing."""
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
        (d / "history.json").write_text("this is not json {{{{")
        metrics = _make_metrics(path=tmp_path)
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)
        data = json.loads((tmp_path / ".statsvy" / "history.json").read_text())
        assert len(data) == 1

    def test_save_handles_history_as_dict_by_wrapping_in_list(
        self, tmp_path: Path
    ) -> None:
        """Test that save() handles a history.json that contains a bare dict."""
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
        (d / "history.json").write_text(json.dumps({"time": "x", "metrics": {}}))
        metrics = _make_metrics(path=tmp_path)
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)
        data = json.loads((tmp_path / ".statsvy" / "history.json").read_text())
        assert isinstance(data, list)
        assert len(data) == 2  # legacy entry + new entry

    def test_save_entry_has_time_field(self, tmp_path: Path) -> None:
        """Test that each saved entry contains a 'time' timestamp string."""
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
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(_make_metrics(path=tmp_path))
        data = json.loads((tmp_path / ".statsvy" / "history.json").read_text())
        assert "time" in data[0]
        assert isinstance(data[0]["time"], str)

    def test_save_entry_has_metrics_field(self, tmp_path: Path) -> None:
        """Test that each saved entry contains a 'metrics' object."""
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
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(_make_metrics(path=tmp_path))
        data = json.loads((tmp_path / ".statsvy" / "history.json").read_text())
        assert "metrics" in data[0]
        assert isinstance(data[0]["metrics"], dict)

    def test_save_updates_project_json_last_scan(self, tmp_path: Path) -> None:
        """Test that save() updates last_scan in project.json when it exists."""
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

        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(_make_metrics(path=tmp_path))

        project_data = json.loads((d / "project.json").read_text())
        assert isinstance(project_data["last_scan"], str)

    def test_save_skips_when_scanning_subdirectory_of_tracked_project(
        self, tmp_path: Path
    ) -> None:
        """Test save() don't when metrics.path is a subdirectory of tracked project."""
        # Arrange: tracked project is tmp_path, but metrics.path points to a
        # subdirectory (tmp_path / "src").
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
        subdir = tmp_path / "src"
        subdir.mkdir()

        metrics = _make_metrics(path=subdir)

        # Act: run save() while CWD is the tracked project root.
        with patch("statsvy.storage.storage_presenter.Path.cwd", return_value=tmp_path):
            Storage.save(metrics)

        # Assert: no history file was created because metrics.path != tracked path
        assert not (tmp_path / ".statsvy" / "history.json").exists()
