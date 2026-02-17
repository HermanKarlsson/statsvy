"""Test suite for the Analyzer module integration.

End-to-end integration tests covering the full Analyzer workflow.
"""

import tempfile
from pathlib import Path

from statsvy.core.analyzer import Analyzer
from statsvy.data.scan_result import ScanResult


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


def _make_scan_result(files: list[Path], size: int = 0) -> ScanResult:
    """Build a ScanResult from a list of file paths.

    Args:
        files: List of Path objects to include.
        size: Total size in bytes to report.

    Returns:
        A ScanResult populated with the given files.
    """
    return ScanResult(
        total_files=len(files),
        total_size_bytes=size,
        scanned_files=tuple(files),
    )


class TestAnalyzerIntegration:
    """End-to-end integration tests covering the full Analyzer workflow."""

    def test_full_workflow_with_mixed_languages(self) -> None:
        """Test a complete analysis with Python, JavaScript, Markdown, and JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml = _make_yaml(
                tmpdir,
                {
                    "Python": [".py"],
                    "JavaScript": [".js"],
                    "Markdown": [".md"],
                    "JSON": [".json"],
                },
            )
            py = Path(tmpdir) / "main.py"
            py.write_text("import os\nimport sys\n\ndef main():\n    pass\n")
            js = Path(tmpdir) / "index.js"
            js.write_text(
                "const express = require('express');\nconst app = express();\n"
            )
            md = Path(tmpdir) / "README.md"
            md.write_text("# Project\n\nDescription.\n\n## Features\n")
            json_f = Path(tmpdir) / "config.json"
            json_f.write_text('{\n  "name": "app",\n  "version": "1.0"\n}\n')

            analyzer = Analyzer("full_project", Path(tmpdir), language_map_path=yaml)
            result = analyzer.analyze(
                ScanResult(
                    total_files=4,
                    total_size_bytes=5000,
                    scanned_files=(py, js, md, json_f),
                )
            )

            assert result.name == "full_project"
            assert result.total_files == 4
            assert result.total_lines == 16
            assert result.lines_by_lang["Python"] == 5
            assert result.lines_by_lang["JavaScript"] == 2
            assert result.lines_by_lang["Markdown"] == 5
            assert result.lines_by_lang["JSON"] == 4
            assert result.total_size_bytes == 5000
