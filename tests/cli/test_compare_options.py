"""Tests for the CompareOptions dataclass in the CLI package."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from statsvy.cli.compare_options import CompareOptions


def test_compare_options_fields_and_immutability(tmp_path: Path) -> None:
    """Ensure fields are set correctly and the dataclass is frozen/slotted."""
    out_file = tmp_path / "out.md"

    opts = CompareOptions(
        project1="/repo/a",
        project2="/repo/b",
        format="md",
        output=out_file,
        verbose=True,
        no_color=False,
    )

    assert opts.project1 == "/repo/a"
    assert opts.project2 == "/repo/b"
    assert opts.format == "md"
    assert opts.output == out_file
    assert isinstance(opts.output, Path)
    assert opts.verbose is True
    assert opts.no_color is False

    # dataclass is frozen -> assignment should raise FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        opts.project1 = "x"  # type: ignore[misc]

    # dataclass uses slots -> instance should not have a __dict__
    with pytest.raises(AttributeError):
        _ = opts.__dict__
