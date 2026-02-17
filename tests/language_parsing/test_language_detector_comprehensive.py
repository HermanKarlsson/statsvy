"""Comprehensive integration tests for LanguageDetector."""

from pathlib import Path

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorComprehensive:
    """Comprehensive tests for LanguageDetector integration."""

    def test_detector_with_real_language_config(self) -> None:
        """Test detector with realistic language configuration."""
        config_path = Path(__file__).parent.parent.parent / "assets" / "languages.yml"
        detector = LanguageDetector(language_config_path=config_path)
        assert detector.detect(Path("main.py")) == "Python"
        assert detector.detect(Path("app.js")) == "JavaScript"
        assert detector.detect(Path("script.mts")) == "TypeScript"
        assert detector.detect(Path("Gemfile")) == "Ruby"
        assert detector.detect(Path("Makefile")) == "Makefile"
