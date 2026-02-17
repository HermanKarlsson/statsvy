"""Test suite for the Project module - track() happy paths.

Tests cover successful tracking of projects via pyproject.toml and package.json.
"""

import json
from pathlib import Path
from unittest.mock import patch

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


def _write_package_json(path: Path, name: str = "my_app") -> None:
    """Write a minimal package.json at *path*.

    Args:
        path: Directory in which to create the file.
        name: Project name to embed.
    """
    (path / "package.json").write_text(json.dumps({"name": name, "version": "1.0.0"}))


class TestProjectTrackHappyPaths:
    """Tests for successful tracking using each supported config file format."""

    def test_track_creates_statsvy_directory(self, tmp_path: Path) -> None:
        """Test that track() creates the .statsvy directory."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        assert (tmp_path / ".statsvy").is_dir()

    def test_track_creates_project_json(self, tmp_path: Path) -> None:
        """Test that track() writes a project.json file inside .statsvy."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        assert (tmp_path / ".statsvy" / "project.json").exists()

    def test_track_project_json_is_valid_json(self, tmp_path: Path) -> None:
        """Test that project.json written by track() is valid JSON."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        content = (tmp_path / ".statsvy" / "project.json").read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_track_stores_project_name_from_pyproject_toml(
        self, tmp_path: Path
    ) -> None:
        """Test that project name is read correctly from pyproject.toml."""
        _write_pyproject(tmp_path, name="awesome_lib")
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert data["name"] == "awesome_lib"

    def test_track_stores_project_name_from_fallback_toml_format(
        self, tmp_path: Path
    ) -> None:
        """Test project name is read correctly when TOML uses literal key."""
        (tmp_path / "pyproject.toml").write_text(
            '["[project]"]\nname = "fallback_app"\n'
        )
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert data["name"] == "fallback_app"

    def test_track_stores_path_in_project_json(self, tmp_path: Path) -> None:
        """Test that the cwd path is stored in project.json."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert data["path"] == str(tmp_path)

    def test_track_stores_date_added_in_project_json(self, tmp_path: Path) -> None:
        """Test that a date_added field is present in project.json."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert "date_added" in data
        assert isinstance(data["date_added"], str)

    def test_track_reads_name_from_package_json(self, tmp_path: Path) -> None:
        """Test that project name is read correctly from package.json."""
        _write_package_json(tmp_path, name="frontend_app")
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert data["name"] == "frontend_app"

    def test_track_overwrites_existing_project_json(self, tmp_path: Path) -> None:
        """Test that calling track() twice overwrites the previous project.json."""
        _write_pyproject(tmp_path, name="v1")
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "v2"\n')
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        data = json.loads((tmp_path / ".statsvy" / "project.json").read_text())
        assert data["name"] == "v2"

    def test_track_creates_parents_of_statsvy_dir(self, tmp_path: Path) -> None:
        """Test that track() creates the .statsvy directory including parents."""
        _write_pyproject(tmp_path)
        with patch("statsvy.core.project.Path.cwd", return_value=tmp_path):
            Project.track()
        assert (tmp_path / ".statsvy" / "project.json").is_file()
