"""Test suite for the Project module - untrack().

Tests for Project.untrack() functionality.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from statsvy.core.project import Project


def _write_pyproject(path: Path, name: str = "my_app") -> None:
    """Write a minimal pyproject.toml at *path*.

    Args:
        path: Directory in which to create the file.
        name: Project name to embed.
    """
    (path / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
    )


class TestProjectUntrack:
    """Tests for Project.untrack()."""

    def test_untrack_removes_statsvy_directory(self, tmp_path: Path) -> None:
        """Test that untrack() removes the .statsvy directory entirely."""
        statsvy = tmp_path / ".statsvy"
        statsvy.mkdir()
        (statsvy / "project.json").write_text("{}")
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.untrack()
        assert not statsvy.exists()

    def test_untrack_removes_all_files_inside_statsvy(self, tmp_path: Path) -> None:
        """Test that untrack() removes all files inside .statsvy."""
        statsvy = tmp_path / ".statsvy"
        statsvy.mkdir()
        (statsvy / "project.json").write_text("{}")
        (statsvy / "history.json").write_text("[]")
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.untrack()
        assert not statsvy.exists()

    def test_untrack_raises_when_statsvy_dir_absent(self, tmp_path: Path) -> None:
        """Test that untrack() raises an error when .statsvy does not exist."""
        with (
            patch("statsvy.core.project.Path.cwd", return_value=tmp_path),
            pytest.raises((FileNotFoundError, OSError)),
        ):
            Project.untrack()

    def test_track_then_untrack_leaves_no_trace(self, tmp_path: Path) -> None:
        """Test that tracking and then untracking leaves the directory clean."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
            assert (tmp_path / ".statsvy").exists()
            Project.untrack()
        assert not (tmp_path / ".statsvy").exists()
