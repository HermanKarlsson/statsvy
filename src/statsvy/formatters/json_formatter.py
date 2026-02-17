"""Formatter module for JSON output."""

import json
from typing import Any

from statsvy.data.git_info import GitInfo
from statsvy.data.metrics import Metrics
from statsvy.serializers.git_info_serializer import GitInfoSerializer
from statsvy.utils.formatting import format_size


class JsonFormatter:
    """Formats Metrics objects as JSON strings."""

    def format(self, metrics: Metrics, git_info: GitInfo | None = None) -> str:
        """Format metrics data as a JSON string.

        Args:
            metrics: The Metrics object to format.
            git_info: Optional Git repository metadata to include.

        Returns:
            str: A pretty-printed JSON string representing the metrics.
        """
        data: dict[str, Any] = self._build_dict(metrics, git_info)
        return json.dumps(data, indent=2)

    def _build_dict(self, metrics: Metrics, git_info: GitInfo | None) -> dict[str, Any]:
        """Build a serialisable dictionary from a Metrics object.

        Args:
            metrics: The Metrics object to convert.
            git_info: Optional Git repository metadata to include.

        Returns:
            dict: A JSON-serialisable representation of the metrics.
        """
        # Prefer explicit byte field; fall back to kB/MB (from test mocks).
        bytes_val = self._extract_bytes(metrics)

        result: dict = {
            "name": metrics.name,
            "path": str(metrics.path),
            "timestamp": metrics.timestamp.strftime("%Y-%m-%d"),
            "total_files": metrics.total_files,
            "total_size": format_size(bytes_val),
            "total_lines": metrics.total_lines,
        }

        if git_info is not None:
            result["git_info"] = GitInfoSerializer.to_dict(git_info)

        if hasattr(metrics, "lines_by_category") and metrics.lines_by_category:
            result["lines_by_category"] = dict(metrics.lines_by_category)

        if metrics.lines_by_lang:
            languages: dict[str, Any] = {}
            for lang, lines in metrics.lines_by_lang.items():
                comments: int = metrics.comment_lines_by_lang.get(lang, 0)
                blanks: int = metrics.blank_lines_by_lang.get(lang, 0)
                code: int = lines - comments - blanks
                languages[lang] = {
                    "total": lines,
                    "code": code,
                    "comments": comments,
                    "blank": blanks,
                }
            result["lines_by_language"] = languages

        deps = getattr(metrics, "dependencies", None)
        if deps is not None:
            # defensively convert dependency fields into serialisable types
            result["dependencies"] = {
                "prod_count": int(deps.prod_count),
                "dev_count": int(deps.dev_count),
                "optional_count": int(deps.optional_count),
                "total_count": int(deps.total_count),
                "sources": list(deps.sources) if deps.sources is not None else [],
                "conflicts": list(deps.conflicts) if deps.conflicts is not None else [],
            }

        return result

    @staticmethod
    def _extract_bytes(metrics: Metrics) -> int:
        """Extract size in bytes from Metrics, handling legacy attributes.

        Args:
            metrics: The Metrics object to extract from.

        Returns:
            Size in bytes, or 0 if unavailable.
        """
        tsb = getattr(metrics, "total_size_bytes", None)
        if isinstance(tsb, int | float):
            return int(tsb)
        tsk = getattr(metrics, "total_size_kb", None)
        if isinstance(tsk, int | float):
            return int(tsk) * 1024
        tsm = getattr(metrics, "total_size_mb", None)
        if isinstance(tsm, int | float):
            return int(tsm * 1024 * 1024)
        return 0
