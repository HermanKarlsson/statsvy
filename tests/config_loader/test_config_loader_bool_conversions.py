"""Tests for boolean conversion from environment variables."""

import pytest

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderBoolConversions:
    """Test boolean conversion from environment variables."""

    def test_bool_conversion_true_variants(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should convert various true representations."""
        for true_val in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            monkeypatch.setenv("STATSVY_CORE_VERBOSE", true_val)
            loader = ConfigLoader()
            loader.load()
            assert loader.config.core.verbose is True

    def test_bool_conversion_false_variants(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should convert non-true representations as false."""
        for false_val in ["false", "0", "no", "off", "anything"]:
            monkeypatch.setenv("STATSVY_CORE_VERBOSE", false_val)
            loader = ConfigLoader()
            loader.load()
            assert loader.config.core.verbose is False
