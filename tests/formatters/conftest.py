"""Shared fixtures for formatters tests."""

from datetime import datetime
from pathlib import Path

import pytest

from statsvy.data.metrics import Metrics


@pytest.fixture
def sample_metrics() -> Metrics:
    """Creates a sample Metrics object populated with dummy data for testing.

    Returns:
        Metrics: A fully populated metrics object with languages and categories.
    """
    return Metrics(
        name="test_project",
        path=Path("/home/user/test_project"),
        timestamp=datetime(2024, 2, 8, 10, 30, 45),
        total_files=42,
        total_size_bytes=1048576,
        total_size_kb=1024,
        total_size_mb=1,
        lines_by_lang={"python": 5000, "javascript": 2000, "css": 1500},
        comment_lines_by_lang={"python": 500, "javascript": 200, "css": 100},
        blank_lines_by_lang={"python": 300, "javascript": 150, "css": 50},
        lines_by_category={"programming": 7500, "markup": 1500},
        comment_lines=800,
        blank_lines=500,
        total_lines=9800,
    )


@pytest.fixture
def empty_metrics() -> Metrics:
    """Creates a Metrics object with no files or lines.

    Returns:
        Metrics: A metrics object representing an empty project.
    """
    return Metrics(
        name="empty_project",
        path=Path("/home/user/empty_project"),
        timestamp=datetime(2024, 1, 1, 0, 0, 0),
        total_files=0,
        total_size_bytes=0,
        total_size_kb=0,
        total_size_mb=0,
        lines_by_lang={},
        comment_lines_by_lang={},
        blank_lines_by_lang={},
        lines_by_category={},
        comment_lines=0,
        blank_lines=0,
        total_lines=0,
    )
