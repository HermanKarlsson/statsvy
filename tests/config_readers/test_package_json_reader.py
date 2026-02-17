"""Test suite for package.json configuration reader.

Tests verify that PackageJsonReader correctly extracts project information
from package.json files in various formats.
"""

import json
from pathlib import Path

import pytest

from statsvy.config_readers.package_json_reader import PackageJsonReader


@pytest.fixture()
def reader() -> PackageJsonReader:
    """Provide a PackageJsonReader instance."""
    return PackageJsonReader()


class TestPackageJsonReaderBasics:
    """Tests for basic PackageJsonReader functionality."""

    def test_reads_project_name(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that PackageJsonReader extracts project name."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"name": "my-app"}))
        result = reader.read_project_info(package_file)
        assert result.name == "my-app"

    def test_reads_production_dependencies(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that PackageJsonReader reads production dependencies."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"express": "^4.17.1", "lodash": "^4.17.21"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.prod_count == 2

    def test_reads_dev_dependencies(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that PackageJsonReader reads dev dependencies."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "devDependencies": {"jest": "^27.0.0", "eslint": "^8.0.0"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.dev_count == 2

    def test_reads_optional_dependencies(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that PackageJsonReader reads optional dependencies."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "optionalDependencies": {"optional-lib": "^1.0.0"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.optional_count == 1

    def test_returns_none_dependencies_when_not_found(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that None is returned when no dependencies found."""
        package_file = tmp_path / "package.json"
        data = {"name": "my-app"}
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is None

    def test_returns_none_name_when_not_found(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that None name is returned when name not found."""
        package_file = tmp_path / "package.json"
        data = {"dependencies": {"express": "^4.17.1"}}
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.name is None


class TestPackageJsonReaderErrorHandling:
    """Tests for error handling."""

    def test_raises_on_file_not_found(self, reader: PackageJsonReader) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            reader.read_project_info(Path("/nonexistent/path/package.json"))

    def test_raises_on_invalid_json(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that JSON decode error is raised for invalid JSON."""
        package_file = tmp_path / "package.json"
        package_file.write_text("{invalid json}")
        with pytest.raises(json.JSONDecodeError):
            reader.read_project_info(package_file)

    def test_handles_non_dict_root(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that non-dict root is handled gracefully."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(["array", "data"]))
        result = reader.read_project_info(package_file)
        assert result.name is None
        assert result.dependencies is None


class TestPackageJsonReaderDependencyParsing:
    """Tests for dependency parsing."""

    def test_parses_production_dependencies_correctly(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that production dependencies are parsed correctly."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"express": "^4.17.1"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert len(deps) == 1
        assert deps[0].name == "express"
        assert deps[0].version == "^4.17.1"
        assert deps[0].category == "prod"

    def test_parses_dev_dependencies_correctly(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that dev dependencies are parsed correctly."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "devDependencies": {"jest": "^27.0.0"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert deps[0].name == "jest"
        assert deps[0].category == "dev"

    def test_normalizes_dependency_names_to_lowercase(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that dependency names are normalized to lowercase."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"Express": "^4.17.1", "LODASH": "^4.17.21"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert all(dep.name.islower() for dep in deps)


class TestPackageJsonReaderDependencyCategories:
    """Tests for proper categorization of dependencies."""

    def test_counts_all_dep_types_correctly(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that all dependency types are counted correctly."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"express": "^4.17.1", "lodash": "^4.17.21"},
            "devDependencies": {"jest": "^27.0.0"},
            "optionalDependencies": {"optional": "^1.0.0"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.prod_count == 2
        assert result.dependencies.dev_count == 1
        assert result.dependencies.optional_count == 1
        assert result.dependencies.total_count == 4

    def test_source_file_is_package_json(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that source_file is set to package.json."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"express": "^4.17.1"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.source_files == ("package.json",)


class TestPackageJsonReaderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_dependencies_object(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test handling of empty dependencies object."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is None

    def test_single_dependency(self, reader: PackageJsonReader, tmp_path: Path) -> None:
        """Test handling of single dependency."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"express": "^4.17.1"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_many_dependencies(self, reader: PackageJsonReader, tmp_path: Path) -> None:
        """Test handling of many dependencies."""
        package_file = tmp_path / "package.json"
        deps = {f"package-{i}": f"^{i}.0.0" for i in range(100)}
        data = {"name": "my-app", "dependencies": deps}
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 100

    def test_version_with_special_characters(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test handling of version specs with special characters."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {
                "express": "^4.17.1",
                "react": ">=17.0.0 <18.0.0",
                "vue": "~3.2.0",
            },
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 3

    def test_name_as_non_string_converted(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that non-string names are converted to string."""
        package_file = tmp_path / "package.json"
        data = {
            "name": 123,
            "dependencies": {"express": "^4.17.1"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert isinstance(result.name, str)

    def test_ignores_non_dict_dependency_sections(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that non-dict dependency sections are ignored."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": "not-a-dict",
            "devDependencies": {"jest": "^27.0.0"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        assert result.dependencies.dev_count == 1
        assert result.dependencies.prod_count == 0

    def test_handles_duplicate_sources_correctly(
        self, reader: PackageJsonReader, tmp_path: Path
    ) -> None:
        """Test that package.json is only listed once in sources."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "my-app",
            "dependencies": {"express": "^4.17.1"},
            "devDependencies": {"jest": "^27.0.0"},
        }
        package_file.write_text(json.dumps(data))
        result = reader.read_project_info(package_file)
        assert result.dependencies is not None
        # Should only appear once in sources
        sources_list = list(result.dependencies.sources)
        assert sources_list.count("package.json") == 1
