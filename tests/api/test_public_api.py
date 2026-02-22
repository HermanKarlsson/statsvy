"""Contract tests for the public programmatic API."""

import datetime
from dataclasses import replace
from pathlib import Path

import pytest

from statsvy.api import ApiComparisonResult, ApiScanResult, StatsvyApi
from statsvy.core.analyzer import Analyzer
from statsvy.core.comparison import ComparisonAnalyzer
from statsvy.core.formatter import Formatter
from statsvy.core.scanner import Scanner
from statsvy.data.config import Config
from statsvy.data.metrics import Metrics
from statsvy.data.scan_result import ScanResult


def test_scan_returns_api_scan_result(tmp_path: Path) -> None:
    """Scan should return the public API DTO with expected core fields."""
    project_dir = tmp_path / "sample"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")

    scan_result = StatsvyApi.scan(project_dir)

    assert isinstance(scan_result, ApiScanResult)
    assert scan_result.total_files >= 1
    assert scan_result.path == str(project_dir)
    assert isinstance(scan_result.lines_by_lang, dict)


def test_compare_returns_api_comparison_result(tmp_path: Path) -> None:
    """Compare should return public comparison DTO with deltas."""
    project_a = tmp_path / "project_a"
    project_b = tmp_path / "project_b"
    project_a.mkdir()
    project_b.mkdir()

    (project_a / "app.py").write_text("print('a')\n", encoding="utf-8")
    (project_b / "app.py").write_text("print('b')\nprint('c')\n", encoding="utf-8")

    result_a = StatsvyApi.scan(project_a)
    result_b = StatsvyApi.scan(project_b)
    comparison = StatsvyApi.compare(result_a, result_b)

    assert isinstance(comparison, ApiComparisonResult)
    assert "overall" in comparison.deltas


def test_format_result_json_for_scan(tmp_path: Path) -> None:
    """Formatting scan result as JSON should return a JSON payload."""
    project_dir = tmp_path / "json_scan"
    project_dir.mkdir()
    (project_dir / "script.py").write_text("print('x')\n", encoding="utf-8")

    result = StatsvyApi.scan(project_dir)
    output = StatsvyApi.format_result(result, output_format="json")

    assert output.strip().startswith("{")
    assert '"total_files"' in output


def test_format_result_json_for_comparison(tmp_path: Path) -> None:
    """Formatting comparison result as JSON should include comparison key."""
    project_a = tmp_path / "fmt_a"
    project_b = tmp_path / "fmt_b"
    project_a.mkdir()
    project_b.mkdir()

    (project_a / "alpha.py").write_text("x = 1\n", encoding="utf-8")
    (project_b / "beta.py").write_text("x = 1\ny = 2\n", encoding="utf-8")

    comparison = StatsvyApi.compare(
        StatsvyApi.scan(project_a),
        StatsvyApi.scan(project_b),
    )
    output = StatsvyApi.format_result(comparison, output_format="json")

    assert output.strip().startswith("{")
    assert '"comparison"' in output


def test_format_result_respects_config_default_format(tmp_path: Path) -> None:
    """Formatter should default to config.core.default_format when omitted."""
    project_dir = tmp_path / "default_format"
    project_dir.mkdir()
    (project_dir / "code.py").write_text("print('ok')\n", encoding="utf-8")

    config = Config.default()
    config = config.__class__(
        core=config.core.__class__(
            name=config.core.name,
            path=config.core.path,
            default_format="json",
            out_dir=config.core.out_dir,
            verbose=config.core.verbose,
            color=config.core.color,
            show_progress=False,
            performance=config.core.performance,
        ),
        scan=config.scan,
        language=config.language,
        storage=config.storage,
        git=config.git,
        display=config.display,
        comparison=config.comparison,
        dependencies=config.dependencies,
        files=config.files,
    )

    result = StatsvyApi.scan(project_dir, config=config)
    output = StatsvyApi.format_result(result, config=config)

    assert output.strip().startswith("{")


