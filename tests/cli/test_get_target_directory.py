"""Test suite for PathResolver.get_target_directory.

Tests cover directory resolution logic for the scan command, including
reading from project.json and falling back to current working directory.
"""

import json
from pathlib import Path
from unittest.mock import patch

from statsvy.utils.path_resolver import PathResolver

_CLI_MODULE = "statsvy.utils.path_resolver"


class TestGetTargetDirectory:
    """Unit tests for the PathResolver.get_target_directory helper."""

    def test_returns_provided_dir_as_path(self, tmp_path: Path) -> None:
        """Test that a provided directory string is returned as a Path."""
        result: Path = PathResolver.get_target_directory(str(tmp_path))
        assert result == tmp_path

    def test_provided_dir_does_not_read_project_json(self, tmp_path: Path) -> None:
        """Test that project.json is not consulted when a directory is provided."""
        statsvy = tmp_path / ".statsvy"
        statsvy.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        (statsvy / "project.json").write_text(json.dumps({"path": str(other)}))

        result: Path = PathResolver.get_target_directory(str(tmp_path))

        assert result == tmp_path

    def test_returns_cwd_path_type(self, tmp_path: Path) -> None:
        """Test that the fallback return value is a Path instance."""
        with patch(f"{_CLI_MODULE}.Path.cwd", return_value=tmp_path):
            result: Path = PathResolver.get_target_directory(None)

        assert isinstance(result, Path)
