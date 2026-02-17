"""Test suite for config readers factory and initialization.

Tests verify that the config readers module correctly identifies and provides
the appropriate reader for each configuration file type.
"""

from pathlib import Path

from statsvy.config_readers.cargo_toml_reader import CargoTomlReader
from statsvy.config_readers.config_readers_factory import get_reader_for_file
from statsvy.config_readers.package_json_reader import PackageJsonReader
from statsvy.config_readers.pyproject_reader import PyProjectReader
from statsvy.config_readers.requirements_txt_reader import RequirementsTxtReader


class TestConfigReadersFactory:
    """Tests for get_reader_for_file factory function."""

    def test_returns_pyproject_reader_for_pyproject_toml(self, tmp_path: Path) -> None:
        """Test that PyProjectReader is returned for pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        reader = get_reader_for_file(pyproject)

        assert reader is not None
        assert isinstance(reader, PyProjectReader)

    def test_returns_package_json_reader_for_package_json(self, tmp_path: Path) -> None:
        """Test that PackageJsonReader is returned for package.json."""
        package = tmp_path / "package.json"
        package.write_text("{}")

        reader = get_reader_for_file(package)

        assert reader is not None
        assert isinstance(reader, PackageJsonReader)

    def test_returns_cargo_toml_reader_for_cargo_toml(self, tmp_path: Path) -> None:
        """Test that CargoTomlReader is returned for Cargo.toml."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("")

        reader = get_reader_for_file(cargo)

        assert reader is not None
        assert isinstance(reader, CargoTomlReader)

    def test_returns_requirements_txt_reader_for_requirements_txt(
        self, tmp_path: Path
    ) -> None:
        """Test that RequirementsTxtReader is returned for requirements.txt."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("")

        reader = get_reader_for_file(requirements)

        assert reader is not None
        assert isinstance(reader, RequirementsTxtReader)

    def test_returns_none_for_unknown_file(self, tmp_path: Path) -> None:
        """Test that None is returned for unknown file types."""
        unknown = tmp_path / "unknown.txt"
        unknown.write_text("")

        reader = get_reader_for_file(unknown)

        assert reader is None

    def test_handles_path_object(self, tmp_path: Path) -> None:
        """Test that Path objects are handled correctly."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        reader = get_reader_for_file(pyproject)

        assert reader is not None

    def test_handles_string_path(self, tmp_path: Path) -> None:
        """Test that string paths are handled correctly."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        reader = get_reader_for_file(Path(str(pyproject)))

        assert reader is not None


class TestConfigReadersIntegration:
    """Integration tests for multiple readers."""

    def test_all_supported_files_return_readers(self, tmp_path: Path) -> None:
        """Test that all supported file types return readers."""
        supported_files = {
            "pyproject.toml": PyProjectReader,
            "package.json": PackageJsonReader,
            "Cargo.toml": CargoTomlReader,
            "requirements.txt": RequirementsTxtReader,
        }

        for filename, expected_reader_type in supported_files.items():
            file_path = tmp_path / filename
            file_path.write_text("" if filename != "package.json" else "{}")

            reader = get_reader_for_file(file_path)

            assert reader is not None
            assert isinstance(reader, expected_reader_type)

    def test_readers_implement_protocol(self, tmp_path: Path) -> None:
        """Test that readers implement the ProjectConfigReader protocol."""
        supported_files = [
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "requirements.txt",
        ]

        for filename in supported_files:
            file_path = tmp_path / filename
            file_path.write_text("" if filename != "package.json" else "{}")

            reader = get_reader_for_file(file_path)

            assert reader is not None
            assert hasattr(reader, "read_project_info")
