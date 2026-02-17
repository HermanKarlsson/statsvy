"""Tests for binary_extensions configuration merging."""

from pathlib import Path

from statsvy.config.config_loader import ConfigLoader


class TestBinaryExtensionsMerging:
    """Test that binary_extensions merges with defaults instead of replacing."""

    def test_binary_extensions_default_values(self) -> None:
        """Test that default binary_extensions are loaded."""
        loader = ConfigLoader()
        default_extensions = loader.config.scan.binary_extensions

        assert ".exe" in default_extensions
        assert ".dll" in default_extensions
        assert ".jpg" in default_extensions
        assert ".pyc" in default_extensions

    def test_binary_extensions_merge_with_defaults(self, tmp_path: Path) -> None:
        """Test that config file binary_extensions merge with defaults."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.scan]
binary_extensions = [".bin", ".dat"]
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        extensions = loader.config.scan.binary_extensions

        # Should have defaults
        assert ".exe" in extensions
        assert ".dll" in extensions
        assert ".jpg" in extensions
        assert ".pyc" in extensions

        # Should also have new ones
        assert ".bin" in extensions
        assert ".dat" in extensions

    def test_binary_extensions_no_duplicates(self, tmp_path: Path) -> None:
        """Test that duplicate extensions are not added."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.scan]
binary_extensions = [".exe", ".dll", ".custom"]
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        extensions = loader.config.scan.binary_extensions

        # Count occurrences of .exe
        exe_count = sum(1 for ext in extensions if ext == ".exe")
        assert exe_count == 1

        # Should have custom one
        assert ".custom" in extensions

    def test_binary_extensions_preserves_order(self, tmp_path: Path) -> None:
        """Test that extension order is preserved."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.scan]
binary_extensions = [".aaa", ".bbb", ".ccc"]
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        extensions = loader.config.scan.binary_extensions

        # Find positions of new extensions
        aaa_index = extensions.index(".aaa")
        bbb_index = extensions.index(".bbb")
        ccc_index = extensions.index(".ccc")

        # Should maintain order
        assert aaa_index < bbb_index < ccc_index

    def test_binary_extensions_cli_override_merges(self) -> None:
        """Test that CLI override also merges instead of replacing."""
        loader = ConfigLoader()
        loader.update_from_cli(scan_binary_extensions=[".test1", ".test2"])

        extensions = loader.config.scan.binary_extensions

        # Should have defaults
        assert ".exe" in extensions
        assert ".jpg" in extensions

        # Should also have CLI-provided ones
        assert ".test1" in extensions
        assert ".test2" in extensions

    def test_binary_extensions_multiple_merges(self, tmp_path: Path) -> None:
        """Test that multiple config sources all merge together."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.scan]
binary_extensions = [".config"]
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()
        loader.update_from_cli(scan_binary_extensions=[".cli"])

        extensions = loader.config.scan.binary_extensions

        # Should have all: defaults + file + cli
        assert ".exe" in extensions  # default
        assert ".config" in extensions  # from file
        assert ".cli" in extensions  # from CLI

    def test_binary_extensions_empty_config_value(self, tmp_path: Path) -> None:
        """Test that empty binary_extensions in config keeps defaults."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.statsvy.scan]
binary_extensions = []
""")

        loader = ConfigLoader(config_path=config_file)
        loader.load()

        extensions = loader.config.scan.binary_extensions

        # Should still have defaults
        assert ".exe" in extensions
        assert ".dll" in extensions
