"""Tests for LanguageDetector priority and precedence."""

from pathlib import Path

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorPriority:
    """Tests for LanguageDetector priority handling."""

    @staticmethod
    def get_detector() -> LanguageDetector:
        """Get detector with real language config."""
        config_path = Path(__file__).parent.parent.parent / "assets" / "languages.yml"
        return LanguageDetector(language_config_path=config_path)

    def test_filename_priority_over_extension(self) -> None:
        """Test that filename detection has priority over extension."""
        detector = self.get_detector()
        # Makefile should be detected as Makefile via filename matching
        result = detector.detect(Path("Makefile"))
        assert result == "Makefile"

    def test_first_matching_extension(self) -> None:
        """Test detection with extension from real config."""
        detector = self.get_detector()
        result = detector.detect(Path("file.md"))
        assert result == "Markdown"
