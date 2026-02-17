"""Project tracking functionality for statsvy.

This module handles initialization and management of project tracking,
including reading project configuration files and managing project metadata.
"""

import shutil
from datetime import date
from pathlib import Path

from rich.text import Text

from statsvy.core.git_stats import GitStats
from statsvy.core.project_scanner import ProjectScanner
from statsvy.data.project_meta import ProjectMeta
from statsvy.serializers.project_meta_serializer import ProjectMetaSerializer
from statsvy.storage.project_metadata_storage import ProjectMetadataStorage
from statsvy.utils.console import console


class Project:
    """Manages project tracking and metadata initialization."""

    @staticmethod
    def track() -> ProjectMeta:
        """Initialize project tracking for the current directory.

        Searches for and reads project configuration files (pyproject.toml,
        package.json, or Cargo.toml) to extract project metadata. Creates
        a .statsvy/project.json file containing project name, path, and
        the date tracking was initiated.

        Returns:
            ProjectMeta: Metadata for the tracked project.

        Raises:
            FileNotFoundError: If no supported configuration file is found.
            ValueError: If project name cannot be extracted.

        Prints:
            A success message with the project name upon completion.
            An error message if no configuration file is found.
        """
        # Scan for project configuration files
        scanner = ProjectScanner(Path.cwd())
        project_info = scanner.scan()

        if not project_info:
            console.print(
                Text("Error: No supported configuration file found"),
                style="red",
            )
            raise FileNotFoundError("No configuration file found")

        if not project_info.name:
            console.print(
                Text("Error: No project name found in configuration files"),
                style="red",
            )
            raise ValueError("Project name missing from configuration")

        name = project_info.name

        # Create metadata
        git_info = GitStats.detect_repository(Path.cwd())
        meta = ProjectMeta(
            name=name,
            path=Path.cwd(),
            date_added=date.today(),
            git_info=git_info,
        )

        # Serialize and save
        proj_json = ProjectMetaSerializer.to_dict(meta)
        proj_file = Path.cwd() / ".statsvy" / "project.json"
        ProjectMetadataStorage.save_project_data(proj_file, proj_json)

        console.print(f"Started tracking project: {meta.name}")
        return meta

    @staticmethod
    def untrack() -> None:
        """Stop tracking the current project.

        Removes the .statsvy directory and all its contents from the
        current working directory, effectively untracking the project.

        Prints:
            A confirmation message upon successful removal.
        """
        shutil.rmtree(Path.cwd() / ".statsvy/")
        console.print("Untracked project")
