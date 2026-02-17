"""Requirements.txt configuration reader."""

from pathlib import Path

from statsvy.data.project_info import (
    Dependency,
    DependencyInfo,
    ProjectFileInfo,
)


class RequirementsTxtReader:
    """Reads dependency information from requirements.txt files.

    Parses standard pip requirements.txt format and extracts dependencies.
    Note: requirements.txt files do not contain project name information.
    """

    def read_project_info(self, path: Path) -> ProjectFileInfo:
        """Read dependencies from requirements.txt.

        Args:
            path: Path to requirements.txt file.

        Returns:
            ProjectFileInfo with dependencies extracted. Name will be None
            as requirements.txt files do not contain project name.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        dependencies_list: list[Dependency] = []

        with open(path, encoding="utf-8") as f:
            for line in f:
                cleaned_line = line.strip()

                # Skip empty lines and comments
                if not cleaned_line or cleaned_line.startswith("#"):
                    continue

                # Remove inline comments
                if "#" in cleaned_line:
                    cleaned_line = cleaned_line.split("#")[0].strip()

                if not cleaned_line:
                    continue

                # Parse dependency line
                dep = self._parse_requirement_line(cleaned_line)
                if dep:
                    dependencies_list.append(dep)

        # Create DependencyInfo if we found dependencies
        dep_info: DependencyInfo | None = None
        if dependencies_list:
            # All requirements are considered production dependencies
            prod_count = len(dependencies_list)

            dep_info = DependencyInfo(
                dependencies=tuple(dependencies_list),
                prod_count=prod_count,
                dev_count=0,
                optional_count=0,
                total_count=len(dependencies_list),
                sources=("requirements.txt",),
                conflicts=(),
            )

        return ProjectFileInfo(
            name=None,
            dependencies=dep_info,
            source_files=(path.name,),
        )

    @staticmethod
    def _parse_requirement_line(line: str) -> Dependency | None:
        """Parse a single requirements.txt line into a Dependency.

        Handles formats like:
        - "click"
        - "click==8.0.0"
        - "click>=8.0.0,<9.0.0"
        - "click[extra]==8.0.0"

        Args:
            line: Single requirement line.

        Returns:
            Dependency object if parsed successfully, None otherwise.
        """
        if not line:
            return None

        # Remove extras (parts in brackets)
        if "[" in line:
            line = (
                line.split("[", maxsplit=1)[0] + line.split("]", 1)[1]
                if "]" in line
                else line
            )
            line = line.replace("]", "")

        # Extract name and version
        # Operators: ==, >=, <=, >, <, ~=, !=
        for op in ("==", ">=", "<=", "~=", ">", "<", "!="):
            if op in line:
                parts = line.split(op, 1)
                name = parts[0].strip()
                version = op + parts[1].strip() if parts[1] else op

                return Dependency(
                    name=name.lower(),
                    version=version,
                    category="prod",
                    source_file="requirements.txt",
                )

        # No version specification
        return Dependency(
            name=line.lower(),
            version="*",
            category="prod",
            source_file="requirements.txt",
        )
