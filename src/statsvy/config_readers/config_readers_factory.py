"""Factory for creating configuration file readers.

This module provides factory functions to create appropriate reader
instances based on configuration file paths.
"""

from pathlib import Path

from statsvy.config_readers.cargo_toml_reader import CargoTomlReader
from statsvy.config_readers.package_json_reader import PackageJsonReader
from statsvy.config_readers.project_config_reader import ProjectConfigReader
from statsvy.config_readers.pyproject_reader import PyProjectReader
from statsvy.config_readers.requirements_txt_reader import RequirementsTxtReader


def get_reader_for_file(file_path: Path) -> ProjectConfigReader | None:
    """Get the appropriate config reader for a file.

    Args:
        file_path: Path to the configuration file.

    Returns:
        Appropriate reader instance, or None if file type is not supported.
    """
    if file_path.name == "pyproject.toml":
        return PyProjectReader()
    elif file_path.name == "package.json":
        return PackageJsonReader()
    elif file_path.name == "Cargo.toml":
        return CargoTomlReader()
    elif file_path.name == "requirements.txt":
        return RequirementsTxtReader()
    return None
