"""Tests for Analyzer I/O instrumentation."""

from pathlib import Path
from unittest.mock import MagicMock

from statsvy.core.analyzer import Analyzer
from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


class TestAnalyzerIOInstrumentation:
    """I/O instrumentation tests for Analyzer internals."""

    def test_count_file_lines_records_io(self, tmp_path: Path) -> None:
        """Ensure _count_file_lines records an I/O event when tracker enabled."""
        file_path = tmp_path / "sample.py"
        content = "line1\nline2\nline3\n"
        file_path.write_text(content)

        mock_tracker = MagicMock()
        mock_tracker.is_tracking_io.return_value = True

        analyzer = Analyzer(
            name="test",
            path=tmp_path,
            config=Config.default(),
            perf_tracker=mock_tracker,
        )

        count = analyzer._count_file_lines(file_path)

        assert count == 3
        assert mock_tracker.record_io.called
        recorded_args = mock_tracker.record_io.call_args[1]
        assert recorded_args.get("bytes_read", 0) >= len(content)
        assert recorded_args.get("elapsed_seconds", 0) >= 0

    def test_process_file_records_single_io(self, tmp_path: Path) -> None:
        """Verify _process_file records a single I/O event (read once)."""
        file_path = tmp_path / "sample2.py"
        content = "# comment\nprint(1)\n"
        file_path.write_text(content)

        mock_tracker = MagicMock()
        mock_tracker.is_tracking_io.return_value = True

        analyzer = Analyzer(
            name="test",
            path=tmp_path,
            config=Config.default(),
            perf_tracker=mock_tracker,
        )

        metrics_data: dict = {
            "lines_by_lang": {},
            "lines_by_category": {},
            "total_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "comment_lines_by_lang": {},
            "blank_lines_by_lang": {},
        }

        analyzer._process_file(file_path, metrics_data)

        # Only a single file read should be recorded (counting uses the read text)
        assert mock_tracker.record_io.call_count == 1

    def test_scan_then_analyze_records_io_only_during_scan(
        self, tmp_path: Path
    ) -> None:
        """When Scanner pre-reads files, Analyzer should not re-record I/O."""
        file_path = tmp_path / "sample3.py"
        content = "print(1)\nprint(2)\n"
        file_path.write_text(content)

        mock_tracker = MagicMock()
        mock_tracker.is_tracking_io.return_value = True

        scanner = Scanner(
            path=tmp_path,
            no_gitignore=True,
            config=Config.default(),
            perf_tracker=mock_tracker,
        )
        scan_result = scanner.scan()

        calls_after_scan = mock_tracker.record_io.call_count
        assert calls_after_scan >= 1

        # Analyzer must reuse ScanResult.file_contents and not add further I/O
        analyzer = Analyzer(
            name="test",
            path=tmp_path,
            config=Config.default(),
            perf_tracker=mock_tracker,
        )
        analyzer.analyze(scan_result)

        assert mock_tracker.record_io.call_count == calls_after_scan
