"""Test suite for project scanner coordinator.

Tests verify that ProjectScanner correctly finds and reads project configuration
files, detecting the appropriate reader for each file type.
"""

import json
from pathlib import Path

import pytest

from statsvy.core.project_scanner import ProjectScanner
from statsvy.data.project_info import ProjectFileInfo


@pytest.fixture()
def sample_pyproject(tmp_path: Path) -> Path:
    """Create a sample pyproject.toml file."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "my-project"
dependencies = ["click>=8.0.0"]
"""
    )
    return tmp_path


@pytest.fixture()
def sample_package_json(tmp_path: Path) -> Path:
    """Create a sample package.json file."""
    package = tmp_path / "package.json"
    data = {
        "name": "my-app",
        "dependencies": {"express": "^4.17.1"},
    }
    package.write_text(json.dumps(data))
    return tmp_path


@pytest.fixture()
def sample_cargo_toml(tmp_path: Path) -> Path:
    """Create a sample Cargo.toml file."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(
        """
[package]
name = "my-project"

[dependencies]
serde = "1.0"
"""
    )
    return tmp_path


@pytest.fixture()
def sample_requirements(tmp_path: Path) -> Path:
    """Create a sample requirements.txt file."""
    reqs = tmp_path / "requirements.txt"
    reqs.write_text("click>=8.0.0\nrequests\n")
    return tmp_path


class TestProjectScannerBasics:
    """Tests for basic ProjectScanner functionality."""

    def test_initializes_with_path(self, tmp_path: Path) -> None:
        """Test that ProjectScanner initializes with a path."""
        scanner = ProjectScanner(tmp_path)
        assert scanner.target_path == tmp_path

    def test_returns_none_when_no_config_files_found(self, tmp_path: Path) -> None:
        """Test that None is returned when no config files found."""
        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()
        assert result is None

    def test_scans_pyproject_toml(self, sample_pyproject: Path) -> None:
        """Test that scanner finds and reads pyproject.toml."""
        scanner = ProjectScanner(sample_pyproject)
        result = scanner.scan()

        assert result is not None
        assert result.name == "my-project"
        assert result.dependencies is not None

    def test_scans_package_json(self, sample_package_json: Path) -> None:
        """Test that scanner finds and reads package.json."""
        scanner = ProjectScanner(sample_package_json)
        result = scanner.scan()

        assert result is not None
        assert result.name == "my-app"

    def test_scans_cargo_toml(self, sample_cargo_toml: Path) -> None:
        """Test that scanner finds and reads Cargo.toml."""
        scanner = ProjectScanner(sample_cargo_toml)
        result = scanner.scan()

        assert result is not None
        assert result.name == "my-project"

    def test_scans_requirements_txt(self, sample_requirements: Path) -> None:
        """Test that scanner finds and reads requirements.txt."""
        scanner = ProjectScanner(sample_requirements)
        result = scanner.scan()

        assert result is not None
        assert result.dependencies is not None
        assert result.dependencies.total_count == 2


class TestProjectScannerMultipleFiles:
    """Tests for handling multiple config files."""

    def test_finds_multiple_config_files(self, tmp_path: Path) -> None:
        """Test that scanner finds multiple config files."""
        # Create multiple config files
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "python-project"')

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("click>=8.0.0\n")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        assert len(result.source_files) == 2

    def test_merges_dependencies_from_multiple_files(self, tmp_path: Path) -> None:
        """Test that dependencies from multiple files are merged."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "my-project"
dependencies = ["click>=8.0.0"]
"""
        )

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests>=2.0\n")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        assert result.dependencies is not None
        # Should have dependencies from both files
        assert result.dependencies.total_count >= 2

    def test_prefers_pyproject_over_others(self, tmp_path: Path) -> None:
        """Test that project name from pyproject.toml is preferred."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "python-project"
"""
        )

        package = tmp_path / "package.json"
        data = {"name": "js-project"}
        package.write_text(json.dumps(data))

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        assert result.name == "python-project"

    def test_detects_conflicts_in_multiple_files(self, tmp_path: Path) -> None:
        """Test that conflicts are detected across files."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "my-project"
