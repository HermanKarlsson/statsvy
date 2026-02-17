"""Project metadata storage and retrieval operations."""

import json
from pathlib import Path
from typing import Any

from rich.text import Text

from statsvy.data.config import Config
from statsvy.utils.console import console


class ProjectMetadataStorage:
    """Manages persistence and retrieval of project metadata."""

    @staticmethod
    def load_project_data(project_file: Path) -> dict[str, Any] | None:
        """Load and validate project metadata.

        Args:
            project_file: Path to project.json.

        Returns:
            Parsed project metadata dict when valid, else None.
        """
        try:
            project_data = json.loads(project_file.read_text())
        except json.JSONDecodeError:
            return None

        if not isinstance(project_data, dict):
            return None

        return project_data

    @staticmethod
    def update_last_scan(
        project_file: Path, scan_time: str, config: Config | None = None
    ) -> None:
        """Update last_scan timestamp in project metadata.

        Args:
            project_file: Path to project.json file.
            scan_time: Timestamp string for the latest scan.
            config: Optional Config instance for verbose logging.
        """
        config = config or Config.default()

        if not project_file.exists():
            return

        project_data = ProjectMetadataStorage.load_project_data(project_file)
        if project_data is None:
            if config.core.verbose:
                console.print(Text("Warning: Project file corrupted", style="yellow"))
            return

        project_data["last_scan"] = scan_time
        project_file.write_text(json.dumps(project_data, indent=2))

        if config.core.verbose:
            console.print(f"Updated project last_scan: {scan_time}")

    @staticmethod
    def save_project_data(
        project_file: Path, project_data: dict[str, Any], config: Config | None = None
    ) -> None:
        """Save project metadata to file.

        Args:
            project_file: Path to project.json file.
            project_data: Project metadata dictionary.
            config: Optional Config instance for verbose logging.
        """
        config = config or Config.default()

        project_file.parent.mkdir(exist_ok=True, parents=True)
        try:
            project_file.write_text(json.dumps(project_data, indent=2))
        except OSError as exc:
            console.print(
                Text(
                    f"Failed to save project metadata to {project_file}: {exc}",
                    style="red",
                )
            )
            raise

        if config.core.verbose:
            console.print(f"Saved project metadata to {project_file}")
