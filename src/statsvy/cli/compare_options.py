"""Options container for the compare command."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CompareOptions:
    """Container for compare command options to reduce function arity.

    Attributes:
        project1: Path to the first project directory.
        project2: Path to the second project directory.
        format: Output format (table, json, md, markdown).
        output: Path to save output file.
        verbose: Enable verbose output.
        no_color: Disable colored output.
    """

    project1: str
    project2: str
    format: str | None
    output: Path | None
    verbose: bool
    no_color: bool
    no_css: bool
