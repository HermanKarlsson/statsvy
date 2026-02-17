"""Tests for LanguageDetector filename-based language detection."""

from pathlib import Path

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorFilenameDetection:
    """Tests for LanguageDetector filename-based detection."""

    @staticmethod
    def get_detector() -> LanguageDetector:
        """Get detector with real language config."""
        config_path = Path(__file__).parent.parent.parent / "assets" / "languages.yml"
        return LanguageDetector(language_config_path=config_path)

    def test_detect_language_by_filename(self) -> None:
        """Test detection by specific filename."""
        detector = self.get_detector()
        assert detector.detect(Path("Makefile")) == "Makefile"

    def test_detect_language_dockerfile(self) -> None:
        """Test detection of Dockerfile."""
        detector = self.get_detector()
        assert detector.detect(Path("Dockerfile")) == "Dockerfile"

    def test_detect_language_gemfile(self) -> None:
        """Test detection of Ruby Gemfile."""
        detector = self.get_detector()
        assert detector.detect(Path("Gemfile")) == "Ruby"

    def test_detect_language_filename_takes_precedence(self) -> None:
        """Test that filename detection works for mapped filenames."""
        detector = self.get_detector()
        assert detector.detect(Path("CMakeLists.txt")) == "CMake"
