"""Package.json configuration reader."""

import json
from pathlib import Path

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)


class PackageJsonReader:
    """Reads project information from package.json files.

    Extracts project name and dependencies from Node.js package.json,
    separating production and development dependencies.
    """

    def read_project_info(self, path: Path) -> ProjectFileInfo:
        """Read project information from package.json.

        Args:
            path: Path to package.json file.

        Returns:
            ProjectFileInfo with name and dependencies extracted.

        Raises:
            FileNotFoundError: If file does not exist.
            json.JSONDecodeError: If JSON file is malformed.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return ProjectFileInfo(name=None, dependencies=None, source_files=())

        # Extract project name
        name: str | None = None
        project_name = data.get("name")
        if project_name:
            name = str(project_name)

        # Extract dependencies from all categories
        dependencies_list: list[Dependency] = []
        sources: list[str] = []
        self._add_prod_deps(data, dependencies_list, sources)
        self._add_dev_deps(data, dependencies_list, sources)
        self._add_optional_deps(data, dependencies_list, sources)

        # Create DependencyInfo if we found dependencies
        dep_info: DependencyInfo | None = None
        if dependencies_list:
            prod_count = sum(1 for d in dependencies_list if d.category == "prod")
            dev_count = sum(1 for d in dependencies_list if d.category == "dev")
            optional_count = sum(
                1 for d in dependencies_list if d.category == "optional"
            )

            dep_info = DependencyInfo(
                dependencies=tuple(dependencies_list),
                prod_count=prod_count,
                dev_count=dev_count,
                optional_count=optional_count,
                total_count=len(dependencies_list),
                sources=tuple(sources),
                conflicts=(),
            )

        return ProjectFileInfo(
            name=name,
            dependencies=dep_info,
            source_files=(path.name,),
        )

    @staticmethod
    def _add_prod_deps(
        data: dict, dependencies_list: list[Dependency], sources: list[str]
    ) -> None:
        """Add production dependencies."""
        prod_deps = data.get("dependencies")
        if isinstance(prod_deps, dict):
            sources.append("package.json")
            for dep_name, dep_version in prod_deps.items():
                dep = Dependency(
                    name=dep_name.lower(),
                    version=str(dep_version),
                    category="prod",
                    source_file="package.json",
                )
                dependencies_list.append(dep)

    @staticmethod
    def _add_dev_deps(
        data: dict, dependencies_list: list[Dependency], sources: list[str]
    ) -> None:
        """Add development dependencies."""
        dev_deps = data.get("devDependencies")
        if isinstance(dev_deps, dict):
            if "package.json" not in sources:
                sources.append("package.json")
            for dep_name, dep_version in dev_deps.items():
                dep = Dependency(
                    name=dep_name.lower(),
                    version=str(dep_version),
                    category="dev",
                    source_file="package.json",
                )
                dependencies_list.append(dep)

    @staticmethod
    def _add_optional_deps(
        data: dict, dependencies_list: list[Dependency], sources: list[str]
    ) -> None:
        """Add optional dependencies."""
        optional_deps = data.get("optionalDependencies")
        if isinstance(optional_deps, dict):
            if "package.json" not in sources:
                sources.append("package.json")
            for dep_name, dep_version in optional_deps.items():
                dep = Dependency(
                    name=dep_name.lower(),
                    version=str(dep_version),
                    category="optional",
                    source_file="package.json",
                )
                dependencies_list.append(dep)
