"""Git configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GitConfig:
    """Git integration settings."""

    enabled: bool
    include_stats: bool
    include_branches: tuple[str, ...]
    detect_authors: bool
    show_contributors: bool
    max_contributors: int
