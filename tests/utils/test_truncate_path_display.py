"""Tests for truncate_path_display utility function."""

from pathlib import Path

from statsvy.utils.formatting import truncate_path_display


class TestTruncatePathDisplay:
    """Tests for path truncation utility."""

    def test_short_path_not_truncated(self) -> None:
        """Short paths should not be truncated."""
        path = Path("/home/user")
        result = truncate_path_display(path)
        assert result == "/home/user"

    def test_long_path_truncated(self) -> None:
        """Long paths should be truncated with ellipsis."""
        path = Path("/home/user/projects/statsvy/src/module")
        result = truncate_path_display(path)
        # Should show first 2 parts and last 1 part with ... in between
        assert "..." in result
        assert result == "/home/user/.../module"

    def test_relative_path_truncated(self) -> None:
        """Relative paths should be truncated without leading slash."""
        path = Path("projects/statsvy/src/core/module")
        result = truncate_path_display(path)
        assert "..." in result
        assert result == "projects/statsvy/.../module"
        assert not result.startswith("/")

    def test_path_exactly_at_threshold(self) -> None:
        """Path with exactly max_parts should not be truncated."""
        path = Path("/home/user/project")
        result = truncate_path_display(path, max_parts=3)
        assert "..." not in result
        assert result == "/home/user/project"

    def test_path_one_over_threshold(self) -> None:
        """Path with one more than max_parts should be truncated."""
        path = Path("/home/user/project/src")
        result = truncate_path_display(path, max_parts=3)
        assert "..." in result
        assert result == "/home/user/.../src"

    def test_string_path_input(self) -> None:
        """Function should accept string paths."""
        path = "/home/user/projects/statsvy/src/module"
        result = truncate_path_display(path)
        assert "..." in result
        assert result == "/home/user/.../module"

    def test_custom_max_parts(self) -> None:
        """Custom max_parts parameter should be respected."""
        path = Path("/home/user/projects/statsvy/src")
        result = truncate_path_display(path, max_parts=2)
        # With max_parts=2, should truncate after 2 parts
        assert "..." in result
        assert result == "/home/user/.../src"

    def test_single_component_path(self) -> None:
        """Single component paths should not be truncated."""
        path = Path("/home")
        result = truncate_path_display(path)
        assert "..." not in result
        assert result == "/home"

    def test_empty_path(self) -> None:
        """Empty paths should return empty or minimal string."""
        path = Path(".")
        result = truncate_path_display(path)
        # Current directory might be "." or empty
        assert "..." not in result
