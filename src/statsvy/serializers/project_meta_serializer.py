"""Serialization and deserialization of ProjectMeta objects."""

from datetime import date
from pathlib import Path
from typing import Any

from statsvy.data.git_info import GitInfo
from statsvy.data.project_meta import ProjectMeta
from statsvy.serializers.git_info_serializer import GitInfoSerializer


class ProjectMetaSerializer:
    """Handles conversion of ProjectMeta to/from dictionary format."""

    @staticmethod
    def to_dict(meta: ProjectMeta) -> dict[str, Any]:
        """Serialize project metadata to a JSON-compatible dictionary.

        Args:
            meta: Project metadata to serialize.

        Returns:
            A dictionary suitable for JSON serialization.
        """
        data: dict[str, Any] = {
            "name": meta.name,
            "path": str(meta.path),
            "date_added": str(meta.date_added),
            "last_scan": meta.last_scan,
        }

        if meta.git_info is not None:
            data["git_info"] = GitInfoSerializer.to_dict(meta.git_info)

        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProjectMeta:
        """Deserialize project metadata from a dictionary.

        Args:
            data: Dictionary containing serialized project metadata.

        Returns:
            ProjectMeta object reconstructed from the dictionary.

        Raises:
            KeyError: If required keys are missing from the dictionary.
        """
        git_info_data = data.get("git_info")
        git_info = None
        if git_info_data:
            git_info = GitInfo(
                is_git_repo=git_info_data.get("is_git_repo", False),
                remote_url=git_info_data.get("remote_url"),
                current_branch=git_info_data.get("current_branch"),
                commit_count=git_info_data.get("commit_count"),
                contributors=git_info_data.get("contributors"),
                last_commit_date=git_info_data.get("last_commit_date"),
                branches=git_info_data.get("branches"),
                commits_per_month_all_time=git_info_data.get(
                    "commits_per_month_all_time"
                ),
                commits_last_30_days=git_info_data.get("commits_last_30_days"),
            )

        return ProjectMeta(
            name=data["name"],
            path=Path(data["path"]),
            date_added=date.fromisoformat(data["date_added"]),
            last_scan=data.get("last_scan"),
            git_info=git_info,
        )