dependencies = ["click>=8.0.0"]
"""
        )

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("click>=9.0.0\n")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        assert result.dependencies is not None
        assert len(result.dependencies.conflicts) > 0


class TestProjectScannerErrorHandling:
    """Tests for error handling."""

    def test_raises_on_malformed_pyproject(self, tmp_path: Path) -> None:
        """Test that error is raised for malformed pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project\nname = invalid")

        scanner = ProjectScanner(tmp_path)
        with pytest.raises(ValueError):
            scanner.scan()

    def test_raises_on_malformed_package_json(self, tmp_path: Path) -> None:
        """Test that error is raised for malformed package.json."""
        package = tmp_path / "package.json"
        package.write_text("{invalid json}")

        scanner = ProjectScanner(tmp_path)
        with pytest.raises(ValueError):
            scanner.scan()

    def test_raises_on_malformed_cargo_toml(self, tmp_path: Path) -> None:
        """Test that error is raised for malformed Cargo.toml."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("[package\nname = invalid")

        scanner = ProjectScanner(tmp_path)
        with pytest.raises(ValueError):
            scanner.scan()

    def test_skips_file_if_unreadable(self, tmp_path: Path) -> None:
        """Test that scanner handles unreadable files."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-project"')

        # Make it unreadable
        pyproject.chmod(0o000)
        try:
            scanner = ProjectScanner(tmp_path)
            with pytest.raises(ValueError):
                scanner.scan()
        finally:
            pyproject.chmod(0o644)


class TestProjectScannerConfigFilePriority:
    """Tests for config file search priority."""

    def test_searches_in_expected_order(self, tmp_path: Path) -> None:
        """Test that config files are searched in priority order."""
        # Create all config files
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "python"')

        package = tmp_path / "package.json"
        package.write_text(json.dumps({"name": "javascript"}))

        cargo = tmp_path / "Cargo.toml"
        cargo.write_text('[package]\nname = "rust"')

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        # Should find pyproject.toml first (highest priority)
        assert result is not None
        assert "pyproject.toml" in result.source_files

    def test_merges_all_found_files(self, tmp_path: Path) -> None:
        """Test that all found files are merged into result."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "python"')

        package = tmp_path / "package.json"
        package.write_text(json.dumps({"name": "javascript"}))

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        # Should have both files in sources
        assert len(result.source_files) >= 2


class TestProjectScannerEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_handles_empty_pyproject(self, tmp_path: Path) -> None:
        """Test handling of empty pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        assert result.name is None
        assert result.dependencies is None

    def test_handles_empty_requirements(self, tmp_path: Path) -> None:
        """Test handling of empty requirements.txt."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        # File is found, so ProjectFileInfo is returned even if no dependencies
        assert result is not None
        assert result.dependencies is None

    def test_handles_nonexistent_path(self) -> None:
        """Test that nonexistent paths return None."""
        scanner = ProjectScanner(Path("/nonexistent/path"))
        result = scanner.scan()

        assert result is None

    def test_handles_file_instead_of_directory(self, tmp_path: Path) -> None:
        """Test that passing a file path returns None."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        scanner = ProjectScanner(file_path)
        result = scanner.scan()

        assert result is None

    def test_converts_path_to_path_object(self, tmp_path: Path) -> None:
        """Test that string paths are converted to Path objects."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"')

        scanner = ProjectScanner(str(tmp_path))
        result = scanner.scan()

        assert result is not None


class TestProjectScannerReturnType:
    """Tests for return type and structure."""

    def test_returns_project_file_info_or_none(self, sample_pyproject: Path) -> None:
        """Test that scan returns ProjectFileInfo or None."""
        scanner = ProjectScanner(sample_pyproject)
        result = scanner.scan()

        assert result is None or isinstance(result, ProjectFileInfo)

    def test_result_has_expected_attributes(self, sample_pyproject: Path) -> None:
        """Test that result has expected attributes."""
        scanner = ProjectScanner(sample_pyproject)
        result = scanner.scan()

        assert result is not None
        assert hasattr(result, "name")
        assert hasattr(result, "dependencies")
        assert hasattr(result, "source_files")


class TestProjectScannerIntegration:
    """Integration tests for complete scanning workflows."""

    def test_complete_workflow_single_file(self, sample_pyproject: Path) -> None:
        """Test complete workflow with single config file."""
        scanner = ProjectScanner(sample_pyproject)
        result = scanner.scan()

        assert result is not None
        assert result.name == "my-project"
        assert result.dependencies is not None
        assert len(result.source_files) == 1

    def test_complete_workflow_multiple_files(self, tmp_path: Path) -> None:
        """Test complete workflow with multiple config files."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "my-project"
dependencies = ["click>=8.0.0"]
"""
        )

        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests>=2.0\n")

        scanner = ProjectScanner(tmp_path)
        result = scanner.scan()

        assert result is not None
        assert result.name == "my-project"
        assert result.dependencies is not None
        assert len(result.source_files) == 2
        assert result.dependencies.total_count >= 2
