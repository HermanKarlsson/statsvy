"""Tests for custom language mapping overrides."""

from pathlib import Path

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorCustomMapping:
    """Tests for LanguageDetector custom mapping behavior."""

    @staticmethod
    def get_detector(custom_mapping: dict[str, object]) -> LanguageDetector:
        """Create a detector with custom language mapping."""
        config_path = Path(__file__).parent.parent.parent / "assets" / "languages.yml"
        return LanguageDetector(
            language_config_path=config_path,
            custom_language_mapping=custom_mapping,
        )

    def test_custom_mapping_overrides_extension(self) -> None:
        """Custom mappings should override existing extensions."""
        custom_mapping = {
            "Docs": {
                "type": "markup",
                "extensions": [".md"],
            }
        }
        detector = self.get_detector(custom_mapping)
        assert detector.detect(Path("README.md")) == "Docs"

    def test_custom_mapping_adds_filename(self) -> None:
        """Custom mappings should support filename detection."""
        custom_mapping = {
            "BuildSpec": {
                "type": "data",
                "filenames": ["Buildfile"],
            }
        }
        detector = self.get_detector(custom_mapping)
        assert detector.detect(Path("Buildfile")) == "BuildSpec"

    def test_custom_mapping_sets_category(self) -> None:
        """Custom mappings should provide category types."""
        custom_mapping = {
            "Infra": {
                "type": "data",
                "extensions": [".infra"],
            }
        }
        detector = self.get_detector(custom_mapping)
        lang = detector.detect(Path("main.infra"))
        assert lang == "Infra"
        assert detector.get_category(lang) == "data"
