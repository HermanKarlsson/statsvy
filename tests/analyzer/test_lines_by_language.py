"""Test suite for the Analyzer module lines by language.

Tests verify lines_by_lang grouping and accumulation.
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


class TestLinesByLanguage:
    """Tests for lines_by_lang grouping and accumulation."""

    def test_groups_lines_by_detected_language(self) -> None:
        """Test that lines_by_lang separates counts per language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml = _make_yaml(tmpdir, {"Python": [".py"], "JavaScript": [".js"]})
            py = Path(tmpdir) / "app.py"
            py.write_text("def start():\n    pass\n")
            js = Path(tmpdir) / "app.js"
            js.write_text("console.log('app');\n")
            result = Analyzer("t", Path(tmpdir), language_map_path=yaml).analyze(
                _make_scan_result([py, js])
            )
            assert result.lines_by_lang.get("Python") == 2
            assert result.lines_by_lang.get("JavaScript") == 1

    def test_accumulates_lines_for_same_language_across_files(self) -> None:
        """Test that multiple files of the same language have their lines summed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml = _make_yaml(tmpdir, {"Python": [".py"]})
            f1 = Path(tmpdir) / "a.py"
            f1.write_text("def f():\n    pass\n")
            f2 = Path(tmpdir) / "b.py"
            f2.write_text("def g():\n    pass\n")
            result = Analyzer("t", Path(tmpdir), language_map_path=yaml).analyze(
                _make_scan_result([f1, f2])
            )
            assert result.lines_by_lang.get("Python") == 4

    def test_unknown_extension_marked_as_unknown(self) -> None:
        """Test that files with unrecognized extensions are labelled 'unknown'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml = _make_yaml(tmpdir, {"Python": [".py"]})
            f = Path(tmpdir) / "data.xyz"
            f.write_text("line1\nline2\n")
            result = Analyzer("t", Path(tmpdir), language_map_path=yaml).analyze(
                _make_scan_result([f])
            )
            assert result.lines_by_lang.get("unknown") == 2

    def test_missing_language_map_marks_all_as_unknown(self) -> None:
        """Test that all files are labelled 'unknown' when no language map exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "script.py"
            f.write_text("code\n")
            result = Analyzer(
                "t", Path(tmpdir), language_map_path=Path(tmpdir) / "nope.yml"
            ).analyze(_make_scan_result([f]))
            assert result.lines_by_lang.get("unknown") == 1

    def test_detects_multiple_languages_in_one_analysis(self) -> None:
        """Test detection of three or more distinct languages in a single run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml = _make_yaml(
                tmpdir,
                {"Python": [".py"], "JavaScript": [".js"], "JSON": [".json"]},
            )
            py = Path(tmpdir) / "app.py"
            py.write_text("def start():\n    pass\n")
            js = Path(tmpdir) / "app.js"
            js.write_text("console.log('app');\n")
            json_file = Path(tmpdir) / "config.json"
            json_file.write_text('{\n  "key": "value"\n}\n')
            result = Analyzer("t", Path(tmpdir), language_map_path=yaml).analyze(
                _make_scan_result([py, js, json_file])
            )
            assert result.lines_by_lang.get("Python") == 2
            assert result.lines_by_lang.get("JavaScript") == 1
            assert result.lines_by_lang.get("JSON") == 3

    def test_total_lines_equals_sum_of_lines_by_lang(self) -> None:
        """Test that total_lines equals the sum of all values in lines_by_lang."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml = _make_yaml(tmpdir, {"Python": [".py"], "JavaScript": [".js"]})
            py = Path(tmpdir) / "a.py"
            py.write_text("x\ny\nz\n")
            js = Path(tmpdir) / "b.js"
            js.write_text("a\nb\n")
            result = Analyzer("t", Path(tmpdir), language_map_path=yaml).analyze(
                _make_scan_result([py, js])
            )
            assert result.total_lines == sum(result.lines_by_lang.values())
