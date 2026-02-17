"""Tests for extended Git statistics functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from git.exc import GitCommandError

from statsvy.core.git_stats import GitStats


class TestGetLastCommitDate:
    """Test last commit date extraction."""

    def test_returns_iso_formatted_date(self) -> None:
        """Should return ISO 8601 formatted date from git log."""
        mock_repo = MagicMock()
        mock_repo.git.log.return_value = "2026-02-14T10:30:00+01:00"

        result = GitStats._get_last_commit_date(mock_repo)

        assert result == "2026-02-14T10:30:00+01:00"
        mock_repo.git.log.assert_called_once_with("-1", "--format=%cI")

    def test_returns_none_for_empty_output(self) -> None:
        """Should return None if no output from git log."""
        mock_repo = MagicMock()
        mock_repo.git.log.return_value = ""

        result = GitStats._get_last_commit_date(mock_repo)

        assert result is None

    def test_returns_none_on_git_command_error(self) -> None:
        """Should return None if git command fails."""
        mock_repo = MagicMock()
        mock_repo.git.log.side_effect = GitCommandError("log", 128)

        result = GitStats._get_last_commit_date(mock_repo)

        assert result is None


class TestGetBranches:
    """Test branch list extraction."""

    def test_returns_sorted_branch_list(self) -> None:
        """Should return sorted list of local branches."""
        mock_repo = MagicMock()
        mock_repo.git.branch.return_value = "* main\n  develop\n  feature-x"

        result = GitStats._get_branches(mock_repo)

        assert result is not None
        assert result == ["develop", "feature-x", "main"]

    def test_respects_max_branches_limit(self) -> None:
        """Should limit results to max_branches parameter."""
        mock_repo = MagicMock()
        branch_output = "\n".join([f"  branch-{i}" for i in range(10)])
        mock_repo.git.branch.return_value = branch_output

        result = GitStats._get_branches(mock_repo, max_branches=3)

        assert result is not None
        assert len(result) == 3
        assert result == ["branch-0", "branch-1", "branch-2"]

    def test_skips_remote_branches(self) -> None:
        """Should not include remote branches."""
        mock_repo = MagicMock()
        mock_repo.git.branch.return_value = "* main\n  remotes/origin/main\n  develop"

        result = GitStats._get_branches(mock_repo)

        assert result is not None
        assert result == ["develop", "main"]
        assert not any("remotes" in b for b in result)

    def test_returns_none_for_empty_output(self) -> None:
        """Should return None if no branches found."""
        mock_repo = MagicMock()
        mock_repo.git.branch.return_value = ""

        result = GitStats._get_branches(mock_repo)

        assert result is None

    def test_returns_none_on_git_command_error(self) -> None:
        """Should return None if git command fails."""
        mock_repo = MagicMock()
        mock_repo.git.branch.side_effect = GitCommandError("branch", 128)

        result = GitStats._get_branches(mock_repo)

        assert result is None


class TestGetCommitsPerMonth:
    """Test commits per month calculation."""

    def test_returns_none_for_zero_commits(self) -> None:
        """Should return None if repository has no commits."""
        mock_repo = MagicMock()
        mock_repo.git.rev_list.return_value = "0"

        result = GitStats._get_commits_per_month(mock_repo)

        assert result is None

    def test_returns_none_on_git_command_error(self) -> None:
        """Should return None if git command fails."""
        mock_repo = MagicMock()
        mock_repo.git.rev_list.side_effect = GitCommandError("rev-list", 128)

        result = GitStats._get_commits_per_month(mock_repo)

        assert result is None

    def test_returns_none_on_invalid_date_format(self) -> None:
        """Should return None if date parsing fails."""
        mock_repo = MagicMock()
        mock_repo.git.rev_list.return_value = "100"
        mock_repo.git.log.side_effect = GitCommandError("log", 128)

        result = GitStats._get_commits_per_month(mock_repo)

        assert result is None


class TestGetCommitsLast30Days:
    """Test recent commits counting."""

    def test_returns_commit_count_for_last_30_days(self) -> None:
        """Should return number of commits in last 30 days."""
        mock_repo = MagicMock()
        mock_repo.git.rev_list.return_value = "15"

        result = GitStats._get_commits_last_30_days(mock_repo)

        assert result == 15
        mock_repo.git.rev_list.assert_called_once_with(
            "--since=30 days ago", "--count", "HEAD"
        )

    def test_returns_zero_for_no_recent_commits(self) -> None:
        """Should return 0 if no commits in last 30 days."""
        mock_repo = MagicMock()
        mock_repo.git.rev_list.return_value = ""

        result = GitStats._get_commits_last_30_days(mock_repo)

        assert result == 0

    def test_returns_none_on_git_command_error(self) -> None:
        """Should return None if git command fails."""
        mock_repo = MagicMock()
        mock_repo.git.rev_list.side_effect = GitCommandError("rev-list", 128)

        result = GitStats._get_commits_last_30_days(mock_repo)

        assert result is None


class TestDetectRepositoryWithNewFields:
    """Test detect_repository including new fields."""

    def test_populates_all_git_fields_for_valid_repo(self) -> None:
        """Should populate all git info fields for valid repository."""
        with patch("statsvy.core.git_stats.Repo") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.bare = False
            mock_repo.remotes = [MagicMock(url="https://github.com/test/repo")]
            mock_repo.active_branch.name = "main"
            mock_repo.git.rev_list.return_value = "50"
            mock_repo.git.log.return_value = "John Doe\nJane Smith"
            mock_repo.git.branch.return_value = "* main\n  develop"
            mock_repo_class.return_value = mock_repo

            result = GitStats.detect_repository(Path("/test"))

            assert result.is_git_repo is True
            assert result.commit_count == 50
            assert result.contributors == ["Jane Smith", "John Doe"]
            assert result.current_branch == "main"
            assert result.remote_url == "https://github.com/test/repo"
            assert result.last_commit_date is not None
            assert result.branches is not None

    def test_non_repo_returns_all_none_fields(self) -> None:
        """Should return None for all fields for non-git directory."""
        with patch(
            "statsvy.core.git_stats.Repo",
            side_effect=GitCommandError("init", 128),
        ):
            result = GitStats.detect_repository(Path("/test"))

            assert result.is_git_repo is False
            assert result.current_branch is None
            assert result.commit_count is None
            assert result.contributors is None
            assert result.last_commit_date is None
            assert result.branches is None
            assert result.commits_per_month_all_time is None
            assert result.commits_last_30_days is None
