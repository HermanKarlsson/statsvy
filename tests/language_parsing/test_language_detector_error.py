"""Tests for LanguageDetector error handling."""

import tempfile
from pathlib import Path

import pytest
import yaml

from statsvy.language_parsing.language_detector import LanguageDetector


class TestLanguageDetectorErrorHandling:
    """Tests for LanguageDetector error handling."""

    def test_detect_language_malformed_yaml(self) -> None:
        """Test that detector handles malformed YAML gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "languages.yml"
            with open(config_file, "w") as f:
                f.write("invalid: yaml: content:")
            with pytest.raises(ValueError, match="Failed to load language map"):
                LanguageDetector(language_config_path=config_file)

    def test_detect_language_empty_yaml(self) -> None:
        """Test that detector handles empty YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "languages.yml"
            with open(config_file, "w") as f:
                f.write("")
            detector = LanguageDetector(language_config_path=config_file)
            result = detector.detect(Path("test.py"))
            assert result == "unknown"

    def test_detect_language_invalid_config_format(self) -> None:
        """Test that detector handles invalid config format gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "languages.yml"
            config = {"languages": {"Python": {"extensions": [".py"]}}}
            with open(config_file, "w") as f:
                yaml.dump(config, f)
            detector = LanguageDetector(language_config_path=config_file)
            # Should not crash with unknown config format
            result = detector.detect(Path("test.py"))
            assert result == "unknown"
