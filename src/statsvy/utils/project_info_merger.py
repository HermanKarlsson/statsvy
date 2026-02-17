"""Project information merger for combining multiple config file results."""

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)


class ProjectInfoMerger:
    """Merges multiple ProjectFileInfo objects from different config files.

    When a project has multiple configuration files (e.g., both
    pyproject.toml and requirements.txt), this class combines them,
    detects conflicts, and aggregates the results.
    """

    @staticmethod
    def merge(infos: list[ProjectFileInfo]) -> ProjectFileInfo:
        """Merge multiple ProjectFileInfo objects into a single result.

        Combines all dependencies, detects version conflicts when the same
        package appears with different versions across files, and selects
        the project name from the first non-None source.

        Args:
            infos: List of ProjectFileInfo objects to merge.

        Returns:
            Merged ProjectFileInfo containing aggregated dependencies,
            combined source files, and detected conflicts.
        """
        if not infos:
            return ProjectFileInfo(name=None, dependencies=None, source_files=())

        if len(infos) == 1:
            return infos[0]

        # Extract project components
        name = ProjectInfoMerger._select_project_name(infos)
        all_dependencies, all_sources = ProjectInfoMerger._collect_all_deps(infos)
        conflicts = ProjectInfoMerger._detect_conflicts(all_dependencies)
        dep_info = ProjectInfoMerger._build_dep_info(
            all_dependencies, all_sources, conflicts
        )

        return ProjectFileInfo(
            name=name,
            dependencies=dep_info,
            source_files=tuple(sorted(all_sources)),
        )

    @staticmethod
    def _select_project_name(infos: list[ProjectFileInfo]) -> str | None:
        """Select first non-None project name from list.

        Args:
            infos: List of ProjectFileInfo objects.

        Returns:
            First non-None name or None if all are None.
        """
        for info in infos:
            if info.name:
                return info.name
        return None

    @staticmethod
    def _collect_all_deps(
        infos: list[ProjectFileInfo],
    ) -> tuple[list[Dependency], set[str]]:
        """Collect all dependencies and sources from ProjectFileInfo list.

        Args:
            infos: List of ProjectFileInfo objects.

        Returns:
            Tuple of (all dependencies list, set of all source files).
        """
        all_dependencies: list[Dependency] = []
        all_sources: set[str] = set()

        for info in infos:
            if info.dependencies:
                all_dependencies.extend(info.dependencies.dependencies)
                all_sources.update(info.dependencies.sources)
            all_sources.update(info.source_files)

        return all_dependencies, all_sources

    @staticmethod
    def _build_dep_info(
        all_dependencies: list[Dependency],
        all_sources: set[str],
        conflicts: list[str],
    ) -> DependencyInfo | None:
        """Build DependencyInfo from aggregated dependencies.

        Args:
            all_dependencies: List of all dependencies.
            all_sources: Set of all source files.
            conflicts: List of conflict descriptions.

        Returns:
            DependencyInfo object or None if no dependencies.
        """
        if not all_dependencies:
            return None

        prod_count = sum(1 for d in all_dependencies if d.category == "prod")
        dev_count = sum(1 for d in all_dependencies if d.category == "dev")
        optional_count = sum(1 for d in all_dependencies if d.category == "optional")

        return DependencyInfo(
            dependencies=tuple(all_dependencies),
            prod_count=prod_count,
            dev_count=dev_count,
            optional_count=optional_count,
            total_count=len(all_dependencies),
            sources=tuple(sorted(all_sources)),
            conflicts=tuple(conflicts),
        )

    @staticmethod
    def _detect_conflicts(dependencies: list[Dependency]) -> list[str]:
        """Detect version conflicts when same package appears in multiple files.

        Args:
            dependencies: List of all dependencies from all files.

        Returns:
            List of conflict descriptions.
        """
        deps_by_name = ProjectInfoMerger._group_deps_by_name(dependencies)
        conflicts: list[str] = []

        for name, deps in deps_by_name.items():
            conflict = ProjectInfoMerger._find_version_conflict(name, deps)
            if conflict:
                conflicts.append(conflict)

        return conflicts

    @staticmethod
    def _group_deps_by_name(
        dependencies: list[Dependency],
    ) -> dict[str, list[Dependency]]:
        """Group dependencies by package name.

        Args:
            dependencies: List of all dependencies.

        Returns:
            Dictionary mapping package names to list of Dependency objects.
        """
        deps_by_name: dict[str, list[Dependency]] = {}
        for dep in dependencies:
            if dep.name not in deps_by_name:
                deps_by_name[dep.name] = []
            deps_by_name[dep.name].append(dep)
        return deps_by_name

    @staticmethod
    def _find_version_conflict(name: str, deps: list[Dependency]) -> str | None:
        """Find version conflict for a specific package.

        Args:
            name: Package name.
            deps: List of Dependency objects for this package.

        Returns:
            Conflict description string or None if no conflict.
        """
        if len(deps) <= 1:
            return None

        versions_by_file: dict[str, set[str]] = {}
        for dep in deps:
            if dep.source_file not in versions_by_file:
                versions_by_file[dep.source_file] = set()
            versions_by_file[dep.source_file].add(dep.version)

        # Conflict only if multiple files with different versions
        if len(versions_by_file) <= 1:
            return None

        version_strs = ProjectInfoMerger._format_version_strings(versions_by_file)
        return f"{name}: {'; '.join(version_strs)}"

    @staticmethod
    def _format_version_strings(
        versions_by_file: dict[str, set[str]],
    ) -> list[str]:
        """Format version information for conflict message.

        Args:
            versions_by_file: Dict mapping file names to version sets.

        Returns:
            List of formatted version strings.
        """
        version_strs: list[str] = []
        for file_name, versions in sorted(versions_by_file.items()):
            version_list = ", ".join(sorted(versions))
            version_strs.append(f"{file_name} has {version_list}")
        return version_strs
