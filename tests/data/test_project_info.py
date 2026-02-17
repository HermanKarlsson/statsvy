"""Test suite for project information data structures.

Tests verify that immutable dataclasses maintain data integrity and
cannot be accidentally modified after creation.
"""

from dataclasses import FrozenInstanceError

import pytest

from statsvy.data.project_info import Dependency, DependencyInfo, ProjectFileInfo


class TestDependency:
    """Tests for Dependency immutable dataclass."""

    def test_creates_dependency_with_all_fields(self) -> None:
        """Test that Dependency is created with all fields."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        assert dep.name == "click"
        assert dep.version == ">=8.0.0"
        assert dep.category == "prod"
        assert dep.source_file == "pyproject.toml"

    def test_is_immutable_cannot_modify_name(self) -> None:
        """Test that Dependency is frozen and cannot be modified."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        with pytest.raises(FrozenInstanceError):
            dep.name = "modified"  # type: ignore[misc]

    def test_is_immutable_cannot_modify_version(self) -> None:
        """Test that Dependency version cannot be modified."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        with pytest.raises(FrozenInstanceError):
            dep.version = "1.0.0"  # type: ignore[misc]

    def test_is_immutable_cannot_modify_category(self) -> None:
        """Test that Dependency category cannot be modified."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        with pytest.raises(FrozenInstanceError):
            dep.category = "dev"  # type: ignore[misc]

    def test_is_immutable_cannot_modify_source_file(self) -> None:
        """Test that Dependency source_file cannot be modified."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        with pytest.raises(FrozenInstanceError):
            dep.source_file = "requirements.txt"  # type: ignore[misc]

    def test_dependency_with_dev_category(self) -> None:
        """Test Dependency can have dev category."""
        dep = Dependency(
            name="pytest",
            version="^7.0.0",
            category="dev",
            source_file="pyproject.toml",
        )
        assert dep.category == "dev"

    def test_dependency_with_optional_category(self) -> None:
        """Test Dependency can have optional category."""
        dep = Dependency(
            name="extra-lib",
            version="~1.2.3",
            category="optional",
            source_file="pyproject.toml",
        )
        assert dep.category == "optional"

    def test_dependency_with_wildcard_version(self) -> None:
        """Test Dependency can have wildcard version."""
        dep = Dependency(
            name="somepackage",
            version="*",
            category="prod",
            source_file="requirements.txt",
        )
        assert dep.version == "*"

    def test_dependency_equality(self) -> None:
        """Test that identical Dependencies are equal."""
        dep1 = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        dep2 = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        assert dep1 == dep2

    def test_dependency_inequality(self) -> None:
        """Test that different Dependencies are not equal."""
        dep1 = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        dep2 = Dependency(
            name="click",
            version=">=9.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        assert dep1 != dep2


class TestDependencyInfo:
    """Tests for DependencyInfo immutable dataclass."""

    def _make_dependencies(self) -> tuple[Dependency, ...]:
        """Create sample dependencies for testing."""
        return (
            Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),
            Dependency("pytest", "^7.0", "dev", "pyproject.toml"),
        )

    def test_creates_dependency_info_with_all_fields(self) -> None:
        """Test that DependencyInfo is created with all fields."""
        deps = self._make_dependencies()
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        assert info.prod_count == 1
        assert info.dev_count == 1
        assert info.optional_count == 0
        assert info.total_count == 2
        assert len(info.dependencies) == 2

    def test_is_immutable_cannot_modify_dependencies(self) -> None:
        """Test that DependencyInfo dependencies tuple cannot be modified."""
        deps = self._make_dependencies()
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.dependencies = ()  # type: ignore[misc]

    def test_is_immutable_cannot_modify_counts(self) -> None:
        """Test that DependencyInfo counts cannot be modified."""
        deps = self._make_dependencies()
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.prod_count = 10  # type: ignore[misc]

    def test_is_immutable_cannot_modify_sources(self) -> None:
        """Test that DependencyInfo sources cannot be modified."""
        deps = self._make_dependencies()
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.sources = ()  # type: ignore[misc]

    def test_is_immutable_cannot_modify_conflicts(self) -> None:
        """Test that DependencyInfo conflicts cannot be modified."""
        deps = self._make_dependencies()
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.conflicts = ("conflict",)  # type: ignore[misc]

    def test_handles_multiple_sources(self) -> None:
        """Test DependencyInfo with multiple source files."""
        deps = self._make_dependencies()
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml", "requirements.txt"),
            conflicts=(),
        )
        assert len(info.sources) == 2
        assert "pyproject.toml" in info.sources
        assert "requirements.txt" in info.sources

    def test_handles_conflicts(self) -> None:
        """Test DependencyInfo can contain conflicts."""
        deps = self._make_dependencies()
        conflict_msg = "click: pyproject.toml has >=8.0.0; requirements.txt has >=9.0.0"
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml", "requirements.txt"),
            conflicts=(conflict_msg,),
        )
        assert len(info.conflicts) == 1
        assert conflict_msg in info.conflicts

    def test_zero_dependencies(self) -> None:
        """Test DependencyInfo with no dependencies."""
        info = DependencyInfo(
            dependencies=(),
            prod_count=0,
            dev_count=0,
            optional_count=0,
            total_count=0,
            sources=(),
            conflicts=(),
        )
        assert len(info.dependencies) == 0
        assert info.total_count == 0


class TestProjectFileInfo:
    """Tests for ProjectFileInfo immutable dataclass."""

    def _make_dep_info(self) -> DependencyInfo:
        """Create sample DependencyInfo for testing."""
        deps = (
            Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),
            Dependency("pytest", "^7.0", "dev", "pyproject.toml"),
        )
        return DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=1,
            optional_count=0,
            total_count=2,
            sources=("pyproject.toml",),
            conflicts=(),
        )

    def test_creates_project_file_info_with_all_fields(self) -> None:
        """Test that ProjectFileInfo is created with all fields."""
        dep_info = self._make_dep_info()
        info = ProjectFileInfo(
            name="my-project",
            dependencies=dep_info,
            source_files=("pyproject.toml",),
        )
        assert info.name == "my-project"
        assert info.dependencies is not None
        assert len(info.source_files) == 1

    def test_creates_project_file_info_with_none_dependencies(self) -> None:
        """Test ProjectFileInfo can have None dependencies."""
        info = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        assert info.name == "my-project"
        assert info.dependencies is None

    def test_creates_project_file_info_with_none_name(self) -> None:
        """Test ProjectFileInfo can have None name."""
        dep_info = self._make_dep_info()
        info = ProjectFileInfo(
            name=None,
            dependencies=dep_info,
            source_files=("requirements.txt",),
        )
        assert info.name is None
        assert info.dependencies is not None

    def test_is_immutable_cannot_modify_name(self) -> None:
        """Test that ProjectFileInfo name cannot be modified."""
        info = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.name = "new-name"  # type: ignore[misc]

    def test_is_immutable_cannot_modify_dependencies(self) -> None:
        """Test that ProjectFileInfo dependencies cannot be modified."""
        info = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.dependencies = self._make_dep_info()  # type: ignore[misc]

    def test_is_immutable_cannot_modify_source_files(self) -> None:
        """Test that ProjectFileInfo source_files cannot be modified."""
        info = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        with pytest.raises(FrozenInstanceError):
            info.source_files = ()  # type: ignore[misc]

    def test_multiple_source_files(self) -> None:
        """Test ProjectFileInfo with multiple source files."""
        info = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml", "requirements.txt", "Cargo.toml"),
        )
        assert len(info.source_files) == 3
        assert "pyproject.toml" in info.source_files
        assert "requirements.txt" in info.source_files
        assert "Cargo.toml" in info.source_files

    def test_equality_identical_instances(self) -> None:
        """Test that identical ProjectFileInfo instances are equal."""
        info1 = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        assert info1 == info2

    def test_inequality_different_names(self) -> None:
        """Test that ProjectFileInfo with different names are not equal."""
        info1 = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        info2 = ProjectFileInfo(
            name="other-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        assert info1 != info2
