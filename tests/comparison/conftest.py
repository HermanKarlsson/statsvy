"""Test fixtures for comparison testing."""

import datetime
from pathlib import Path

import pytest

from statsvy.data.metrics import Metrics


@pytest.fixture
def sample_metrics_project1() -> Metrics:
    """Create sample metrics for project 1."""
    return Metrics(
        name="Project Alpha",
        path=Path("/path/to/project1"),
        timestamp=datetime.datetime(2026, 2, 15, 10, 0, 0),
        total_files=42,
        total_size_bytes=1048576,
        total_size_kb=1024,
        total_size_mb=1,
        lines_by_lang={
            "Python": 2500,
            "JavaScript": 1000,
            "TypeScript": 500,
        },
        comment_lines_by_lang={
            "Python": 500,
            "JavaScript": 100,
            "TypeScript": 50,
        },
        blank_lines_by_lang={
            "Python": 300,
            "JavaScript": 100,
            "TypeScript": 50,
        },
        lines_by_category={
            "code": 2700,
            "comment": 650,
            "blank": 450,
        },
        comment_lines=650,
        blank_lines=450,
        total_lines=4000,
    )


@pytest.fixture
def sample_metrics_project2() -> Metrics:
    """Create sample metrics for project 2 (slightly larger)."""
    return Metrics(
        name="Project Beta",
        path=Path("/path/to/project2"),
        timestamp=datetime.datetime(2026, 2, 15, 11, 0, 0),
        total_files=58,
        total_size_bytes=2097152,
        total_size_kb=2048,
        total_size_mb=2,
        lines_by_lang={
            "Python": 3200,
            "JavaScript": 1500,
            "TypeScript": 700,
            "Go": 400,
        },
        comment_lines_by_lang={
            "Python": 650,
            "JavaScript": 150,
            "TypeScript": 70,
            "Go": 40,
        },
        blank_lines_by_lang={
            "Python": 400,
            "JavaScript": 150,
            "TypeScript": 70,
            "Go": 40,
        },
        lines_by_category={
            "code": 4100,
            "comment": 910,
            "blank": 660,
        },
        comment_lines=910,
        blank_lines=660,
        total_lines=5670,
    )