def test_scan_delegates_to_internal_scanner_and_analyzer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Public scan API should delegate to core Scanner and Analyzer."""
    project_dir = tmp_path / "wired"
    project_dir.mkdir()

    calls = {
        "scanner_scan": 0,
        "analyzer_analyze": 0,
    }

    def fake_scanner_scan(
        _self: object,
        _timeout_checker: object | None = None,
    ) -> ScanResult:
        calls["scanner_scan"] += 1
        return ScanResult(
            total_files=1,
            total_size_bytes=10,
            scanned_files=(project_dir / "sample.py",),
        )

    def fake_analyzer_analyze(
        _self: object,
        scan_result: ScanResult,
        _timeout_checker: object | None = None,
    ) -> Metrics:
        calls["analyzer_analyze"] += 1
        return Metrics(
            name="api-test",
            path=project_dir,
            timestamp=datetime.datetime.now(),
            total_files=scan_result.total_files,
            total_size_bytes=scan_result.total_size_bytes,
            total_size_kb=0,
            total_size_mb=0,
            lines_by_lang={"python": 1},
            comment_lines_by_lang={"python": 0},
            blank_lines_by_lang={"python": 0},
            lines_by_category={"code": 1, "comment": 0, "blank": 0},
            comment_lines=0,
            blank_lines=0,
            total_lines=1,
            dependencies=None,
        )

    def fake_project_scan(_self: object) -> None:
        return None

    monkeypatch.setattr("statsvy.core.scanner.Scanner.scan", fake_scanner_scan)
    monkeypatch.setattr("statsvy.core.analyzer.Analyzer.analyze", fake_analyzer_analyze)
    monkeypatch.setattr(
        "statsvy.core.project_scanner.ProjectScanner.scan",
        fake_project_scan,
    )

    result = StatsvyApi.scan(project_dir)

    assert isinstance(result, ApiScanResult)
    assert result.name == "api-test"
    assert calls["scanner_scan"] == 1
    assert calls["analyzer_analyze"] == 1


def test_scan_matches_internal_pipeline_contract(tmp_path: Path) -> None:
    """API scan should match results from direct internal scan/analyze flow."""
    project_dir = tmp_path / "parity"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (project_dir / "utils.py").write_text("x = 1\n", encoding="utf-8")

    config = Config.default()
    config = replace(
        config,
        core=replace(config.core, show_progress=False),
        dependencies=replace(config.dependencies, include_dependencies=False),
    )

    api_result = StatsvyApi.scan(project_dir, config=config)

    scanner = Scanner(
        project_dir,
        ignore=config.scan.ignore_patterns,
        no_gitignore=not config.scan.respect_gitignore,
        config=config,
    )
    scan_result = scanner.scan()
    analyzer = Analyzer(
        name=f"{Path.cwd()}/{project_dir.name}",
        path=project_dir,
        language_map_path=StatsvyApi._language_config_path(),
        custom_language_mapping=config.language.custom_language_mapping,
        config=config,
    )
    internal_metrics = analyzer.analyze(scan_result)

    assert api_result.total_files == internal_metrics.total_files
    assert api_result.total_size_bytes == internal_metrics.total_size_bytes
    assert api_result.total_lines == internal_metrics.total_lines
    assert api_result.lines_by_lang == dict(internal_metrics.lines_by_lang)
    assert api_result.comment_lines_by_lang == dict(
        internal_metrics.comment_lines_by_lang
    )
    assert api_result.blank_lines_by_lang == dict(internal_metrics.blank_lines_by_lang)


def test_compare_and_format_match_internal_modules(tmp_path: Path) -> None:
    """API compare/format should stay aligned with internal comparison formatter."""
    project_a = tmp_path / "internal_a"
    project_b = tmp_path / "internal_b"
    project_a.mkdir()
    project_b.mkdir()

    (project_a / "app.py").write_text("a = 1\n", encoding="utf-8")
    (project_b / "app.py").write_text("a = 1\nb = 2\n", encoding="utf-8")

    config = Config.default()
    config = replace(
        config,
        core=replace(config.core, show_progress=False),
        dependencies=replace(config.dependencies, include_dependencies=False),
        git=replace(config.git, enabled=False),
    )

    api_a = StatsvyApi.scan(project_a, config=config)
    api_b = StatsvyApi.scan(project_b, config=config)
    api_comparison = StatsvyApi.compare(api_a, api_b)

    scanner_a = Scanner(
        project_a,
        ignore=config.scan.ignore_patterns,
        no_gitignore=not config.scan.respect_gitignore,
        config=config,
    )
    scanner_b = Scanner(
        project_b,
        ignore=config.scan.ignore_patterns,
        no_gitignore=not config.scan.respect_gitignore,
        config=config,
    )
    analyzer_a = Analyzer(
        name=f"{Path.cwd()}/{project_a.name}",
        path=project_a,
        language_map_path=StatsvyApi._language_config_path(),
        custom_language_mapping=config.language.custom_language_mapping,
        config=config,
    )
    analyzer_b = Analyzer(
        name=f"{Path.cwd()}/{project_b.name}",
        path=project_b,
        language_map_path=StatsvyApi._language_config_path(),
        custom_language_mapping=config.language.custom_language_mapping,
        config=config,
    )

    metrics_a = analyzer_a.analyze(scanner_a.scan())
    metrics_b = analyzer_b.analyze(scanner_b.scan())
    internal_comparison = ComparisonAnalyzer.compare(metrics_a, metrics_b)

    assert api_comparison.deltas == internal_comparison.deltas

    api_json = StatsvyApi.format_result(
        api_comparison,
        output_format="json",
        config=config,
    )
    internal_json = Formatter.format(
        internal_comparison,
        "json",
        display_config=config.display,
        include_css=None,
    )
    assert api_json == internal_json
