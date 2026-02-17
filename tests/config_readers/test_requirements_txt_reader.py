"""Test suite for requirements.txt configuration reader.

Tests verify that RequirementsTxtReader correctly extracts dependencies
from requirements.txt files in various formats.
"""

from pathlib import Path

import pytest

from statsvy.config_readers.requirements_txt_reader import RequirementsTxtReader


@pytest.fixture()
def reader() -> RequirementsTxtReader:
    """Provide a RequirementsTxtReader instance."""
    return RequirementsTxtReader()


class TestRequirementsTxtReaderBasics:
    """Tests for basic RequirementsTxtReader functionality."""

    def test_reads_single_dependency(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test reading a single dependency."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_reads_multiple_dependencies(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test reading multiple dependencies."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\nrequests\npytest^7.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 3

    def test_returns_no_name(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that requirements.txt returns None for name."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.name is None

    def test_returns_none_dependencies_for_empty_file(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that empty file returns None dependencies."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("")
        result = reader.read_project_info(req_file)
        assert result.dependencies is None


class TestRequirementsTxtReaderErrorHandling:
    """Tests for error handling."""

    def test_raises_on_file_not_found(self, reader: RequirementsTxtReader) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            reader.read_project_info(Path("/nonexistent/path/requirements.txt"))

    def test_handles_permission_error(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that permission errors are raised."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n")
        req_file.chmod(0o000)
        try:
            with pytest.raises(PermissionError):
                reader.read_project_info(req_file)
        finally:
            req_file.chmod(0o644)


class TestRequirementsTxtReaderDependencyParsing:
    """Tests for dependency parsing."""

    def test_parses_dependency_name_only(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing dependency name without version."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "*"

    def test_parses_dependency_with_equals_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with == operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click==8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "==8.0.0"

    def test_parses_dependency_with_greater_than_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with > operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == ">8.0.0"

    def test_parses_dependency_with_gte_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with >= operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == ">=8.0.0"

    def test_parses_dependency_with_lt_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with < operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click<9.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "<9.0.0"

    def test_parses_dependency_with_lte_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with <= operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click<=9.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "<=9.0.0"

    def test_parses_dependency_with_tilde_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with ~= operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click~=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "~=8.0.0"

    def test_parses_dependency_with_not_equals_version(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing with != operator."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click!=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == "!=8.0.0"

    def test_parses_complex_version_spec(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing complex version specification."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0,<9.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert ">=8.0.0" in dep.version

    def test_parses_dependency_with_extras(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test parsing dependency with extras."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests[security]>=2.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "requests"
        assert dep.version == ">=2.0.0"


class TestRequirementsTxtReaderComments:
    """Tests for comment handling."""

    def test_skips_comment_lines(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that comment lines are skipped."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("# This is a comment\nclick>=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_skips_inline_comments(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that inline comments are removed."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0  # Popular CLI library\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"
        assert dep.version == ">=8.0.0"

    def test_handles_mixed_comments_and_deps(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling mixed comments and dependencies."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            """# Production dependencies
click>=8.0.0  # CLI framework
requests  # HTTP library
# End of file
"""
        )
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 2


class TestRequirementsTxtReaderWhitespace:
    """Tests for whitespace handling."""

    def test_skips_empty_lines(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that empty lines are skipped."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n\n\nrequests\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 2

    def test_handles_leading_whitespace(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling of leading whitespace."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("  click>=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_handles_trailing_whitespace(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling of trailing whitespace."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0  \n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 1

    def test_handles_mixed_whitespace(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling of mixed leading/trailing whitespace."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("  click>=8.0.0  \n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        dep = result.dependencies.dependencies[0]
        assert dep.name == "click"


class TestRequirementsTxtReaderDependencyCategories:
    """Tests for dependency categorization."""

    def test_all_dependencies_are_production(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that all dependencies are categorized as production."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\nrequests\npytest\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.prod_count == 3
        assert result.dependencies.dev_count == 0
        assert result.dependencies.optional_count == 0

    def test_source_file_is_requirements_txt(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that source_file is set to requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n")
        result = reader.read_project_info(req_file)
        assert result.source_files == ("requirements.txt",)


class TestRequirementsTxtReaderEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_many_dependencies(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling of many dependencies."""
        req_file = tmp_path / "requirements.txt"
        deps = "\n".join(f"package-{i}>=1.0" for i in range(200))
        req_file.write_text(deps)
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 200

    def test_handles_urls(self, reader: RequirementsTxtReader, tmp_path: Path) -> None:
        """Test that URL-based dependencies don't break parsing."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "git+https://github.com/user/repo.git@master\nclick>=8.0.0\n"
        )
        result = reader.read_project_info(req_file)
        # Should at least get click
        assert result.dependencies is not None
        assert result.dependencies.total_count >= 1

    def test_normalizes_dependency_names_to_lowercase(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test that dependency names are normalized to lowercase."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("Click>=8.0.0\nREQUESTS\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        deps = result.dependencies.dependencies
        assert all(dep.name.islower() for dep in deps)

    def test_very_long_dependency_line(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling of very long dependency specifications."""
        req_file = tmp_path / "requirements.txt"
        long_spec = "package-name>=" + "1.0.0" * 50
        req_file.write_text(f"{long_spec}\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count >= 1

    def test_handles_blank_lines_and_only_whitespace(
        self, reader: RequirementsTxtReader, tmp_path: Path
    ) -> None:
        """Test handling of lines with only whitespace."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("click>=8.0.0\n   \n\t\nrequests\n")
        result = reader.read_project_info(req_file)
        assert result.dependencies is not None
        assert result.dependencies.total_count == 2
