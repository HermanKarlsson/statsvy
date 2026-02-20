"""Storage configuration data model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Persistence settings."""

    auto_save: bool
