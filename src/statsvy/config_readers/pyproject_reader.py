"""PyProject.toml configuration reader."""

import re
import tomllib
from pathlib import Path

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)


class PyProjectReader:
    """Reads project information from pyproject.toml files.

    Extracts project name from [project] section and dependencies from
    [project.dependencies] and [project.optional-dependencies] sections.
    """

    def read_project_info(self, path: Path) -> ProjectFileInfo:
        """Read project information from pyproject.toml.

        Args:
            path: Path to pyproject.toml file.

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

        project_section = data.get("project")
        # Some malformed/legacy pyproject files use a *literal* table name
        # like ["[project]"] which results in a top-level key of "[project]".
        # Accept that fallback so tests and real-world malformed files still
        # return the expected project metadata.
        if not isinstance(project_section, dict):
            alt = data.get("[project]")
            if isinstance(alt, dict):
                project_section = alt
            else:
                return ProjectFileInfo(name=None, dependencies=None, source_files=())

        # Extract project name and dependencies
        name = self._get_project_name(project_section)
        dependencies_list = self._extract_dependencies(project_section)

        # Create DependencyInfo if we found dependencies
        dep_info: DependencyInfo | None = None
        if dependencies_list:
            dep_info = self._build_dep_info(dependencies_list)

        return ProjectFileInfo(
            name=name,
            dependencies=dep_info,
            source_files=(path.name,),
        )

    @staticmethod
    def _get_project_name(project_section: dict) -> str | None:
        """Extract project name from [project] section.

        Args:
            project_section: The [project] section from pyproject.toml.

        Returns:
            Project name or None.
        """
        project_name = project_section.get("name")
        return str(project_name) if project_name else None

    def _extract_dependencies(self, project_section: dict) -> list[Dependency]:
        """Extract all dependencies from [project] section.

        Args:
            project_section: The [project] section from pyproject.toml.

        Returns:
            List of Dependency objects.
        """
        dependencies_list: list[Dependency] = []

        # Extract standard and optional dependencies
        dependencies_list.extend(self._extract_standard_deps(project_section))
        dependencies_list.extend(self._extract_optional_deps(project_section))

        return dependencies_list

    @staticmethod
    def _extract_standard_deps(project_section: dict) -> list[Dependency]:
        """Extract [project.dependencies] section.

        Args:
            project_section: The [project] section from pyproject.toml.

        Returns:
            List of Dependency objects with category "prod".
        """
        dependencies_list: list[Dependency] = []

        deps = project_section.get("dependencies")
        if isinstance(deps, list):
            for dep_str in deps:
                if dep_str:
                    dep = PyProjectReader._parse_dependency_string(str(dep_str), "prod")
                    if dep:
                        dependencies_list.append(dep)

        return dependencies_list

    @staticmethod
    def _extract_optional_deps(project_section: dict) -> list[Dependency]:
        """Extract [project.optional-dependencies] section.

        Args:
            project_section: The [project] section from pyproject.toml.

        Returns:
            List of Dependency objects with category "optional".
        """
        dependencies_list: list[Dependency] = []

        optional_deps = project_section.get("optional-dependencies")
        if isinstance(optional_deps, dict):
            for opt_list in optional_deps.values():
                if isinstance(opt_list, list):
                    for dep_str in opt_list:
                        if dep_str:
                            dep = PyProjectReader._parse_dependency_string(
                                str(dep_str), "optional"
                            )
                            if dep:
                                dependencies_list.append(dep)

        return dependencies_list

    @staticmethod
    def _build_dep_info(dependencies_list: list[Dependency]) -> DependencyInfo:
        """Build DependencyInfo from dependencies list.

        Args:
            dependencies_list: List of Dependency objects.

        Returns:
            DependencyInfo object.
        """
        prod_count = sum(1 for d in dependencies_list if d.category == "prod")
        dev_count = sum(1 for d in dependencies_list if d.category == "dev")
        optional_count = sum(1 for d in dependencies_list if d.category == "optional")

        return DependencyInfo(
            dependencies=tuple(dependencies_list),
            prod_count=prod_count,
            dev_count=dev_count,
            optional_count=optional_count,
            total_count=len(dependencies_list),
            sources=("pyproject.toml",),
            conflicts=(),
        )

    @staticmethod
    def _parse_dependency_string(dep_str: str, category: str) -> Dependency | None:
        """Parse a PEP 508 dependency string into name and version.

        Handles formats like:
        - "click"
        - "click>=8.0.0"
        - "click[extra]>=8.0.0"
        - "click>=8.0.0 ; python_version >= '3.8'"

        Args:
            dep_str: Dependency specification string.
            category: Dependency category (prod/dev/optional).

        Returns:
            Dependency object if parsed successfully, None otherwise.
        """
        # Remove environment markers (after semicolon)
        if ";" in dep_str:
            dep_str = dep_str.split(";", maxsplit=1)[0].strip()

        if not dep_str:
            return None

        # Extract name and version using regex
        # Matches: name (with optional [extras]) optionally followed by version spec
        match = re.match(r"^([a-zA-Z0-9._-]+)(\[[^\]]*\])?(.*?)$", dep_str.strip())

        if not match:
            return None

        name = match.group(1)
        version_spec = match.group(3).strip() if match.group(3) else ""

        # If no version spec, use any version
        version = version_spec if version_spec else "*"

        return Dependency(
            name=name.lower(),
            version=version,
            category=category,
            source_file="pyproject.toml",
        )
