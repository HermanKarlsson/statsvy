"""Project file scanner coordinator.

Orchestrates the discovery and reading of project configuration files.
"""

from pathlib import Path

from statsvy.config_readers.config_readers_factory import get_reader_for_file
from statsvy.data.project_info import ProjectFileInfo
from statsvy.utils.project_info_merger import ProjectInfoMerger


class ProjectScanner:
    """Scans a project directory for configuration files and extracts metadata.

    Finds all supported project configuration files (pyproject.toml,
    package.json, Cargo.toml, requirements.txt) and reads project information
    from them. If multiple files are found, their results are merged with
    conflict detection.
    """

    # Files to search for, in order
    CONFIG_FILES = (
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "requirements.txt",
    )

    def __init__(self, target_path: Path | str) -> None:
        """Initialize scanner for a project directory.

        Args:
            target_path: Path or string path to the project root directory.
        """
        self.target_path = Path(target_path)

    def scan(self) -> ProjectFileInfo | None:
        """Scan project directory and extract configuration information.

        Searches for all supported configuration files in the target directory.
        If none are found, returns None. If one is found, returns its parsed
        content. If multiple are found, merges them with conflict detection.

        Returns:
            ProjectFileInfo with extracted metadata, or None if no supported
            config files are found.

        Raises:
            ValueError: If a config file cannot be parsed.
        """
        found_files = self._find_config_files()

        if not found_files:
            return None

        project_infos = self._read_config_files(found_files)

        if not project_infos:
            return None

        return ProjectInfoMerger.merge(project_infos)

    def _find_config_files(self) -> list[Path]:
        """Find all supported config files in target directory.

        Returns:
            List of Path objects for found config files.
        """
        found_files: list[Path] = []
        for config_file in self.CONFIG_FILES:
            file_path = self.target_path / config_file
            if file_path.is_file():
                found_files.append(file_path)
        return found_files

    @staticmethod
    def _read_config_files(file_paths: list[Path]) -> list[ProjectFileInfo]:
        """Read all config files and return their parsed content.

        Args:
            file_paths: List of Path objects to read.

        Returns:
            List of ProjectFileInfo objects from successfully read files.

        Raises:
            ValueError: If a config file cannot be parsed.
        """
        project_infos: list[ProjectFileInfo] = []
        for file_path in file_paths:
            reader = get_reader_for_file(file_path)
            if reader:
                try:
                    info = reader.read_project_info(file_path)
                    project_infos.append(info)
                except (ValueError, OSError) as e:
                    raise ValueError(f"Failed to parse {file_path.name}: {e}") from e
        return project_infos
