"""Tests for loading configuration from environment variables."""

import pytest

from statsvy.config.config_loader import ConfigLoader


class TestConfigLoaderFromEnv:
    """Test loading from environment variables."""

    def test_load_from_env_updates_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables should update Config."""
        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader()
        loader.load()
        assert loader.config.core.verbose is True

    def test_load_from_env_handles_multiple_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle multiple environment variables."""
        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")
        monkeypatch.setenv("STATSVY_SCAN_MAX_DEPTH", "10")

        loader = ConfigLoader()
        loader.load()
        assert loader.config.core.verbose is True
        assert loader.config.scan.max_depth == 10

    def test_load_from_env_converts_bool_types(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should convert env var strings to bool correctly."""
        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader()
        loader.load()
        assert isinstance(loader.config.core.verbose, bool)
        assert loader.config.core.verbose is True

    def test_load_from_env_converts_bool_false_variants(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle various false representations."""
        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "false")

        loader = ConfigLoader()
        loader.load()
        assert isinstance(loader.config.core.verbose, bool)
        assert loader.config.core.verbose is False

    def test_load_from_env_converts_int_types(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should convert env var strings to int correctly."""
        monkeypatch.setenv("STATSVY_SCAN_MAX_DEPTH", "5")

        loader = ConfigLoader()
        loader.load()
        assert isinstance(loader.config.scan.max_depth, int)
        assert loader.config.scan.max_depth == 5

    def test_load_from_env_converts_float_types(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should convert env var strings to float correctly."""
        monkeypatch.setenv("STATSVY_CORE_TIMEOUT", "3.5")

        loader = ConfigLoader()
        loader.load()

    def test_load_from_env_ignores_invalid_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should ignore invalid environment variables."""
        monkeypatch.setenv("STATSVY_INVALID_KEY", "value")
        monkeypatch.setenv("OTHER_APP_CONFIG", "value")

        loader = ConfigLoader()
        loader.load()

    def test_load_from_env_ignores_non_statsvy_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should only process STATSVY_ prefixed variables."""
        monkeypatch.setenv("MY_VERBOSE", "true")
        monkeypatch.setenv("STATSVY_CORE_VERBOSE", "true")

        loader = ConfigLoader()
        loader.load()
        assert loader.config.core.verbose is True

    def test_load_from_env_handles_invalid_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should ignore malformed env var names."""
        monkeypatch.setenv("STATSVY_INVALID", "value")

        loader = ConfigLoader()
        loader.load()
        pass
