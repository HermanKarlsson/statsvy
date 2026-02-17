"""Test suite for Cargo.toml configuration reader.

Tests verify that CargoTomlReader correctly extracts project information
from Cargo.toml files in various formats.
"""

from pathlib import Path

import pytest

from statsvy.config_readers.cargo_toml_reader import CargoTomlReader


@pytest.fixture()
def reader() -> CargoTomlReader:
    """Provide a CargoTomlReader instance."""
    return CargoTomlReader()


class TestCargoTomlReaderBasics:
    """Tests for basic CargoTomlReader functionality."""

    def test_reads_project_name(self, reader: CargoTomlReader, tmp_path: Path) -> None:
        """Test that CargoTomlReader extracts project name."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.name == "my-project"

    def test_reads_production_dependencies(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that CargoTomlReader reads production dependencies."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "1.0"
tokio = "1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        assert result.dependencies.prod_count == 2

    def test_reads_dev_dependencies(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that CargoTomlReader reads dev dependencies."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dev-dependencies]
criterion = "0.3"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        assert result.dependencies.dev_count == 1

    def test_returns_none_name_when_not_found(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that None name is returned when not found."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[dependencies]
serde = "1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.name is None

    def test_returns_none_dependencies_when_not_found(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that None dependencies is returned when not found."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is None


class TestCargoTomlReaderErrorHandling:
    """Tests for error handling."""

    def test_raises_on_file_not_found(self, reader: CargoTomlReader) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            reader.read_project_info(Path("/nonexistent/path/Cargo.toml"))

    def test_raises_on_malformed_toml(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that error is raised for invalid TOML syntax."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("[package\nname = invalid")
        with pytest.raises(Exception):  # noqa: B017
            reader.read_project_info(cargo_file)

    def test_handles_non_dict_root(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that non-dict root is handled gracefully."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("just_a_string = true")
        result = reader.read_project_info(cargo_file)
        assert result.name is None
        assert result.dependencies is None


class TestCargoTomlReaderDependencyParsing:
    """Tests for dependency parsing."""

    def test_parses_simple_string_version(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test parsing simple string version specification."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert len(deps) == 1
        assert deps[0].name == "serde"
        assert deps[0].version == "1.0"

    def test_parses_dict_version_spec(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test parsing dict-style version specification."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies.serde]
version = "1.0"
features = ["derive"]
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert deps[0].name == "serde"
        assert deps[0].version == "1.0"

    def test_normalizes_dependency_names_to_lowercase(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that dependency names are normalized to lowercase."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
Serde = "1.0"
Tokio = "1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert all(dep.name.islower() for dep in deps)

    def test_handles_missing_version_with_wildcard(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that missing version is replaced with wildcard."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies.serde]
features = ["derive"]
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert deps[0].version == "*"


class TestCargoTomlReaderDependencyCategories:
    """Tests for dependency category classification."""

    def test_prod_dependencies_get_prod_category(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that production dependencies get prod category."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert deps[0].category == "prod"

    def test_dev_dependencies_get_dev_category(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that dev dependencies get dev category."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dev-dependencies]
criterion = "0.3"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert deps[0].category == "dev"

    def test_source_file_is_cargo_toml(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that source_file is set to Cargo.toml."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.source_files == ("Cargo.toml",)


class TestCargoTomlReaderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_dependencies_section(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test handling of empty dependencies section."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.name == "my-project"
        assert result.dependencies is None

    def test_mixed_prod_and_dev_dependencies(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test handling mixed production and dev dependencies."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "1.0"
tokio = "1.0"

[dev-dependencies]
criterion = "0.3"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        assert result.dependencies.prod_count == 2
        assert result.dependencies.dev_count == 1

    def test_version_with_caret_syntax(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test handling of caret version syntax."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "^1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_version_with_tilde_syntax(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test handling of tilde version syntax."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

[dependencies]
serde = "~1.0"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_many_dependencies(self, reader: CargoTomlReader, tmp_path: Path) -> None:
        """Test handling of many dependencies."""
        cargo_file = tmp_path / "Cargo.toml"
        deps_section = "\n".join(f'package-{i} = "1.0"' for i in range(50))
        cargo_file.write_text(
            f"""
[package]
name = "my-project"

[dependencies]
{deps_section}
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 50

    def test_handles_non_dict_dependency_sections(
        self, reader: CargoTomlReader, tmp_path: Path
    ) -> None:
        """Test that non-dict dependency sections are ignored."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text(
            """
[package]
name = "my-project"

dependencies = "not-a-dict"
"""
        )
        result = reader.read_project_info(cargo_file)
        assert result.dependencies is None
