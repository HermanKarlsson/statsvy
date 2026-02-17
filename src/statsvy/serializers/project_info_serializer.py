"""Serializer for project information structures."""

from typing import Any

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)


class ProjectInfoSerializer:
    """Handles serialization/deserialization of project information.

    Converts between ProjectFileInfo, DependencyInfo, and Dependency
    objects and their dictionary representations for JSON storage.
    """

    @staticmethod
    def serialize_dependency(dep: Dependency) -> dict[str, str]:
        """Serialize a single Dependency to a dictionary.

        Args:
            dep: Dependency object to serialize.

        Returns:
            Dictionary representation with name, version, category, source_file.
        """
        return {
            "name": dep.name,
            "version": dep.version,
            "category": dep.category,
            "source_file": dep.source_file,
        }

    @staticmethod
    def deserialize_dependency(data: dict[str, str]) -> Dependency:
        """Deserialize a Dependency from a dictionary.

        Args:
            data: Dictionary with dependency fields.

        Returns:
            Reconstructed Dependency object.
        """
        return Dependency(
            name=data.get("name", ""),
            version=data.get("version", "*"),
            category=data.get("category", "prod"),
            source_file=data.get("source_file", "unknown"),
        )

    @staticmethod
    def serialize_dependency_info(info: DependencyInfo) -> dict[str, Any]:
        """Serialize DependencyInfo to a dictionary.

        Args:
            info: DependencyInfo object to serialize.

        Returns:
            Dictionary with aggregated dependency information.
        """
        return {
            "total_count": info.total_count,
            "prod_count": info.prod_count,
            "dev_count": info.dev_count,
            "optional_count": info.optional_count,
            "sources": list(info.sources),
            "conflicts": list(info.conflicts),
            "dependencies": [
                ProjectInfoSerializer.serialize_dependency(dep)
                for dep in info.dependencies
            ],
        }

    @staticmethod
    def deserialize_dependency_info(data: dict[str, Any]) -> DependencyInfo:
        """Deserialize DependencyInfo from a dictionary.

        Args:
            data: Dictionary with dependency information.

        Returns:
            Reconstructed DependencyInfo object.
        """
        deps = [
            ProjectInfoSerializer.deserialize_dependency(dep_dict)
            for dep_dict in data.get("dependencies", [])
        ]

        return DependencyInfo(
            dependencies=tuple(deps),
            prod_count=data.get("prod_count", 0),
            dev_count=data.get("dev_count", 0),
            optional_count=data.get("optional_count", 0),
            total_count=data.get("total_count", 0),
            sources=tuple(data.get("sources", [])),
            conflicts=tuple(data.get("conflicts", [])),
        )

    @staticmethod
    def serialize_project_file_info(info: ProjectFileInfo) -> dict[str, Any]:
        """Serialize ProjectFileInfo to a dictionary.

        Args:
            info: ProjectFileInfo object to serialize.

        Returns:
            Dictionary representation for JSON storage.
        """
        return {
            "name": info.name,
            "source_files": list(info.source_files),
            "dependencies": (
                ProjectInfoSerializer.serialize_dependency_info(info.dependencies)
                if info.dependencies
                else None
            ),
        }

    @staticmethod
    def deserialize_project_file_info(
        data: dict[str, Any],
    ) -> ProjectFileInfo:
        """Deserialize ProjectFileInfo from a dictionary.

        Args:
            data: Dictionary with project file information.

        Returns:
            Reconstructed ProjectFileInfo object.
        """
        dep_data = data.get("dependencies")
        dependencies = (
            ProjectInfoSerializer.deserialize_dependency_info(dep_data)
            if dep_data
            else None
        )

        return ProjectFileInfo(
            name=data.get("name"),
            dependencies=dependencies,
            source_files=tuple(data.get("source_files", [])),
        )
