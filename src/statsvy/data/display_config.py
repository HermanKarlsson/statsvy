"""Display configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisplayConfig:
    """Terminal display preferences."""

    truncate_paths: bool
    show_percentages: bool
