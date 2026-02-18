"""Tests for git metadata stored in project.json during tracking."""

import json
from pathlib import Path
from unittest.mock import patch

from statsvy.core.project import Project


class TestTrackGitInfo:
    """Tests for git metadata stored in project.json during tracking."""

    @staticmethod
    def _write_pyproject(path: Path, name: str = "my_app") -> None:
        """Write a minimal pyproject.toml at *path*.

        Args:
            path: Directory in which to create the file.
            name: Project name to embed.
        """
        (path / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
        )

    def test_track_writes_git_info_for_non_repo(self, tmp_path: Path) -> None:
        """Track should include git info even for non-repositories."""
        self._write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()

        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert "git_info" in data
        assert data["git_info"]["is_git_repo"] is False
        assert data["git_info"]["remote_url"] is None
        assert data["git_info"]["current_branch"] is None
        assert data["git_info"]["commit_count"] is None
