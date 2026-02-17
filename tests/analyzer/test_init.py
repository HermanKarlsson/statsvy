"""Test suite for the Analyzer module initialization.

Tests verify that Analyzer correctly initializes with various parameters.
"""

import tempfile
from pathlib import Path

import pytest

from statsvy.core.analyzer import Analyzer


def _make_yaml(tmpdir: str, languages: dict[str, list[str]]) -> Path:
    """Write a minimal languages.yml to *tmpdir* and return its path.

    Args:
        tmpdir: Directory in which to create the file.
        languages: Mapping of language name to list of file extensions.

    Returns:
        Path to the written YAML file.
    """
    lines = []
    for lang, extensions in languages.items():
        lines.append(f"{lang}:")
        lines.append("  extensions:")
        for ext in extensions:
            lines.append(f'  - "{ext}"')
    yaml_path = Path(tmpdir) / "languages.yml"
    yaml_path.write_text("\n".join(lines) + "\n")
    return yaml_path


class TestAnalyzerInit:
    """Tests for Analyzer construction."""

    def test_can_be_instantiated_with_name_and_path(self) -> None:
        """Test that Analyzer can be created with only name and path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("project", Path(tmpdir))
            assert analyzer is not None

    def test_stores_name(self) -> None:
        """Test that Analyzer stores the provided name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("my_project", Path(tmpdir))
            assert analyzer.name == "my_project"

    def test_stores_path(self) -> None:
        """Test that Analyzer stores the provided path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            analyzer = Analyzer("proj", path)
            assert analyzer.path == path

    def test_initializes_language_detector(self) -> None:
        """Test that Analyzer creates a LanguageDetector instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("proj", Path(tmpdir))
            assert hasattr(analyzer, "language_detector")
            assert analyzer.language_detector is not None

    def test_analyze_method_exists_and_is_callable(self) -> None:
        """Test that Analyzer exposes a callable analyze() method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = Analyzer("proj", Path(tmpdir))
            assert callable(getattr(analyzer, "analyze", None))

    def test_raises_on_invalid_yaml_syntax(self) -> None:
        """Test that Analyzer raises ValueError when the YAML file is malformed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_yaml = Path(tmpdir) / "languages.yml"
            bad_yaml.write_text("Python:\n  extensions:\n  - [unclosed\n")
            with pytest.raises(ValueError, match="Failed to load language map"):
                Analyzer("proj", Path(tmpdir), language_map_path=bad_yaml)

    def test_handles_missing_language_config_gracefully(self) -> None:
        """Test that a nonexistent language map path does not raise on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent.yml"
            analyzer = Analyzer("proj", Path(tmpdir), language_map_path=nonexistent)
            assert analyzer is not None
