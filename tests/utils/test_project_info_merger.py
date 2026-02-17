"""Test suite for project information merger.

Tests verify that ProjectInfoMerger correctly combines multiple ProjectFileInfo
objects and detects version conflicts between dependencies from different files.
"""

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)
from statsvy.utils.project_info_merger import ProjectInfoMerger


class TestProjectInfoMergerEmptyInput:
    """Tests for handling empty input."""

    def test_merge_empty_list_returns_none(self) -> None:
        """Test that merging empty list returns None dependencies."""
        result = ProjectInfoMerger.merge([])
        assert result.name is None
        assert result.dependencies is None
        assert result.source_files == ()

    def test_merge_single_info(self) -> None:
        """Test that single info is returned unchanged."""
        dep = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep_info = DependencyInfo(
            dependencies=(dep,),
            prod_count=1,
            dev_count=0,
            optional_count=0,
            total_count=1,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        original = ProjectFileInfo(
            name="my-project",
            dependencies=dep_info,
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoMerger.merge([original])
        assert result == original


class TestProjectInfoMergerNameSelection:
    """Tests for project name selection."""

    def test_selects_first_non_none_name(self) -> None:
        """Test that first non-None name is selected."""
        info1 = ProjectFileInfo(name=None, dependencies=None, source_files=())
        info2 = ProjectFileInfo(name="my-project", dependencies=None, source_files=())
        info3 = ProjectFileInfo(
            name="other-project", dependencies=None, source_files=()
        )
        result = ProjectInfoMerger.merge([info1, info2, info3])
        assert result.name == "my-project"

    def test_returns_none_when_all_names_are_none(self) -> None:
        """Test that None is returned when all names are None."""
        info1 = ProjectFileInfo(name=None, dependencies=None, source_files=())
        info2 = ProjectFileInfo(name=None, dependencies=None, source_files=())
        result = ProjectInfoMerger.merge([info1, info2])
        assert result.name is None

    def test_prefers_first_available_name(self) -> None:
        """Test that first available name takes precedence."""
        info1 = ProjectFileInfo(name="first", dependencies=None, source_files=())
        info2 = ProjectFileInfo(name="second", dependencies=None, source_files=())
        result = ProjectInfoMerger.merge([info1, info2])
        assert result.name == "first"


class TestProjectInfoMergerDependencyMerging:
    """Tests for dependency merging."""

    def _make_dep_info(
        self,
        deps: list[Dependency] | None = None,
        sources: tuple[str, ...] = ("source.txt",),
    ) -> DependencyInfo:
        """Helper to create DependencyInfo."""
        if deps is None:
            deps = []
        prod_count = sum(1 for d in deps if d.category == "prod")
        dev_count = sum(1 for d in deps if d.category == "dev")
        optional_count = sum(1 for d in deps if d.category == "optional")
        return DependencyInfo(
            dependencies=tuple(deps),
            prod_count=prod_count,
            dev_count=dev_count,
            optional_count=optional_count,
            total_count=len(deps),
            sources=sources,
            conflicts=(),
        )

    def test_merges_dependencies_from_multiple_files(self) -> None:
        """Test that dependencies from multiple files are merged."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("pytest", "^7.0", "dev", "requirements.txt")

        info1 = ProjectFileInfo(
            name="my-project",
            dependencies=self._make_dep_info([dep1], ("pyproject.toml",)),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2], ("requirements.txt",)),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        assert result.dependencies.total_count == 2
        assert result.dependencies.prod_count == 1
        assert result.dependencies.dev_count == 1

    def test_returns_none_dependencies_when_all_none(self) -> None:
        """Test that None dependencies is returned when all are None."""
        info1 = ProjectFileInfo(
            name="project1",
            dependencies=None,
            source_files=("file1.txt",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=None,
            source_files=("file2.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])
        assert result.dependencies is None

    def test_ignores_none_dependencies_in_merge(self) -> None:
        """Test that None dependencies are ignored during merge."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        info1 = ProjectFileInfo(
            name="my-project",
            dependencies=self._make_dep_info([dep1], ("pyproject.toml",)),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=None,
            source_files=("empty.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        assert result.dependencies.total_count == 1


class TestProjectInfoMergerSourceFiles:
    """Tests for source file aggregation."""

    def test_aggregates_source_files(self) -> None:
        """Test that source files from all inputs are aggregated."""
        dep = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        info1 = ProjectFileInfo(
            name="project",
            dependencies=DependencyInfo(
                dependencies=(dep,),
                prod_count=1,
                dev_count=0,
                optional_count=0,
                total_count=1,
                sources=("pyproject.toml",),
                conflicts=(),
            ),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=None,
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert "pyproject.toml" in result.source_files
        assert "requirements.txt" in result.source_files

    def test_source_files_are_sorted(self) -> None:
        """Test that source files in result are sorted."""
        info1 = ProjectFileInfo(
            name="project",
            dependencies=None,
            source_files=("zzz.txt",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=None,
            source_files=("aaa.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        sources_list = list(result.source_files)
        assert sources_list == sorted(sources_list)


class TestProjectInfoMergerConflictDetection:
    """Tests for conflict detection."""

    def _make_dep_info(self, deps: list[Dependency] | None = None) -> DependencyInfo:
        """Helper to create DependencyInfo."""
        if deps is None:
            deps = []
        prod_count = sum(1 for d in deps if d.category == "prod")
        dev_count = sum(1 for d in deps if d.category == "dev")
        optional_count = sum(1 for d in deps if d.category == "optional")
        return DependencyInfo(
            dependencies=tuple(deps),
            prod_count=prod_count,
            dev_count=dev_count,
            optional_count=optional_count,
            total_count=len(deps),
            sources=tuple(d.source_file for d in deps),
            conflicts=(),
        )

    def test_detects_version_conflict(self) -> None:
        """Test that version conflicts are detected."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("click", ">=9.0.0", "prod", "requirements.txt")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1]),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2]),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        assert len(result.dependencies.conflicts) > 0
        assert "click" in result.dependencies.conflicts[0]

    def test_conflict_reported_for_same_dep_in_different_files(self) -> None:
        """Test that conflict is reported when same dep appears in multiple files."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("click", ">=8.0.0", "prod", "requirements.txt")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1]),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2]),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        # Conflict is reported even when versions are identical
        # (appears in multiple files)
        assert len(result.dependencies.conflicts) > 0

    def test_no_conflict_for_same_file_different_versions(self) -> None:
        """Test that no conflict is reported when same package in same file."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("click", ">=9.0.0", "prod", "pyproject.toml")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1, dep2]),
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoMerger.merge([info1])

        assert result.dependencies is not None
        # No conflict because both from same file
        assert len(result.dependencies.conflicts) == 0

    def test_detects_multiple_conflicts(self) -> None:
        """Test that multiple conflicts are detected."""
        dep1a = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep1b = Dependency("pytest", "^7.0", "dev", "pyproject.toml")
        dep2a = Dependency("click", ">=9.0.0", "prod", "requirements.txt")
        dep2b = Dependency("pytest", "^8.0", "dev", "requirements.txt")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1a, dep1b]),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2a, dep2b]),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        assert len(result.dependencies.conflicts) >= 2

    def test_conflict_message_includes_package_name(self) -> None:
        """Test that conflict message includes package name."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("click", ">=9.0.0", "prod", "requirements.txt")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1]),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2]),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        assert "click" in result.dependencies.conflicts[0]

    def test_conflict_message_includes_file_names(self) -> None:
        """Test that conflict message includes file names."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("click", ">=9.0.0", "prod", "requirements.txt")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1]),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2]),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        conflict_msg = result.dependencies.conflicts[0]
        assert "pyproject.toml" in conflict_msg
        assert "requirements.txt" in conflict_msg

    def test_conflict_message_includes_versions(self) -> None:
        """Test that conflict message includes version specifications."""
        dep1 = Dependency("click", ">=8.0.0", "prod", "pyproject.toml")
        dep2 = Dependency("click", ">=9.0.0", "prod", "requirements.txt")

        info1 = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info([dep1]),
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name=None,
            dependencies=self._make_dep_info([dep2]),
            source_files=("requirements.txt",),
        )
        result = ProjectInfoMerger.merge([info1, info2])

        assert result.dependencies is not None
        conflict_msg = result.dependencies.conflicts[0]
        assert "8.0.0" in conflict_msg
        assert "9.0.0" in conflict_msg


class TestProjectInfoMergerCounting:
    """Tests for dependency counting."""

    def _make_dep_info(self, deps: list[Dependency] | None = None) -> DependencyInfo:
        """Helper to create DependencyInfo."""
        if deps is None:
            deps = []
        prod_count = sum(1 for d in deps if d.category == "prod")
        dev_count = sum(1 for d in deps if d.category == "dev")
        optional_count = sum(1 for d in deps if d.category == "optional")
        return DependencyInfo(
            dependencies=tuple(deps),
            prod_count=prod_count,
            dev_count=dev_count,
            optional_count=optional_count,
            total_count=len(deps),
            sources=tuple(d.source_file for d in deps),
            conflicts=(),
        )

    def test_counts_prod_dependencies_correctly(self) -> None:
        """Test that prod dependencies are counted correctly."""
        deps = [
            Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),
            Dependency("requests", "^2.0", "prod", "pyproject.toml"),
        ]
        info = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info(deps),
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoMerger.merge([info])

        assert result.dependencies is not None
        assert result.dependencies.prod_count == 2

    def test_counts_dev_dependencies_correctly(self) -> None:
        """Test that dev dependencies are counted correctly."""
        deps = [
            Dependency("pytest", "^7.0", "dev", "pyproject.toml"),
            Dependency("black", "^22.0", "dev", "pyproject.toml"),
            Dependency("type-checker", "^1.0", "dev", "pyproject.toml"),
        ]
        info = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info(deps),
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoMerger.merge([info])

        assert result.dependencies is not None
        assert result.dependencies.dev_count == 3

    def test_counts_optional_dependencies_correctly(self) -> None:
        """Test that optional dependencies are counted correctly."""
        deps = [
            Dependency("extra-lib", "^1.0", "optional", "pyproject.toml"),
        ]
        info = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info(deps),
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoMerger.merge([info])

        assert result.dependencies is not None
        assert result.dependencies.optional_count == 1

    def test_total_count_equals_sum_of_categories(self) -> None:
        """Test that total count equals sum of all categories."""
        deps = [
            Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),
            Dependency("pytest", "^7.0", "dev", "pyproject.toml"),
            Dependency("extra-lib", "^1.0", "optional", "pyproject.toml"),
        ]
        info = ProjectFileInfo(
            name="project",
            dependencies=self._make_dep_info(deps),
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoMerger.merge([info])

        assert result.dependencies is not None
        total = (
            result.dependencies.prod_count
            + result.dependencies.dev_count
            + result.dependencies.optional_count
        )
        assert result.dependencies.total_count == total
