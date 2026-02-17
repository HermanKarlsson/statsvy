"""Tests for basic language analyzer functionality."""

from pathlib import Path

from statsvy.language_parsing.language_analyzer import LanguageAnalyzer


class TestAnalysisBasic:
    """Tests for basic analysis functionality."""

    def test_analyze_python_no_comments_no_blanks(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze Python file with no comments and no blank lines."""
        file_path = tmp_path / "test.py"
        code = "x = 1\ny = 2\nprint(x + y)"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert isinstance(comment_lines, int)
        assert isinstance(blank_lines, int)
        assert comment_lines == 0
        assert blank_lines == 0

    def test_analyze_python_with_comments(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze Python file with comments."""
        file_path = tmp_path / "test.py"
        code = "# This is a comment\nx = 1\n# Another comment\ny = 2"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert comment_lines == 2
        assert blank_lines == 0

    def test_analyze_python_with_blank_lines(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze Python file with blank lines."""
        file_path = tmp_path / "test.py"
        code = "x = 1\n\ny = 2\n\n"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert comment_lines == 0
        assert blank_lines == 2

    def test_analyze_python_with_comments_and_blanks(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze Python file with both comments and blank lines."""
        file_path = tmp_path / "test.py"
        code = "# Comment\n\nx = 1\n\n# Another comment\ny = 2"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert comment_lines == 2
        assert blank_lines == 2

    def test_analyze_java_with_comments(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze Java file with single line comments."""
        file_path = tmp_path / "Test.java"
        code = "// Single line comment\nint x = 1;\nint y = 2;"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert comment_lines >= 1
        assert blank_lines >= 0

    def test_analyze_go_with_comments(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze Go file with comments."""
        file_path = tmp_path / "main.go"
        code = "// Comment\npackage main\n// Another comment\nfunc main() {}"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert comment_lines >= 1
        assert blank_lines >= 0

    def test_analyze_javascript_with_comments(
        self: "TestAnalysisBasic",
        tmp_path: Path,
    ) -> None:
        """Analyze JavaScript file with comments."""
        file_path = tmp_path / "script.js"
        code = "// Comment\nconst x = 1;\n// Another\nconst y = 2;"
        file_path.write_text(code)
        analyzer = LanguageAnalyzer()
        comment_lines, blank_lines = analyzer.analyze(file_path, code)

        assert comment_lines >= 1
        assert blank_lines >= 0
