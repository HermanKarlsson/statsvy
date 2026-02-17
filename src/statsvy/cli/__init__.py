"""CLI command orchestration and utilities.

This package contains command orchestrators and CLI-specific helpers
that coordinate multiple components to handle user commands.
"""

# Re-export main for backwards compatibility with tests
from statsvy.cli_main import main

__all__ = ["main"]
