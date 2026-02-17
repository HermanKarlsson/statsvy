"""Test suite for pyproject.toml configuration reader.

Tests verify that PyProjectReader correctly extracts project information
from pyproject.toml files in various formats.
"""

from pathlib import Path

import pytest

from statsvy.config_readers.pyproject_reader import PyProjectReader


@pytest.fixture()
def reader() -> PyProjectReader:
    """Provide a PyProjectReader instance."""
    return PyProjectReader()


class TestPyProjectReaderBasics:
    """Tests for basic PyProjectReader functionality."""

    def test_reads_project_name(self, reader: PyProjectReader, tmp_path: Path) -> None:
        """Test that PyProjectReader extracts project name."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
name = "my-project"
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.name == "my-project"

    def test_reads_standard_dependencies(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader extracts standard dependencies."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
name = "my-project"
dependencies = ["click>=8.0.0", "requests"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        assert result.dependencies.prod_count == 2
        assert result.dependencies.total_count == 2

    def test_reads_optional_dependencies(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader extracts optional dependencies."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
name = "my-project"
dependencies = ["click>=8.0.0"]

[project.optional-dependencies]
extra = ["extra-lib>=1.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        assert result.dependencies.optional_count == 1

    def test_returns_none_dependencies_when_not_found(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader returns None when no dependencies found."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
name = "my-project"
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is None

    def test_returns_none_name_when_not_found(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader returns None name when not found."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click>=8.0.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.name is None


class TestPyProjectReaderErrorHandling:
    """Tests for PyProjectReader error handling."""

    def test_raises_on_file_not_found(self, reader: PyProjectReader) -> None:
        """Test that PyProjectReader raises FileNotFoundError when file missing."""
        with pytest.raises(FileNotFoundError):
            reader.read_project_info(Path("/nonexistent/path/pyproject.toml"))

    def test_raises_on_malformed_toml(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader raises on invalid TOML syntax."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("[project\nname = invalid")
        with pytest.raises(Exception):  # noqa: B017
            reader.read_project_info(pyproject_file)

    def test_handles_non_dict_root(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader handles non-dict root gracefully."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("just_a_string = true")
        result = reader.read_project_info(pyproject_file)
        assert result.name is None
        assert result.dependencies is None

    def test_handles_missing_project_section(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that PyProjectReader handles missing [project] section."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[build-system]
requires = ["setuptools"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.name is None
        assert result.dependencies is None


class TestPyProjectReaderDependencyParsing:
    """Tests for dependency string parsing."""

    def test_parses_simple_dependency_name_only(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test parsing dependency name without version."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        assert len(result.dependencies.dependencies) == 1
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "*"

    def test_parses_dependency_with_version_spec(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test parsing dependency with version specification."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click>=8.0.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == ">=8.0.0"

    def test_parses_dependency_with_extras(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test parsing dependency with extras specification."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click[dev]>=8.0.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == ">=8.0.0"

    def test_parses_dependency_with_environment_marker(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test parsing dependency with environment marker."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click>=8.0.0 ; python_version >= '3.8'"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert ">=8.0.0" in dep.version

    def test_parses_complex_version_spec(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test parsing complex version specifications."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click>=8.0.0,<9.0.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert ">=8.0.0" in dep.version
        assert "<9.0.0" in dep.version


class TestPyProjectReaderDependencyCategories:
    """Tests for dependency category classification."""

    def test_standard_deps_get_prod_category(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that standard dependencies get prod category."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click>=8.0.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.category == "prod"

    def test_optional_deps_get_optional_category(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that optional dependencies get optional category."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]

[project.optional-dependencies]
extra = ["extra-lib>=1.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.category == "optional"

    def test_source_file_is_pyproject_toml(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that source_file is set to pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["click>=8.0.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.source_files == ("pyproject.toml",)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.source_file == "pyproject.toml"


class TestPyProjectReaderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_dependencies_list(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test handling of empty dependencies list."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
name = "my-project"
dependencies = []
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.name == "my-project"
        assert result.dependencies is None

    def test_multiple_optional_dependency_groups(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test handling multiple optional-dependencies groups."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]

[project.optional-dependencies]
dev = ["pytest>=7.0"]
extra = ["extra-lib>=1.0"]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        assert result.dependencies.optional_count == 2

    def test_handles_invalid_dependency_format(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that invalid dependency formats are skipped gracefully."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["valid-package", ""]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count >= 1

    def test_name_converted_to_string(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test that project name is converted to string."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
name = "my-project"
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert isinstance(result.name, str)
        assert result.name == "my-project"

    def test_handles_whitespace_in_dependencies(
        self, reader: PyProjectReader, tmp_path: Path
    ) -> None:
        """Test handling of whitespace in dependency strings."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = ["  click>=8.0.0  "]
"""
        )
        result = reader.read_project_info(pyproject_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1
