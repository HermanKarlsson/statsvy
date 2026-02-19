"""Tests verifying Analyzer reuses pre-read contents supplied in ScanResult."""

from pathlib import Path
from unittest.mock import MagicMock

from statsvy.core.analyzer import Analyzer
from statsvy.data.config import Config
from statsvy.data.scan_result import ScanResult


def test_analyzer_uses_scan_result_file_contents_to_avoid_io(tmp_path: Path) -> None:
    """When ScanResult contains file text, Analyzer must not re-read the file."""
    f = tmp_path / "sample.py"
    content = "# comment\nprint(1)\n"
    f.write_text(content)

    scan_result = ScanResult(
        total_files=1,
        total_size_bytes=int(f.stat().st_size),
        scanned_files=(f,),
        file_contents={f: content},
    )

    mock_tracker = MagicMock()
    mock_tracker.is_tracking_io.return_value = True

    analyzer = Analyzer(
        name="test", path=tmp_path, config=Config.default(), perf_tracker=mock_tracker
    )

    metrics = analyzer.analyze(scan_result)

    # Analyzer should not have performed any I/O when text was provided
    assert mock_tracker.record_io.call_count == 0
    # Metrics still computed correctly
    assert metrics.total_lines >= 2
