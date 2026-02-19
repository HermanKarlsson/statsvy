"""Tests for Analyzer behaviour when duplicate files are present.

Verifies scanner detects duplicates and Analyzer skips them during analysis.
"""

from dataclasses import replace
from pathlib import Path

from statsvy.core.analyzer import Analyzer
from statsvy.core.scanner import Scanner
from statsvy.data.config import Config


class TestDuplicateSkipping:
    """Ensure Analyzer skips duplicate files reported by Scanner."""

    def test_analyzer_skips_duplicate_files(self, tmp_path: Path) -> None:
        """Analyzer should ignore files that scanner flagged as duplicates.

        The scanner will detect duplicates using size+hash; the analyzer must not
        include duplicate files when computing line counts.
        """
        # create two identical files and one unique file
        a = tmp_path / "one.py"
        b = tmp_path / "two.py"
        c = tmp_path / "three.py"
        a.write_text('print("x")\n')
        b.write_text('print("x")\n')
        c.write_text('print("y")\n')

        base_cfg = Config.default()
        files_cfg = replace(base_cfg.files, duplicate_threshold_bytes=1)
        cfg = replace(base_cfg, files=files_cfg)

        scanner = Scanner(tmp_path, config=cfg)
        scan_result = scanner.scan()

        # verify scanner detected exactly one duplicate (order not guaranteed)
        assert tuple(scan_result.duplicate_files)
        assert len(scan_result.duplicate_files) == 1
        assert scan_result.duplicate_files[0] in {a, b}

        analyzer = Analyzer("test", tmp_path, config=Config.default())
        metrics = analyzer.analyze(scan_result)

        # only two unique files should contribute to lines (a and c)
        assert metrics.total_lines == 2
        # languages should count lines from only the unique files
        assert sum(metrics.lines_by_lang.values()) == 2
