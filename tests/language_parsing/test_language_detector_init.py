"""Tests for LanguageDetector initialization and configuration."""

from pathlib import Path

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorInit:
    """Tests for LanguageDetector initialization."""

    def test_detector_can_be_instantiated(self) -> None:
        """Test that LanguageDetector can be created."""
        detector = LanguageDetector()
        assert detector is not None

    def test_detector_with_real_config(self) -> None:
        """Test that LanguageDetector works with real config."""
        config_path = Path(__file__).parent.parent.parent / "assets" / "languages.yml"
        detector = LanguageDetector(language_config_path=config_path)
        assert len(detector.extension_to_lang) > 0
        assert len(detector.filename_to_lang) >= 0

    def test_detector_with_nonexistent_config_file(self) -> None:
        """Test that LanguageDetector handles missing config gracefully."""
        nonexistent_yaml = Path("/nonexistent/path/languages.yml")
        detector = LanguageDetector(language_config_path=nonexistent_yaml)
        assert detector.extension_to_lang == {}
        assert detector.filename_to_lang == {}
