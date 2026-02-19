"""Storage coordination for scan history and project metadata."""

import os
from pathlib import Path

from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.storage.history_storage import HistoryStorage
from statsvy.storage.project_metadata_storage import ProjectMetadataStorage
from statsvy.utils.console import console


class Storage:
    """Coordinates persistence operations for metrics and project data."""

    @staticmethod
    def save(metrics: Metrics, config: Config | None = None) -> None:
        """Save metrics to the scan history file.

        Args:
            metrics: The Metrics object to persist.
            config: Optional Config instance for storage settings.
        """
        config = config or Config.default()
        if config.core.verbose:
            console.print("Saving scan results...")

        stats_dir = Storage._get_stats_dir()
        if stats_dir is None:
            if config.core.verbose:
                console.print("No .statsvy directory found, skipping save")
            return

        # Gate save behind tracked-project semantics
        if not Storage._is_tracked_project(stats_dir, metrics, config):
            return

        history_file = stats_dir / "history.json"
        project_file = stats_dir / "project.json"

        # Save to history
        HistoryStorage.save_entry(history_file, metrics, config)

        # Update project metadata
        latest_entry = HistoryStorage.get_latest_entry(history_file, config)
        if latest_entry:
            scan_time = latest_entry.get("time", "")
            ProjectMetadataStorage.update_last_scan(project_file, scan_time, config)

    @staticmethod
    def _is_tracked_project(stats_dir: Path, metrics: Metrics, config: Config) -> bool:
        """Return True when the stats directory represents the tracked project.

        The project is considered tracked when `.statsvy/project.json` exists,
        is valid JSON, and its `path` matches either the current working
        directory or the scanned metrics path.
        """
        project_file = stats_dir / "project.json"
        if not Storage._validate_project_file(project_file, config):
            return False

        project_data = ProjectMetadataStorage.load_project_data(project_file)
        if not project_data:
            if config.core.verbose:
                console.print("Project metadata invalid or corrupted — skipping save")
            return False

        tracked_path = project_data.get("path")
        if tracked_path is None:
            if config.core.verbose:
                console.print("Project path not set in project.json — skipping save")
            return False

        return Storage._validate_tracked_path(tracked_path, metrics.path, config)

    @staticmethod
    def _validate_tracked_path(
        tracked_path: str, metrics_path: Path | str, config: Config
    ) -> bool:
        """Validate that the tracked path matches the metrics path.

        Only save history when the scanned path exactly matches the tracked
        project path. Previously the code also allowed saving when the
        current working directory matched the tracked path which caused
        scans of subdirectories (while running from project root) to be
        recorded incorrectly. Compare resolved paths to be robust.
        """
        if not Storage._paths_match(tracked_path, metrics_path):
            if config.core.verbose:
                console.print("Project path mismatch — skipping save")
            return False
        return True

    @staticmethod
    def _validate_project_file(project_file: Path, config: Config) -> bool:
        """Check if project file exists."""
        if not project_file.exists():
            if config.core.verbose:
                console.print("No project.json found in .statsvy — skipping save")
            return False
        return True

    @staticmethod
    def _paths_match(tracked_path: str, metrics_path: Path | str) -> bool:
        """Check if two paths resolve to the same location.

        Use non-strict resolution to avoid failures on paths that may not be
        present or when resolving symlinks is not possible in the test
        environment. Comparing the fully resolved (absolute) string forms
        prevents accidental matches for subdirectories or different
        relative representations of the same path.
        """
        # Use strict=False so resolution does not raise for non-existent or
        # indirectly accessible paths; expanduser() handles tilde paths.
        tracked_resolved = str(Path(tracked_path).expanduser().resolve(strict=False))
        metrics_resolved = str(Path(metrics_path).expanduser().resolve(strict=False))

        return tracked_resolved == metrics_resolved

    @staticmethod
    def _get_stats_dir() -> Path | None:
        """Retrieve the path to the .statsvy directory in current working directory.

        Returns:
            Path object if the directory exists, otherwise None.
        """
        stats_dir = Path.cwd() / ".statsvy"
        return stats_dir if os.path.isdir(stats_dir) else None
