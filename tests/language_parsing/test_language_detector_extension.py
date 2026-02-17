"""Tests for LanguageDetector extension-based language detection."""

from pathlib import Path

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorExtensionDetection:
    """Tests for LanguageDetector extension-based detection."""

    @staticmethod
    def get_detector() -> LanguageDetector:
        """Get detector with real language config."""
        config_path = Path(__file__).parent.parent.parent / "assets" / "languages.yml"
        return LanguageDetector(language_config_path=config_path)

    def test_detect_language_python_file(self) -> None:
        """Test detection of Python files."""
        detector = self.get_detector()
        assert detector.detect(Path("test.py")) == "Python"

    def test_detect_language_javascript_file(self) -> None:
        """Test detection of JavaScript files."""
        detector = self.get_detector()
        assert detector.detect(Path("script.js")) == "JavaScript"

    def test_detect_language_multiple_extensions(self) -> None:
        """Test detection with multiple extensions for same language."""
        detector = self.get_detector()
        assert detector.detect(Path("program.c")) == "C"
        assert detector.detect(Path("header.h")) == "Objective-C"

    def test_detect_language_case_insensitive(self) -> None:
        """Test that extension detection is case-insensitive."""
        detector = self.get_detector()
        assert detector.detect(Path("test.PY")) == "Python"
        assert detector.detect(Path("test.Py")) == "Python"

    def test_detect_language_unknown_extension(self) -> None:
        """Test detection of unknown extension returns unknown."""
        detector = self.get_detector()
        assert detector.detect(Path("test.unknown")) == "unknown"

    def test_detect_language_no_extension(self) -> None:
        """Test detection of file with no extension."""
        detector = self.get_detector()
        assert detector.detect(Path("Makefile")) == "Makefile"

    def test_detect_language_dot_file(self) -> None:
        """Test detection of dot file without extension."""
        detector = self.get_detector()
        result = detector.detect(Path(".gitignore"))
        assert result == "Ignore List"
