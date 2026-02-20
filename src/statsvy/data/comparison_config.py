"""Comparison configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ComparisonConfig:
    """Comparison and delta settings."""

    show_unchanged: bool
