"""Test suite for the Project module - track() error cases.

Tests for error handling when no config file is found.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from statsvy.core.project import Project


class TestProjectTrackErrorCases:
    """Tests for error handling when no config file is found."""

    def test_track_raises_when_no_config_file_exists(self, tmp_path: Path) -> None:
        """Test that track() raises StopIteration (or similar) when no config found."""
        with (
            patch("statsvy.core.project.Path.cwd", return_value=tmp_path),
            pytest.raises((StopIteration, FileNotFoundError)),
        ):
            Project.track()
            pass
