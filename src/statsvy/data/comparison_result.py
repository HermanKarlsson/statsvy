"""Comparison result data model for comparing two metric snapshots.

This module defines the data structure for results when comparing metrics
from two distinct project scans.
"""

import datetime
from dataclasses import dataclass
from typing import Any

from statsvy.data.metrics import Metrics


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Represent the comparison between two metric snapshots.

    Stores absolute and relative deltas for all metrics, allowing formatters
    to display comparison results in multiple formats (table, json, markdown).

    Attributes:
        project1: Metrics from the first project.
        project2: Metrics from the second project.
        deltas: Dict containing overall, by_language, and by_category deltas.
            Structure: {
                "overall": dict[str, int],
                "by_language": dict[str, dict[str, int | None]],
                "by_category": dict[str, int | None]
            }
        timestamp: When the comparison was performed.
    """

    project1: Metrics
    project2: Metrics
    deltas: dict[str, Any]
    timestamp: datetime.datetime
