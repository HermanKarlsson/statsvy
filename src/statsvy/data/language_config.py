"""Language configuration data model."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LanguageConfig:
    """Language detection and line-counting settings."""

    custom_language_mapping: Mapping[str, Any]
    exclude_languages: tuple[str, ...]
    min_lines_threshold: int
    count_comments: bool
    count_blank_lines: bool
    count_docstrings: bool
