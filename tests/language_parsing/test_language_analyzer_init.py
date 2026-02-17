"""Tests for LanguageAnalyzer initialization."""

from statsvy.language_parsing.language_analyzer import LanguageAnalyzer


class TestLanguageAnalyzerInitialization:
    """Tests for LanguageAnalyzer initialization."""

    def test_init_creates_analyzer(
        self: "TestLanguageAnalyzerInitialization",
    ) -> None:
        """Initialize LanguageAnalyzer without arguments."""
        analyzer = LanguageAnalyzer()
        assert analyzer is not None

    def test_multiple_instances_independent(
        self: "TestLanguageAnalyzerInitialization",
    ) -> None:
        """Verify multiple analyzer instances are independent."""
        analyzer1 = LanguageAnalyzer()
        analyzer2 = LanguageAnalyzer()
        assert analyzer1 is not analyzer2
