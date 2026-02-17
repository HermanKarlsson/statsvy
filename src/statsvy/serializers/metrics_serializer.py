"""Serialization and deserialization of Metrics objects."""

import datetime
from pathlib import Path
from typing import Any

from statsvy.data.metrics import Metrics
from statsvy.serializers.project_info_serializer import ProjectInfoSerializer


class MetricsSerializer:
    """Handles conversion of Metrics to/from dictionary format."""

    @staticmethod
    def to_dict(metrics: Metrics) -> dict[str, Any]:
        """Convert a Metrics object to a dictionary.

        Args:
            metrics: The Metrics object to serialize.

        Returns:
            Dictionary representation of the metrics.
        """
        data: dict[str, Any] = {
            "name": metrics.name,
            "path": str(metrics.path),
            "timestamp": metrics.timestamp.isoformat(),
            "total_files": metrics.total_files,
            "total_size_bytes": metrics.total_size_bytes,
            "total_size_kb": metrics.total_size_kb,
            "total_size_mb": metrics.total_size_mb,
            "lines_by_lang": dict(metrics.lines_by_lang),
            "comment_lines_by_lang": dict(metrics.comment_lines_by_lang),
            "blank_lines_by_lang": dict(metrics.blank_lines_by_lang),
            "lines_by_category": dict(metrics.lines_by_category),
            "comment_lines": metrics.comment_lines,
            "blank_lines": metrics.blank_lines,
            "total_lines": metrics.total_lines,
        }

        # Serialize dependencies if present
        if metrics.dependencies:
            data["dependencies"] = ProjectInfoSerializer.serialize_dependency_info(
                metrics.dependencies
            )

        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Metrics:
        """Convert a serialized metrics dictionary back to a Metrics object.

        Args:
            data: The serialized metrics dictionary.

        Returns:
            A Metrics object reconstructed from the dictionary.

        Raises:
            KeyError: If required keys are missing from the dictionary.
            ValueError: If data types cannot be converted properly.
        """
        # Deserialize dependencies if present
        dependencies = None
        if data.get("dependencies"):
            dependencies = ProjectInfoSerializer.deserialize_dependency_info(
                data["dependencies"]
            )

        return Metrics(
            name=data.get("name", ""),
            path=Path(data.get("path", "")),
            timestamp=datetime.datetime.fromisoformat(data.get("timestamp", "")),
            total_files=data.get("total_files", 0),
            total_size_bytes=data.get("total_size_bytes", 0),
            total_size_kb=data.get("total_size_kb", 0),
            total_size_mb=data.get("total_size_mb", 0),
            lines_by_lang=data.get("lines_by_lang", {}),
            comment_lines_by_lang=data.get("comment_lines_by_lang", {}),
            blank_lines_by_lang=data.get("blank_lines_by_lang", {}),
            lines_by_category=data.get("lines_by_category", {}),
            comment_lines=data.get("comment_lines", 0),
            blank_lines=data.get("blank_lines", 0),
            total_lines=data.get("total_lines", 0),
            dependencies=dependencies,
        )
