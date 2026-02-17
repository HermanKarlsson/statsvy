"""Tests for table formatter edge cases."""

from rich.table import Table

from statsvy.data.git_info import GitInfo
from statsvy.formatters.table_formatter import TableFormatter


class TestTableFormatterGitInfo:
    """Test table formatter git info display."""

    def test_create_git_table_with_no_contributors(self) -> None:
        """Test _create_git_table with None contributors."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url="https://github.com/user/repo.git",
            current_branch="main",
            commit_count=50,
            contributors=None,
            last_commit_date="2024-01-15",
            branches=["main", "develop"],
            commits_per_month_all_time=10.0,
            commits_last_30_days=5,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_empty_contributors_list(self) -> None:
        """Test _create_git_table with empty contributors list."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url="https://github.com/user/repo.git",
            current_branch="main",
            commit_count=50,
            contributors=[],
            last_commit_date="2024-01-15",
            branches=["main", "develop"],
            commits_per_month_all_time=10.0,
            commits_last_30_days=5,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_no_branches(self) -> None:
        """Test _create_git_table with None branches."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url="https://github.com/user/repo.git",
            current_branch="main",
            commit_count=50,
            contributors=["Alice", "Bob"],
            last_commit_date="2024-01-15",
            branches=None,
            commits_per_month_all_time=10.0,
            commits_last_30_days=5,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_empty_branches_list(self) -> None:
        """Test _create_git_table with empty branches list."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url="https://github.com/user/repo.git",
            current_branch="main",
            commit_count=50,
            contributors=["Alice"],
            last_commit_date="2024-01-15",
            branches=[],
            commits_per_month_all_time=10.0,
            commits_last_30_days=5,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_none_commit_count(self) -> None:
        """Test _create_git_table with None commit count."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url=None,
            current_branch="main",
            commit_count=None,
            contributors=["Alice"],
            last_commit_date="2024-01-15",
            branches=["main"],
            commits_per_month_all_time=10.0,
            commits_last_30_days=5,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_none_commits_per_month(self) -> None:
        """Test _create_git_table with None commits per month."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url="https://github.com/user/repo.git",
            current_branch="main",
            commit_count=50,
            contributors=["Alice"],
            last_commit_date="2024-01-15",
            branches=["main"],
            commits_per_month_all_time=None,
            commits_last_30_days=5,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_none_commits_30_days(self) -> None:
        """Test _create_git_table with None commits last 30 days."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=True,
            remote_url="https://github.com/user/repo.git",
            current_branch="main",
            commit_count=50,
            contributors=["Alice"],
            last_commit_date="2024-01-15",
            branches=["main"],
            commits_per_month_all_time=10.0,
            commits_last_30_days=None,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)

    def test_create_git_table_with_not_a_git_repo(self) -> None:
        """Test _create_git_table when not a git repository."""
        formatter = TableFormatter()
        git_info = GitInfo(
            is_git_repo=False,
            remote_url=None,
            current_branch=None,
            commit_count=None,
            contributors=None,
            last_commit_date=None,
            branches=None,
            commits_per_month_all_time=None,
            commits_last_30_days=None,
        )

        table = formatter._create_git_table(git_info)
        assert isinstance(table, Table)
