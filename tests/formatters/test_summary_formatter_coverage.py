"""Tests for summary formatter edge cases and missing coverage."""

from unittest.mock import patch

from statsvy.formatters.summary_formatter import SummaryFormatter


class TestSummaryFormatterLatestMetrics:
    """Test coverage for _print_latest_metrics method."""

    def test_print_latest_metrics_with_empty_dict(self) -> None:
        """Test _print_latest_metrics with empty metrics dict."""
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_latest_metrics({})
            # Should return early without printing anything
            mock_console.print.assert_not_called()

    def test_print_latest_metrics_with_none(self) -> None:
        """Test _print_latest_metrics with None."""
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_latest_metrics(None)  # type: ignore
            # Should return early without printing anything
            mock_console.print.assert_not_called()

    def test_print_latest_metrics_with_all_values(self) -> None:
        """Test _print_latest_metrics with all metric values present."""
        metrics = {
            "total_files": 42,
            "total_size": "2.5 MB",
            "total_lines": 15000,
        }
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_latest_metrics(metrics)
            # Should print 3 times for the metrics
            assert mock_console.print.call_count == 3

    def test_print_latest_metrics_with_missing_values(self) -> None:
        """Test _print_latest_metrics with missing metric values."""
        metrics = {"total_files": 42}
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_latest_metrics(metrics)
            # Should print 3 times (uses "-" for missing values)
            assert mock_console.print.call_count == 3
            # Check that "-" is used for missing values
            call_args_list = [str(call) for call in mock_console.print.call_args_list]
            assert any("-" in str(call) for call in call_args_list)

    def test_print_latest_metrics_with_zero_values(self) -> None:
        """Test _print_latest_metrics with zero values."""
        metrics = {
            "total_files": 0,
            "total_size": "0 B",
            "total_lines": 0,
        }
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_latest_metrics(metrics)
            assert mock_console.print.call_count == 3


class TestSummaryFormatterGitInfo:
    """Test coverage for _print_git_info method."""

    def test_print_git_info_with_none_git_info(self) -> None:
        """Test _print_git_info when git_info is None."""
        project_data = {"name": "test", "git_info": None}
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_git_info(project_data)
            mock_console.print.assert_not_called()

    def test_print_git_info_with_non_dict_git_info(self) -> None:
        """Test _print_git_info when git_info is not a dict."""
        project_data = {"name": "test", "git_info": "not a dict"}
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_git_info(project_data)
            mock_console.print.assert_not_called()

    def test_print_git_info_with_all_fields(self) -> None:
        """Test _print_git_info with all git fields populated."""
        project_data = {
            "git_info": {
                "is_git_repo": True,
                "current_branch": "main",
                "remote_url": "https://github.com/user/repo.git",
                "commit_count": 42,
                "contributors": ["Alice", "Bob"],
                "last_commit_date": "2024-01-15",
                "branches": ["main", "develop"],
                "commits_per_month_all_time": 5.2,
                "commits_last_30_days": 8,
            }
        }
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_git_info(project_data)
            # Should print 9 times (all git info fields)
            assert mock_console.print.call_count == 9

    def test_print_git_info_with_none_values(self) -> None:
        """Test _print_git_info when all git fields are None."""
        project_data = {
            "git_info": {
                "is_git_repo": False,
                "current_branch": None,
                "remote_url": None,
                "commit_count": None,
                "contributors": None,
                "last_commit_date": None,
                "branches": None,
                "commits_per_month_all_time": None,
                "commits_last_30_days": None,
            }
        }
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_git_info(project_data)
            # Should still print 9 times, using "-" for None values
            assert mock_console.print.call_count == 9

    def test_print_git_info_with_empty_contributors_list(self) -> None:
        """Test _print_git_info with empty contributors list."""
        project_data = {
            "git_info": {
                "is_git_repo": True,
                "current_branch": "main",
                "remote_url": None,
                "commit_count": None,
                "contributors": [],
                "last_commit_date": None,
                "branches": [],
                "commits_per_month_all_time": None,
                "commits_last_30_days": None,
            }
        }
        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter._print_git_info(project_data)
            assert mock_console.print.call_count == 9

    def test_format_with_all_parameters_populated(self) -> None:
        """Test full format method with all parameters."""
        project_data = {
            "name": "TestProject",
            "path": "/path/to/project",
            "date_added": "2024-01-01",
            "git_info": {
                "is_git_repo": True,
                "current_branch": "main",
                "remote_url": "https://github.com/user/repo.git",
                "commit_count": 100,
                "contributors": ["Alice", "Bob"],
                "last_commit_date": "2024-02-01",
                "branches": ["main", "dev"],
                "commits_per_month_all_time": 10.0,
                "commits_last_30_days": 5,
            },
        }
        history_data = [{"timestamp": "2024-01-01", "metrics": {}}]
        latest_metrics = {
            "total_files": 50,
            "total_size": "5 MB",
            "total_lines": 10000,
        }

        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter.format(
                project_data,
                history_data,
                "2024-02-14",
                latest_metrics,
            )
            # Should print multiple times
            assert mock_console.print.call_count > 0

    def test_format_with_minimal_parameters(self) -> None:
        """Test format method with minimal parameters."""
        project_data = {}
        history_data = []
        latest_metrics = {}

        with patch("statsvy.formatters.summary_formatter.console") as mock_console:
            SummaryFormatter.format(
                project_data,
                history_data,
                None,
                latest_metrics,
            )
            # Should still print something
            assert mock_console.print.call_count > 0
