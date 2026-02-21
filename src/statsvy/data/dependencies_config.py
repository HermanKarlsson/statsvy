"""Dependencies configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DependenciesConfig:
    """Dependency analysis settings.

    Attributes:
        include_dependencies: Whether to analyze dependencies (default True).
        exclude_dev_dependencies: Whether to exclude dev dependencies from analysis.
    """

    include_dependencies: bool = True
    exclude_dev_dependencies: bool = False
