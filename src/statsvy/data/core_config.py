"""Core configuration data model."""

from dataclasses import dataclass

from statsvy.data.performance_config import PerformanceConfig


@dataclass(frozen=True, slots=True)
class CoreConfig:
    """Core application settings."""

    name: str
    path: str
    default_format: str
    out_dir: str
    verbose: bool
    color: bool
    show_progress: bool
    performance: PerformanceConfig
