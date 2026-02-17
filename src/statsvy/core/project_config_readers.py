"""Project configuration readers using strategy pattern."""

import json
import tomllib
from pathlib import Path
from typing import Protocol


class ProjectConfigReader(Protocol):
    """Protocol for reading project configuration files."""

    def read_project_name(self, path: Path) -> str | None:
        """Read the project name from a configuration file.

        Args:
            path: Path to the configuration file.

        Returns:
            Project name if found, None otherwise.
        """
        ...


class PyProjectReader:
    """Reads project name from pyproject.toml files."""

    def read_project_name(self, path: Path) -> str | None:
        """Read project name from pyproject.toml.

        Args:
            path: Path to pyproject.toml file.

        Returns:
            Project name if found, None otherwise.

        Raises:
            tomllib.TOMLDecodeError: If TOML file is malformed.
        """
        with open(path, mode="rb") as f:
            data = tomllib.load(f)

        if not isinstance(data, dict):
            return None

        # Try standard [project] section
        project_section = data.get("project")
        if isinstance(project_section, dict):
            name = project_section.get("name")
            if name:
                return str(name)

        # Try alternative [project] section (some tools use this)
        alternative_section = data.get("[project]")
        if isinstance(alternative_section, dict):
            name = alternative_section.get("name")
            if name:
                return str(name)

        return None


class PackageJsonReader:
    """Reads project name from package.json files."""

    def read_project_name(self, path: Path) -> str | None:
        """Read project name from package.json.

        Args:
            path: Path to package.json file.

        Returns:
            Project name if found, None otherwise.

        Raises:
            json.JSONDecodeError: If JSON file is malformed.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        name = data.get("name")
        return str(name) if name else None


class CargoTomlReader:
    """Reads project name from Cargo.toml files."""

    def read_project_name(self, path: Path) -> str | None:
        """Read project name from Cargo.toml.

        Args:
            path: Path to Cargo.toml file.

        Returns:
            Project name if found, None otherwise.

        Raises:
            tomllib.TOMLDecodeError: If TOML file is malformed.
        """
        with open(path, mode="rb") as f:
            data = tomllib.load(f)

        if not isinstance(data, dict):
            return None

        package_section = data.get("package")
        if isinstance(package_section, dict):
            name = package_section.get("name")
            if name:
                return str(name)

        return None


def get_reader_for_file(file_path: Path) -> ProjectConfigReader | None:
    """Get the appropriate config reader for a file.

    Args:
        file_path: Path to the configuration file.

    Returns:
        Appropriate reader instance, or None if file type not supported.
    """
    if file_path.name == "pyproject.toml":
        return PyProjectReader()
    elif file_path.name == "package.json":
        return PackageJsonReader()
    elif file_path.name == "Cargo.toml":
        return CargoTomlReader()
    return None
