"""Unit tests for `statsvy.core.project_config_readers`.

These tests cover the small reader implementations and the factory used by
`core` code paths. They mirror expectations in the other `config_readers`
packages but exercise the core module's implementations and branches.
"""

import json
import tomllib
from pathlib import Path

import pytest

from statsvy.core import project_config_readers as pcr
from statsvy.core.project_config_readers import (
    CargoTomlReader,
    PackageJsonReader,
    PyProjectReader,
    get_reader_for_file,
)


class TestPyProjectReader:
    """Tests for reading project name from pyproject.toml."""

    def test_reads_name_from_project_section(self, tmp_path: Path) -> None:
        """Read name from the standard [project] table."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "my-pyproj"
""")

        reader = PyProjectReader()
        assert reader.read_project_name(pyproject) == "my-pyproj"

    def test_returns_none_when_no_project_section(self, tmp_path: Path) -> None:
        """Return None when no [project] table is present."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.some]
value = 1
""")

        reader = PyProjectReader()
        assert reader.read_project_name(pyproject) is None

    def test_raises_on_malformed_toml(self, tmp_path: Path) -> None:
        """Raise tomllib.TOMLDecodeError for malformed TOML."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project\nname = invalid")

        reader = PyProjectReader()
        with pytest.raises(tomllib.TOMLDecodeError):
            reader.read_project_name(pyproject)

    def test_handles_alternative_project_key_via_loader_monkeypatch(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Accept alternative '[project]' key returned by the TOML loader.

        The test monkeypatches `tomllib.load` to simulate a non-standard
        representation used by some tooling.
        """

        def _fake_load(f: object) -> dict[str, dict[str, str]]:
            # Reference the file argument to avoid unused-argument lint errors.
            _ = f
            return {"[project]": {"name": "alt"}}

        monkeypatch.setattr(pcr.tomllib, "load", _fake_load)

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")

        reader = PyProjectReader()
        assert reader.read_project_name(pyproject) == "alt"


class TestPackageJsonReader:
    """Tests for reading project name from package.json."""

    def test_reads_name(self, tmp_path: Path) -> None:
        """Return name when 'name' key is present in JSON object."""
        package = tmp_path / "package.json"
        package.write_text(json.dumps({"name": "pkg-name"}))

        reader = PackageJsonReader()
        assert reader.read_project_name(package) == "pkg-name"

    def test_returns_none_when_no_name(self, tmp_path: Path) -> None:
        """Return None when JSON is valid but does not contain a name."""
        package = tmp_path / "package.json"
        package.write_text("[]")  # valid JSON but not an object

        reader = PackageJsonReader()
        assert reader.read_project_name(package) is None

    def test_raises_on_malformed_json(self, tmp_path: Path) -> None:
        """Raise json.JSONDecodeError for malformed JSON content."""
        package = tmp_path / "package.json"
        package.write_text("{ name: 'bad' }")

        reader = PackageJsonReader()
        with pytest.raises(json.JSONDecodeError):
            reader.read_project_name(package)


class TestCargoTomlReader:
    """Tests for reading project name from Cargo.toml."""

    def test_reads_name_from_package_section(self, tmp_path: Path) -> None:
        """Read name from the [package] table."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("""
[package]
name = "cargo-name"
""")

        reader = CargoTomlReader()
        assert reader.read_project_name(cargo) == "cargo-name"

    def test_returns_none_when_no_package_section(self, tmp_path: Path) -> None:
        """Return None when no [package] table exists."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("""
[lib]
name = "not-package"
""")

        reader = CargoTomlReader()
        assert reader.read_project_name(cargo) is None

    def test_raises_on_malformed_toml(self, tmp_path: Path) -> None:
        """Raise tomllib.TOMLDecodeError for malformed TOML."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("[package\nname = bad")

        reader = CargoTomlReader()
        with pytest.raises(tomllib.TOMLDecodeError):
            reader.read_project_name(cargo)


class TestGetReaderForFileFactory:
    """Tests for the `get_reader_for_file` factory function."""

    def test_returns_correct_reader_instances(self, tmp_path: Path) -> None:
        """Return appropriate reader instances for known config files."""
        py = tmp_path / "pyproject.toml"
        py.write_text("")
        pkg = tmp_path / "package.json"
        pkg.write_text("{}")
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text("")

        assert isinstance(get_reader_for_file(py), PyProjectReader)
        assert isinstance(get_reader_for_file(pkg), PackageJsonReader)
        assert isinstance(get_reader_for_file(cargo), CargoTomlReader)

    def test_returns_none_for_unsupported_file(self, tmp_path: Path) -> None:
        """Return None for unsupported or unknown file names."""
        other = tmp_path / "something.txt"
        other.write_text("")

        assert get_reader_for_file(other) is None
