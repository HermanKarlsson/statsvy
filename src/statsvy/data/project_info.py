"""Project configuration and dependency information.

This module provides common data structures for project file information
and dependency analysis results. These structures represent extracted data
from project configuration files (pyproject.toml, package.json, etc.)
without any business logic.
"""

# Re-export for backward compatibility
from statsvy.data.dependency import Dependency
from statsvy.data.dependency_info import DependencyInfo
from statsvy.data.project_file_info import ProjectFileInfo

__all__ = ["Dependency", "DependencyInfo", "ProjectFileInfo"]
