"""Tests for the __main__.py entry point module."""

import importlib

import statsvy.__main__


class TestMainEntryPoint:
    """Tests for the module entry-point (`__main__`)."""

    def test_main_entry_point_exists(self) -> None:
        """Module can be imported."""
        # Verify that the module can be imported
        assert statsvy.__main__ is not None

    def test_main_module_has_if_name_main_block(self) -> None:
        """Re-importing the module must not raise."""
        importlib.reload(statsvy.__main__)
        assert True
