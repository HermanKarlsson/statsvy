"""Cargo.toml configuration reader."""

import tomllib
from pathlib import Path

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)


class CargoTomlReader:
    """Reads project information from Cargo.toml files.

    Extracts project name from [package] section and dependencies from
    [dependencies] and [dev-dependencies] sections. Handles both simple
    and detailed dependency specifications.
    """

    def read_project_info(self, path: Path) -> ProjectFileInfo:
        """Read project information from Cargo.toml.

        Args:
            path: Path to Cargo.toml file.

        Returns:
            ProjectFileInfo with name and dependencies extracted.

        Raises:
            FileNotFoundError: If file does not exist.
            tomllib.TOMLDecodeError: If TOML file is malformed.
        """
        with open(path, mode="rb") as f:
            data = tomllib.load(f)

        if not isinstance(data, dict):
            return ProjectFileInfo(name=None, dependencies=None, source_files=())

        # Extract project name
        name: str | None = None
        package_section = data.get("package")
        if isinstance(package_section, dict):
            package_name = package_section.get("name")
            if package_name:
                name = str(package_name)

        # Extract dependencies from all categories
        dependencies_list: list[Dependency] = []
        sources: list[str] = []
        self._add_prod_deps(data, dependencies_list, sources)
        self._add_dev_deps(data, dependencies_list, sources)

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
        """Add production dependencies from [dependencies] section."""
        prod_deps = data.get("dependencies")
        if isinstance(prod_deps, dict):
            sources.append("Cargo.toml")
            for dep_name, dep_spec in prod_deps.items():
                version = CargoTomlReader._extract_version(dep_spec)
                dep = Dependency(
                    name=dep_name.lower(),
                    version=version,
                    category="prod",
                    source_file="Cargo.toml",
                )
                dependencies_list.append(dep)

    @staticmethod
    def _add_dev_deps(
        data: dict, dependencies_list: list[Dependency], sources: list[str]
    ) -> None:
        """Add development dependencies from [dev-dependencies] section."""
        dev_deps = data.get("dev-dependencies")
        if isinstance(dev_deps, dict):
            if "Cargo.toml" not in sources:
                sources.append("Cargo.toml")
            for dep_name, dep_spec in dev_deps.items():
                version = CargoTomlReader._extract_version(dep_spec)
                dep = Dependency(
                    name=dep_name.lower(),
                    version=version,
                    category="dev",
                    source_file="Cargo.toml",
                )
                dependencies_list.append(dep)

    @staticmethod
    def _extract_version(dep_spec: str | dict | list) -> str:
        """Extract version specification from Cargo dependency format.

        Handles:
        - Simple string: "1.0"
        - Dict: {version = "1.0", features = [...]}
        - List: Should not occur normally

        Args:
            dep_spec: Dependency specification from TOML.

        Returns:
            Version string, or "*" if not found.
        """
        if isinstance(dep_spec, str):
            return dep_spec
        elif isinstance(dep_spec, dict):
            version = dep_spec.get("version")
            if version:
                return str(version)
        return "*"
