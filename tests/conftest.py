"""Shared pytest fixtures for formatter tests."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _make_metrics(
    *,
    name: str = "my_project",
    path: str = "/home/user/project",
    total_files: int = 42,
    total_size: float = 1.5,
    total_lines: int = 1000,
    lines_by_category: dict | None = None,
    lines_by_lang: dict | None = None,
    comment_lines_by_lang: dict | None = None,
    blank_lines_by_lang: dict | None = None,
    timestamp: datetime | None = None,
) -> MagicMock:
    """Create a mock Metrics object with sensible defaults.

    Args:
        name: Project name.
        path: Filesystem path.
        total_files: Number of scanned files.
        total_size: Total size in megabytes.
        total_lines: Total line count.
        lines_by_category: Optional mapping of category -> line count.
        lines_by_lang: Optional mapping of language -> line count.
        comment_lines_by_lang: Optional mapping of language -> comment lines.
        blank_lines_by_lang: Optional mapping of language -> blank lines.
        timestamp: Optional scan timestamp.

    Returns:
        MagicMock: A mock that quacks like a Metrics object.
    """
    m = MagicMock()
    m.name = name
    m.path = Path(path)
    m.total_files = total_files
    m.total_size_mb = total_size
    m.total_size_kb = int(total_size * 1024)
    m.total_lines = total_lines
    m.timestamp = timestamp or datetime(2024, 6, 1, 12, 0, 0)
    m.lines_by_category = lines_by_category or {}
    m.lines_by_lang = lines_by_lang or {}
    m.comment_lines_by_lang = comment_lines_by_lang or {}
    m.blank_lines_by_lang = blank_lines_by_lang or {}
    return m


@pytest.fixture()
def minimal_metrics() -> MagicMock:
    """Metrics with no language or category data."""
    return _make_metrics()


@pytest.fixture()
def full_metrics() -> MagicMock:
    """Metrics with both category and language data."""
    return _make_metrics(
        name="statsvy",
        total_lines=500,
        lines_by_category={"source": 350, "test": 100, "unknown": 50},
        lines_by_lang={"Python": 300, "YAML": 200},
        comment_lines_by_lang={"Python": 40, "YAML": 10},
        blank_lines_by_lang={"Python": 30, "YAML": 20},
    )


@pytest.fixture()
def zero_lines_metrics() -> MagicMock:
    """Metrics where total_lines is zero."""
    return _make_metrics(
        total_lines=0,
        lines_by_category={"source": 0},
        lines_by_lang={"Python": 0},
        comment_lines_by_lang={"Python": 0},
        blank_lines_by_lang={"Python": 0},
    )
