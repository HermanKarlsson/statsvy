"""Public DTO for comparison results."""

from dataclasses import dataclass
from typing import Any

from statsvy.api.api_scan_result import ApiScanResult


@dataclass(frozen=True, slots=True)
class ApiComparisonResult:
    """Represent an API-safe comparison result contract.

    Attributes:
        project1: The first scan snapshot used for comparison.
        project2: The second scan snapshot used for comparison.
        deltas: Calculated delta payload grouped by category.
        timestamp: ISO-8601 timestamp when comparison completed.
    """

    project1: ApiScanResult
    project2: ApiScanResult
    deltas: dict[str, Any]
    timestamp: str
