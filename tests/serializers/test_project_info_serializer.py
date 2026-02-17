"""Test suite for project information serializer.

Tests verify that ProjectInfoSerializer correctly serializes and deserializes
project information structures to/from dictionary format.
"""

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)
from statsvy.serializers.project_info_serializer import ProjectInfoSerializer


class TestProjectInfoSerializerDependency:
    """Tests for Dependency serialization/deserialization."""

    def test_serializes_dependency_with_all_fields(self) -> None:
        """Test serializing dependency with all fields."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        result = ProjectInfoSerializer.serialize_dependency(dep)

        assert result["name"] == "click"
        assert result["version"] == ">=8.0.0"
        assert result["category"] == "prod"
        assert result["source_file"] == "pyproject.toml"

    def test_serialized_dependency_keys(self) -> None:
        """Test that serialized dependency has expected keys."""
        dep = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        result = ProjectInfoSerializer.serialize_dependency(dep)

        assert "name" in result
        assert "version" in result
        assert "category" in result
        assert "source_file" in result

    def test_deserializes_dependency_with_all_fields(self) -> None:
        """Test deserializing dependency with all fields."""
        data = {
            "name": "click",
            "version": ">=8.0.0",
            "category": "prod",
            "source_file": "pyproject.toml",
        }
        result = ProjectInfoSerializer.deserialize_dependency(data)

        assert result.name == "click"
        assert result.version == ">=8.0.0"
        assert result.category == "prod"
        assert result.source_file == "pyproject.toml"

    def test_deserialize_with_missing_fields_uses_defaults(self) -> None:
        """Test that missing fields use defaults during deserialization."""
        data = {"name": "click"}
        result = ProjectInfoSerializer.deserialize_dependency(data)

        assert result.name == "click"
        assert result.version == "*"
        assert result.category == "prod"
        assert result.source_file == "unknown"

    def test_roundtrip_dependency_serialization(self) -> None:
        """Test that dependency can be serialized and deserialized."""
        original = Dependency(
            name="click",
            version=">=8.0.0",
            category="prod",
            source_file="pyproject.toml",
        )
        serialized = ProjectInfoSerializer.serialize_dependency(original)
        deserialized = ProjectInfoSerializer.deserialize_dependency(serialized)

        assert deserialized == original

    def test_serializes_dev_dependency(self) -> None:
        """Test serializing dev dependency."""
        dep = Dependency(
            name="pytest",
            version="^7.0",
            category="dev",
            source_file="pyproject.toml",
        )
        result = ProjectInfoSerializer.serialize_dependency(dep)

        assert result["category"] == "dev"

    def test_serializes_optional_dependency(self) -> None:
        """Test serializing optional dependency."""
        dep = Dependency(
            name="extra-lib",
            version="^1.0",
            category="optional",
            source_file="pyproject.toml",
        )
        result = ProjectInfoSerializer.serialize_dependency(dep)

        assert result["category"] == "optional"


class TestProjectInfoSerializerDependencyInfo:
    """Tests for DependencyInfo serialization/deserialization."""

    def _make_dep_info(self) -> DependencyInfo:
        """Create sample DependencyInfo."""
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

    def test_serializes_dependency_info_with_all_fields(self) -> None:
        """Test serializing DependencyInfo with all fields."""
        info = self._make_dep_info()
        result = ProjectInfoSerializer.serialize_dependency_info(info)

        assert result["total_count"] == 2
        assert result["prod_count"] == 1
        assert result["dev_count"] == 1
        assert result["optional_count"] == 0
        assert result["sources"] == ["pyproject.toml"]
        assert result["conflicts"] == []
        assert len(result["dependencies"]) == 2

    def test_serialized_dependency_info_keys(self) -> None:
        """Test that serialized DependencyInfo has expected keys."""
        info = self._make_dep_info()
        result = ProjectInfoSerializer.serialize_dependency_info(info)

        assert "total_count" in result
        assert "prod_count" in result
        assert "dev_count" in result
        assert "optional_count" in result
        assert "sources" in result
        assert "conflicts" in result
        assert "dependencies" in result

    def test_deserializes_dependency_info_with_all_fields(self) -> None:
        """Test deserializing DependencyInfo with all fields."""
        data = {
            "total_count": 2,
            "prod_count": 1,
            "dev_count": 1,
            "optional_count": 0,
            "sources": ["pyproject.toml"],
            "conflicts": [],
            "dependencies": [
                {
                    "name": "click",
                    "version": ">=8.0.0",
                    "category": "prod",
                    "source_file": "pyproject.toml",
                },
                {
                    "name": "pytest",
                    "version": "^7.0",
                    "category": "dev",
                    "source_file": "pyproject.toml",
                },
            ],
        }
        result = ProjectInfoSerializer.deserialize_dependency_info(data)

        assert result.total_count == 2
        assert result.prod_count == 1
        assert result.dev_count == 1
        assert result.optional_count == 0
        assert len(result.dependencies) == 2

    def test_roundtrip_dependency_info_serialization(self) -> None:
        """Test that DependencyInfo can be serialized and deserialized."""
        original = self._make_dep_info()
        serialized = ProjectInfoSerializer.serialize_dependency_info(original)
        deserialized = ProjectInfoSerializer.deserialize_dependency_info(serialized)

        assert deserialized == original

    def test_deserialize_with_missing_fields_uses_defaults(self) -> None:
        """Test that missing fields use defaults during deserialization."""
        data = {
            "dependencies": [
                {
                    "name": "click",
                    "version": ">=8.0.0",
                    "category": "prod",
                    "source_file": "pyproject.toml",
                }
            ]
        }
        result = ProjectInfoSerializer.deserialize_dependency_info(data)

        assert result.prod_count == 0  # Default
        assert result.total_count == 0  # Default

    def test_handles_empty_dependencies(self) -> None:
        """Test handling empty dependencies list."""
        data = {
            "total_count": 0,
            "prod_count": 0,
            "dev_count": 0,
            "optional_count": 0,
            "sources": [],
            "conflicts": [],
            "dependencies": [],
        }
        result = ProjectInfoSerializer.deserialize_dependency_info(data)

        assert len(result.dependencies) == 0
        assert result.total_count == 0

    def test_handles_conflicts_in_serialization(self) -> None:
        """Test serialization of DependencyInfo with conflicts."""
        deps = (Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),)
        info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=0,
            optional_count=0,
            total_count=1,
            sources=("pyproject.toml",),
            conflicts=("click: file1 has >=8.0.0; file2 has >=9.0.0",),
        )
        result = ProjectInfoSerializer.serialize_dependency_info(info)

        assert len(result["conflicts"]) == 1


class TestProjectInfoSerializerProjectFileInfo:
    """Tests for ProjectFileInfo serialization/deserialization."""

    def _make_project_file_info(self) -> ProjectFileInfo:
        """Create sample ProjectFileInfo."""
        deps = (Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),)
        dep_info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=0,
            optional_count=0,
            total_count=1,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        return ProjectFileInfo(
            name="my-project",
            dependencies=dep_info,
            source_files=("pyproject.toml",),
        )

    def test_serializes_project_file_info_with_all_fields(self) -> None:
        """Test serializing ProjectFileInfo with all fields."""
        info = self._make_project_file_info()
        result = ProjectInfoSerializer.serialize_project_file_info(info)

        assert result["name"] == "my-project"
        assert result["source_files"] == ["pyproject.toml"]
        assert result["dependencies"] is not None

    def test_serialized_project_file_info_keys(self) -> None:
        """Test that serialized ProjectFileInfo has expected keys."""
        info = self._make_project_file_info()
        result = ProjectInfoSerializer.serialize_project_file_info(info)

        assert "name" in result
        assert "source_files" in result
        assert "dependencies" in result

    def test_deserializes_project_file_info_with_all_fields(self) -> None:
        """Test deserializing ProjectFileInfo with all fields."""
        data = {
            "name": "my-project",
            "source_files": ["pyproject.toml"],
            "dependencies": {
                "total_count": 1,
                "prod_count": 1,
                "dev_count": 0,
                "optional_count": 0,
                "sources": ["pyproject.toml"],
                "conflicts": [],
                "dependencies": [
                    {
                        "name": "click",
                        "version": ">=8.0.0",
                        "category": "prod",
                        "source_file": "pyproject.toml",
                    }
                ],
            },
        }
        result = ProjectInfoSerializer.deserialize_project_file_info(data)

        assert result.name == "my-project"
        assert result.dependencies is not None
        assert len(result.source_files) == 1

    def test_roundtrip_project_file_info_serialization(self) -> None:
        """Test that ProjectFileInfo can be serialized and deserialized."""
        original = self._make_project_file_info()
        serialized = ProjectInfoSerializer.serialize_project_file_info(original)
        deserialized = ProjectInfoSerializer.deserialize_project_file_info(serialized)

        assert deserialized == original

    def test_serializes_project_file_info_with_none_name(self) -> None:
        """Test serializing ProjectFileInfo with None name."""
        info = ProjectFileInfo(
            name=None,
            dependencies=None,
            source_files=("requirements.txt",),
        )
        result = ProjectInfoSerializer.serialize_project_file_info(info)

        assert result["name"] is None

    def test_serializes_project_file_info_with_none_dependencies(self) -> None:
        """Test serializing ProjectFileInfo with None dependencies."""
        info = ProjectFileInfo(
            name="my-project",
            dependencies=None,
            source_files=("pyproject.toml",),
        )
        result = ProjectInfoSerializer.serialize_project_file_info(info)

        assert result["dependencies"] is None

    def test_deserialize_with_none_name(self) -> None:
        """Test deserializing ProjectFileInfo with None name."""
        data = {
            "name": None,
            "source_files": ["requirements.txt"],
            "dependencies": None,
        }
        result = ProjectInfoSerializer.deserialize_project_file_info(data)

        assert result.name is None

    def test_deserialize_with_none_dependencies(self) -> None:
        """Test deserializing ProjectFileInfo with None dependencies."""
        data = {
            "name": "my-project",
            "source_files": ["pyproject.toml"],
            "dependencies": None,
        }
        result = ProjectInfoSerializer.deserialize_project_file_info(data)

        assert result.dependencies is None

    def test_deserialize_with_missing_fields_uses_defaults(self) -> None:
        """Test that missing fields use defaults during deserialization."""
        data = {"name": "my-project"}
        result = ProjectInfoSerializer.deserialize_project_file_info(data)

        assert result.name == "my-project"
        assert result.dependencies is None
        assert result.source_files == ()


class TestProjectInfoSerializerRoundtrips:
    """Tests for complete roundtrip scenarios."""

    def test_roundtrip_with_multiple_dependencies(self) -> None:
        """Test roundtrip with multiple dependencies."""
        deps = (
            Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),
            Dependency("requests", "^2.0", "prod", "pyproject.toml"),
            Dependency("pytest", "^7.0", "dev", "pyproject.toml"),
            Dependency("extra-lib", "^1.0", "optional", "pyproject.toml"),
        )
        dep_info = DependencyInfo(
            dependencies=deps,
            prod_count=2,
            dev_count=1,
            optional_count=1,
            total_count=4,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        original = ProjectFileInfo(
            name="my-project",
            dependencies=dep_info,
            source_files=("pyproject.toml",),
        )

        serialized = ProjectInfoSerializer.serialize_project_file_info(original)
        deserialized = ProjectInfoSerializer.deserialize_project_file_info(serialized)

        assert deserialized == original

    def test_roundtrip_with_conflicts(self) -> None:
        """Test roundtrip with conflicts."""
        deps = (Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),)
        dep_info = DependencyInfo(
            dependencies=deps,
            prod_count=1,
            dev_count=0,
            optional_count=0,
            total_count=1,
            sources=("pyproject.toml", "requirements.txt"),
            conflicts=(
                "click: pyproject.toml has >=8.0.0; requirements.txt has >=9.0.0",
            ),
        )
        original = ProjectFileInfo(
            name="my-project",
            dependencies=dep_info,
            source_files=("pyproject.toml", "requirements.txt"),
        )

        serialized = ProjectInfoSerializer.serialize_project_file_info(original)
        deserialized = ProjectInfoSerializer.deserialize_project_file_info(serialized)

        assert deserialized == original
        # Narrow type for the type checker: dependencies must be present in this case
        assert deserialized.dependencies is not None
        assert len(deserialized.dependencies.conflicts) == 1

    def test_roundtrip_minimal_info(self) -> None:
        """Test roundtrip with minimal info."""
        original = ProjectFileInfo(
            name=None,
            dependencies=None,
            source_files=(),
        )

        serialized = ProjectInfoSerializer.serialize_project_file_info(original)
        deserialized = ProjectInfoSerializer.deserialize_project_file_info(serialized)

        assert deserialized == original

    def test_roundtrip_preserves_category_counts(self) -> None:
        """Test that roundtrip preserves category counts."""
        deps = (
            Dependency("click", ">=8.0.0", "prod", "pyproject.toml"),
            Dependency("requests", "^2.0", "prod", "pyproject.toml"),
            Dependency("pytest", "^7.0", "dev", "pyproject.toml"),
        )
        dep_info = DependencyInfo(
            dependencies=deps,
            prod_count=2,
            dev_count=1,
            optional_count=0,
            total_count=3,
            sources=("pyproject.toml",),
            conflicts=(),
        )
        original = ProjectFileInfo(
            name="my-project",
            dependencies=dep_info,
            source_files=("pyproject.toml",),
        )

        serialized = ProjectInfoSerializer.serialize_project_file_info(original)
        deserialized = ProjectInfoSerializer.deserialize_project_file_info(serialized)

        # Narrow type for the type checker: dependencies must be present in this case
        assert deserialized.dependencies is not None
        assert deserialized.dependencies.prod_count == 2
        assert deserialized.dependencies.dev_count == 1
        assert deserialized.dependencies.optional_count == 0
