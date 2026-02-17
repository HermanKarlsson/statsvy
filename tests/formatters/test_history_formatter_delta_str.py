"""Tests for the delta_str helper function."""

from statsvy.utils.formatting import delta_str as _delta_str


class TestDeltaStr:
    """Tests for the :func:`_delta_str` helper."""

    def test_no_previous_returns_dash(self) -> None:
        """Should return ``-`` when ``previous`` is ``None``."""
        assert _delta_str(100, None) == "-"

    def test_positive_delta_uses_positive_color(self) -> None:
        """Should include ``+`` prefix and the positive colour tag."""
        result = _delta_str(110, 100)
        assert "+10" in result
        assert "spring_green3" in result

    def test_negative_delta_uses_red(self) -> None:
        """Should include ``red`` colour tag for negative deltas."""
        result = _delta_str(90, 100)
        assert "-10" in result
        assert "red" in result

    def test_zero_delta_uses_neutral_style(self) -> None:
        """Should return a neutral ``±0`` string when values are equal."""
        result = _delta_str(100, 100)
        assert "±0" in result

    def test_custom_positive_color(self) -> None:
        """Should respect a custom ``color_pos`` argument."""
        result = _delta_str(200, 100, color_pos="magenta")
        assert "magenta" in result

    def test_large_positive_delta_has_thousands_separator(self) -> None:
        """Large positive deltas should be formatted with commas."""
        result = _delta_str(11_000, 0)
        assert "11,000" in result

    def test_large_negative_delta_has_thousands_separator(self) -> None:
        """Large negative deltas should be formatted with commas."""
        result = _delta_str(0, 11_000)
        assert "-11,000" in result
