"""Tests for language analyzer and detector edge cases."""

from pathlib import Path

from pygments.lexers import PythonLexer

from statsvy.language_parsing.language_analyzer import LanguageAnalyzer
from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageAnalyzerCoverage:
    """Test edge cases in language analyzer."""

    def test_analyze_file_with_comments_and_blank_lines(self) -> None:
        """Test analyze method counts comments and blank lines."""
        analyzer = LanguageAnalyzer()

        code = """# This is a comment
def foo():
    # Another comment
    pass

# Last comment
"""
        result = analyzer.analyze(Path("test.py"), code)

        # Should return tuple of (blank_lines, comment_lines)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_count_blank_lines_with_empty_string(self) -> None:
        """Test _count_blank_lines with empty code."""
        analyzer = LanguageAnalyzer()

        result = analyzer._count_blank_lines("")

        assert result == 0

    def test_count_blank_lines_with_only_blanks(self) -> None:
        """Test _count_blank_lines with only blank lines."""
        analyzer = LanguageAnalyzer()

        result = analyzer._count_blank_lines("\n\n\n")

        assert result == 3

    def test_count_blank_lines_with_whitespace_only_lines(self) -> None:
        """Test _count_blank_lines counts whitespace-only lines."""
        analyzer = LanguageAnalyzer()

        code = "  \n  \n  "
        result = analyzer._count_blank_lines(code)

        # Whitespace-only lines should be counted as blank
        assert result >= 2

    def test_count_comment_lines_with_python_code(self) -> None:
        """Test _count_comment_lines with python lexer."""
        analyzer = LanguageAnalyzer()
        lexer = PythonLexer()

        # Test with no comments
        result = analyzer._count_comment_lines("x = 1", lexer)
        assert result == 0

        # Test with single line comment
        result = analyzer._count_comment_lines("# comment\nx = 1", lexer)
        assert result >= 1


class TestLanguageDetectorCoverage:
    """Test edge cases in language detector."""

    def test_detect_with_unknown_extension(self) -> None:
        """Test detect with unknown file extension."""
        detector = LanguageDetector()

        result = detector.detect(Path("file.unknownext"))

        assert result == "unknown"

    def test_detect_with_no_extension(self) -> None:
        """Test detect with file that has no extension."""
        detector = LanguageDetector()

        result = detector.detect(Path("filename_no_ext"))

        assert result == "unknown"

    def test_detect_with_known_extension(self) -> None:
        """Test detect with known extension."""
        detector = LanguageDetector()

        result = detector.detect(Path("script.py"))

        assert isinstance(result, str)

    def test_detect_with_filename_only(self) -> None:
        """Test detect with special filename detection."""
        detector = LanguageDetector()

        result = detector.detect(Path("Makefile"))

        # Should detect or return unknown
        assert isinstance(result, str)

    def test_get_category_with_known_language(self) -> None:
        """Test get_category with known language."""
        detector = LanguageDetector()

        result = detector.get_category("python")

        assert isinstance(result, str)

    def test_get_category_with_unknown_language(self) -> None:
        """Test get_category with unknown language."""
        detector = LanguageDetector()

        result = detector.get_category("nonexistent_language")

        assert result == "unknown"

    def test_process_extensions_with_valid_extensions(self) -> None:
        """Test _process_extensions with valid language extensions."""
        detector = LanguageDetector()
        extension_to_lang = {}

        info = {"extensions": [".py", ".pyw"]}

        detector._process_extensions(info, "python", extension_to_lang)

        assert extension_to_lang.get(".py") == "python"
        assert extension_to_lang.get(".pyw") == "python"

    def test_process_extensions_with_no_extensions(self) -> None:
        """Test _process_extensions with missing extensions key."""
        detector = LanguageDetector()
        extension_to_lang = {}

        info = {}

        # Should not raise
        detector._process_extensions(info, "language", extension_to_lang)

        assert len(extension_to_lang) == 0

    def test_process_filenames_with_valid_filenames(self) -> None:
        """Test _process_filenames with valid language filenames."""
        detector = LanguageDetector()
        filename_to_lang = {}

        info = {"filenames": ["Makefile", "makefile"]}

        detector._process_filenames(info, "makefile", filename_to_lang)

        assert filename_to_lang.get("Makefile") == "makefile"
        assert filename_to_lang.get("makefile") == "makefile"

    def test_process_filenames_with_no_filenames(self) -> None:
        """Test _process_filenames with missing filenames key."""
        detector = LanguageDetector()
        filename_to_lang = {}

        info = {}

        # Should not raise
        detector._process_filenames(info, "language", filename_to_lang)

        assert len(filename_to_lang) == 0

    def test_process_category_with_valid_category(self) -> None:
        """Test _process_category with valid language category."""
        detector = LanguageDetector()
        lang_to_category = {}

        info = {"type": "compiled"}

        detector._process_category(info, "golang", lang_to_category)

        assert lang_to_category.get("golang") == "compiled"

    def test_process_category_with_no_category(self) -> None:
        """Test _process_category with missing category key defaults to unknown."""
        detector = LanguageDetector()
        lang_to_category = {}

        info = {}

        # Should not raise and should default to "unknown"
        detector._process_category(info, "language", lang_to_category)

        assert lang_to_category.get("language") == "unknown"

    def test_detect_returns_string(self) -> None:
        """Test detect always returns a string."""
        detector = LanguageDetector()

        result = detector.detect(Path("test.xyz"))

        assert isinstance(result, str)
