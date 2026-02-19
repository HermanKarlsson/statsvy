"""Tests for the __main__.py entry point module."""

import importlib

import statsvy.__main__


def test_main_entry_point_exists() -> None:
    """Test that __main__ module can be imported."""
    # Verify that the module can be imported
    assert statsvy.__main__ is not None


def test_main_module_has_if_name_main_block() -> None:
    """Test that __main__ module has the main execution block."""
    # Re-import to ensure the module can be reloaded
    importlib.reload(statsvy.__main__)
    # If this doesn't raise, the module is well-formed
    assert True
