"""Tests for dependency list display in formatters.

Verifies that all three formatters (table, markdown, json) show a full
dependency list by default and suppress it when show_deps_list=False.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from statsvy.data.config import DisplayConfig
from statsvy.data.dependency import Dependency
from statsvy.data.metrics import Metrics
from statsvy.data.project_info import DependencyInfo
from statsvy.formatters.json_formatter import JsonFormatter
from statsvy.formatters.markdown_formatter import MarkdownFormatter
from statsvy.formatters.table_formatter import TableFormatter


@pytest.fixture()
def sample_deps() -> DependencyInfo:
    """Create a DependencyInfo with three dependencies across all categories."""
    dependencies = (
        Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        ),
        Dependency(
            name="requests",
            version=">=2.28.0",
            category="prod",
            source_file="pyproject.toml",
        ),
        Dependency(
            name="pytest", version=">=7.0", category="dev", source_file="pyproject.toml"
        ),
        Dependency(
            name="mypy",
            version=">=1.0",
            category="optional",
            source_file="pyproject.toml",
        ),
    )
    return DependencyInfo(
        dependencies=dependencies,
        prod_count=2,
        dev_count=1,
        optional_count=1,
        total_count=4,
        sources=("pyproject.toml",),
        conflicts=(),
    )


@pytest.fixture()
def sample_metrics(sample_deps: DependencyInfo, tmp_path: Path) -> Metrics:
    """Create a Metrics object with dependency information."""
    return Metrics(
        name="test_project",
        path=tmp_path,
        timestamp=datetime(2024, 1, 1),
        total_files=5,
        total_size_bytes=1024,
        total_size_kb=1,
        total_size_mb=0,
        lines_by_lang={"Python": 100},
        comment_lines_by_lang={"Python": 10},
        blank_lines_by_lang={"Python": 5},
        lines_by_category={},
        comment_lines=10,
        blank_lines=5,
        total_lines=100,
        dependencies=sample_deps,
    )


class TestTableFormatterDepsListEnabled:
    """Table formatter shows dep list when show_deps_list=True."""

    def test_dep_list_table_present(self, sample_metrics: Metrics) -> None:
        """Dependency List table is shown when show_deps_list=True."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        result = TableFormatter(config).format(sample_metrics)
        assert "Dependency List" in result

    def test_dep_names_present(self, sample_metrics: Metrics) -> None:
        """Individual dependency names appear in output when show_deps_list=True."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        result = TableFormatter(config).format(sample_metrics)
        assert "click" in result
        assert "pytest" in result

    def test_default_no_display_config_shows_list(
        self, sample_metrics: Metrics
    ) -> None:
        """Dep list is shown when no display config is provided (default True)."""
        result = TableFormatter(None).format(sample_metrics)
        assert "Dependency List" in result


class TestTableFormatterDepsListDisabled:
    """Table formatter hides dep list when show_deps_list=False."""

    def test_dep_list_table_absent(self, sample_metrics: Metrics) -> None:
        """Dependency List table is absent when show_deps_list=False."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=False
        )
        result = TableFormatter(config).format(sample_metrics)
        assert "Dependency List" not in result

    def test_summary_table_still_present(self, sample_metrics: Metrics) -> None:
        """Summary counts table is still shown when show_deps_list=False."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=False
        )
        result = TableFormatter(config).format(sample_metrics)
        assert "Dependencies" in result


class TestTableFormatterDepsSortOrder:
    """Prod deps appear before dev, dev before optional."""

    def test_prod_before_dev(self, sample_metrics: Metrics) -> None:
        """Production category appears before Development in the list table."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        result = TableFormatter(config).format(sample_metrics)
        assert result.index("Production") < result.index("Development")

    def test_dev_before_optional(self, sample_metrics: Metrics) -> None:
        """Development category appears before Optional in the list table."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        result = TableFormatter(config).format(sample_metrics)
        assert result.index("Development") < result.index("Optional")


class TestMarkdownFormatterDepsListEnabled:
    """Markdown formatter shows packages section when show_deps_list=True."""

    def test_packages_section_present(self, sample_metrics: Metrics) -> None:
        """Packages section heading is present when show_deps_list=True."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        result = MarkdownFormatter(config).format(sample_metrics)
        assert "### Packages" in result

    def test_dep_names_present(self, sample_metrics: Metrics) -> None:
        """Individual dependency names appear in markdown output."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        result = MarkdownFormatter(config).format(sample_metrics)
        assert "click" in result
        assert "pytest" in result

    def test_default_no_display_config_shows_list(
        self, sample_metrics: Metrics
    ) -> None:
        """Packages section is shown when no display config is provided."""
        result = MarkdownFormatter(None).format(sample_metrics)
        assert "### Packages" in result


class TestMarkdownFormatterDepsListDisabled:
    """Markdown formatter hides packages section when show_deps_list=False."""

    def test_packages_section_absent(self, sample_metrics: Metrics) -> None:
        """Packages section is absent when show_deps_list=False."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=False
        )
        result = MarkdownFormatter(config).format(sample_metrics)
        assert "### Packages" not in result

    def test_summary_table_still_present(self, sample_metrics: Metrics) -> None:
        """Summary counts table is still rendered when show_deps_list=False."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=False
        )
        result = MarkdownFormatter(config).format(sample_metrics)
        assert "## Dependencies" in result


class TestJsonFormatterDepsListEnabled:
    """JSON formatter includes items key when show_deps_list=True."""

    def test_items_key_present(self, sample_metrics: Metrics) -> None:
        """The items key is present in dependencies dict when show_deps_list=True."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        raw = JsonFormatter(config).format(sample_metrics)
        data = json.loads(raw)
        assert "items" in data["dependencies"]

    def test_items_contains_dep_fields(self, sample_metrics: Metrics) -> None:
        """Each item in the list has name, version, category and source_file fields."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        raw = JsonFormatter(config).format(sample_metrics)
        data = json.loads(raw)
        item = data["dependencies"]["items"][0]
        assert "name" in item
        assert "version" in item
        assert "category" in item
        assert "source_file" in item

    def test_all_deps_included(self, sample_metrics: Metrics) -> None:
        """All dependencies are included in the items list."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=True
        )
        raw = JsonFormatter(config).format(sample_metrics)
        data = json.loads(raw)
        names = {d["name"] for d in data["dependencies"]["items"]}
        assert names == {"click", "requests", "pytest", "mypy"}

    def test_default_no_display_config_includes_items(
        self, sample_metrics: Metrics
    ) -> None:
        """Items are included in JSON output when no display config is provided."""
        raw = JsonFormatter(None).format(sample_metrics)
        data = json.loads(raw)
        assert "items" in data["dependencies"]


class TestJsonFormatterDepsListDisabled:
    """JSON formatter omits items key when show_deps_list=False."""

    def test_items_key_absent(self, sample_metrics: Metrics) -> None:
        """The items key is absent from dependencies dict when show_deps_list=False."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=False
        )
        raw = JsonFormatter(config).format(sample_metrics)
        data = json.loads(raw)
        assert "items" not in data["dependencies"]

    def test_count_fields_still_present(self, sample_metrics: Metrics) -> None:
        """Summary count fields are still present when show_deps_list=False."""
        config = DisplayConfig(
            truncate_paths=False, show_percentages=False, show_deps_list=False
        )
        raw = JsonFormatter(config).format(sample_metrics)
        data = json.loads(raw)
        assert data["dependencies"]["total_count"] == 4
        assert data["dependencies"]["prod_count"] == 2
