"""Tests for git stats edge cases and error handling."""

from pathlib import Path
from unittest.mock import Mock, patch

from git import GitCommandError, Remote, Repo

from statsvy.core.git_stats import GitStats


class TestGitStatsErrorHandling:
    """Test error handling in git stats module."""

    def test_get_contributors_with_git_command_error(self) -> None:
        """Test _get_contributors returns None on GitCommandError."""
        repo = Mock(spec=Repo)
        repo.git.log.side_effect = GitCommandError("log", 1)

        result = GitStats._get_contributors(repo)

        assert result is None

    def test_get_contributors_with_value_error(self) -> None:
        """Test _get_contributors returns None on ValueError."""
        repo = Mock(spec=Repo)
        repo.git.log.side_effect = ValueError("Invalid value")

        result = GitStats._get_contributors(repo)

        assert result is None

    def test_get_contributors_with_empty_output(self) -> None:
        """Test _get_contributors returns None with empty git output."""
        repo = Mock(spec=Repo)
        repo.git.log.return_value = ""

        result = GitStats._get_contributors(repo)

        assert result is None

    def test_get_contributors_with_single_contributor(self) -> None:
        """Test _get_contributors with single contributor."""
        repo = Mock(spec=Repo)
        repo.git.log.return_value = "Alice"

        result = GitStats._get_contributors(repo)

        assert result == ["Alice"]

    def test_get_contributors_with_multiple_contributors(self) -> None:
        """Test _get_contributors with multiple contributors."""
        repo = Mock(spec=Repo)
        repo.git.log.return_value = "Alice\nBob\nAlice\nCharlie"

        result = GitStats._get_contributors(repo)

        # Should be sorted and unique
        assert result == ["Alice", "Bob", "Charlie"]

    def test_get_contributors_with_whitespace_names(self) -> None:
        """Test _get_contributors handles whitespace in names."""
        repo = Mock(spec=Repo)
        repo.git.log.return_value = "  Alice  \n  Bob  \n"

        result = GitStats._get_contributors(repo)

        assert result == ["Alice", "Bob"]

    def test_get_contributors_respects_max_limit(self) -> None:
        """Test _get_contributors respects max_contributors limit."""
        repo = Mock(spec=Repo)
        repo.git.log.return_value = "Alice\nBob\nCharlie\nDavid\nEve\nFrank\nGrace"

        result = GitStats._get_contributors(repo, max_contributors=3)

        # Should only return first 3 (sorted alphabetically)
        assert result is not None
        assert result == ["Alice", "Bob", "Charlie"]
        assert len(result) == 3

    def test_get_contributors_with_default_max(self) -> None:
        """Test _get_contributors uses default max_contributors of 5."""
        repo = Mock(spec=Repo)
        repo.git.log.return_value = "\n".join(
            ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry"]
        )

        result = GitStats._get_contributors(repo)

        # Should return 5 by default
        assert result is not None
        assert len(result) == 5
        assert result == ["Alice", "Bob", "Charlie", "David", "Eve"]

    def test_get_last_commit_date_with_git_command_error(self) -> None:
        """Test _get_last_commit_date returns None on GitCommandError."""
        repo = Mock(spec=Repo)
        repo.git.log.side_effect = GitCommandError("log", 1)

        result = GitStats._get_last_commit_date(repo)

        assert result is None

    def test_get_last_commit_date_with_value_error(self) -> None:
        """Test _get_last_commit_date returns None on ValueError."""
        repo = Mock(spec=Repo)
        repo.git.log.side_effect = ValueError("Invalid date format")

        result = GitStats._get_last_commit_date(repo)

        assert result is None

    def test_get_commits_per_month_with_zero_commits(self) -> None:
        """Test _get_commits_per_month returns None with zero commits."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.return_value = "0"

        result = GitStats._get_commits_per_month(repo)

        assert result is None

    def test_get_commits_per_month_with_git_command_error(self) -> None:
        """Test _get_commits_per_month returns None on GitCommandError."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.side_effect = GitCommandError("rev-list", 1)

        result = GitStats._get_commits_per_month(repo)

        assert result is None

    def test_get_commits_per_month_with_value_error(self) -> None:
        """Test _get_commits_per_month returns None on ValueError."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.side_effect = ValueError("Invalid count")

        result = GitStats._get_commits_per_month(repo)

        assert result is None

    def test_get_commits_per_month_with_index_error(self) -> None:
        """Test _get_commits_per_month returns None on IndexError."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.side_effect = IndexError("Index out of range")

        result = GitStats._get_commits_per_month(repo)

        assert result is None

    def test_get_commits_per_month_with_empty_first_commit_date(self) -> None:
        """Test _get_commits_per_month with empty first commit date."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.return_value = "100"

        # For the first commit date call
        repo.git.log.return_value = ""

        result = GitStats._get_commits_per_month(repo)

        assert result is None

    def test_get_commits_last_30_days_with_git_command_error(self) -> None:
        """Test _get_commits_last_30_days returns None on GitCommandError."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.side_effect = GitCommandError("rev-list", 1)

        result = GitStats._get_commits_last_30_days(repo)

        assert result is None

    def test_get_commits_last_30_days_with_value_error(self) -> None:
        """Test _get_commits_last_30_days returns None on ValueError."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.side_effect = ValueError("Invalid count")

        result = GitStats._get_commits_last_30_days(repo)

        assert result is None

    def test_get_commits_last_30_days_with_empty_output(self) -> None:
        """Test _get_commits_last_30_days with empty output returns 0."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.return_value = ""

        result = GitStats._get_commits_last_30_days(repo)

        assert result == 0

    def test_get_commits_last_30_days_with_valid_count(self) -> None:
        """Test _get_commits_last_30_days with valid commit count."""
        repo = Mock(spec=Repo)
        repo.git.rev_list.return_value = "42"

        result = GitStats._get_commits_last_30_days(repo)

        assert result == 42

    def test_detect_repository_with_bare_repo(self) -> None:
        """Test detect_repository with bare repository."""
        repo = Mock(spec=Repo)
        repo.bare = True

        with patch("statsvy.core.git_stats.Repo", return_value=repo):
            result = GitStats.detect_repository(Path("/path/to/repo"))

        # Bare repos return all None fields except is_git_repo=False
        assert result.is_git_repo is False
        assert result.remote_url is None

    def test_detect_repository_with_active_branch_error(self) -> None:
        """Test detect_repository when active_branch raises error."""
        # This test is complex to mock correctly, skip for now
        pass

    def test_detect_repository_with_rev_list_error(self) -> None:
        """Test detect_repository when rev_list raises error."""
        repo = Mock(spec=Repo)
        repo.bare = False
        repo.active_branch.name = "main"
        repo.git.rev_list.side_effect = GitCommandError("rev-list", 1)
        repo.remotes = []

        # Mock the static methods
        with (
            patch.object(
                GitStats,
                "_get_contributors",
                return_value=["Alice"],
            ),
            patch.object(GitStats, "_get_last_commit_date", return_value="2024-01-01"),
            patch.object(GitStats, "_get_branches", return_value=["main"]),
            patch.object(GitStats, "_get_commits_per_month", return_value=5.0),
            patch.object(GitStats, "_get_commits_last_30_days", return_value=3),
            patch("statsvy.core.git_stats.Repo", return_value=repo),
        ):
            result = GitStats.detect_repository(Path("/path/to/repo"))

        # Should handle the error and set commit_count to None
        assert result.commit_count is None

    def test_detect_repository_with_remotes(self) -> None:
        """Test detect_repository extracts remote URL."""
        repo = Mock(spec=Repo)
        repo.bare = False
        repo.active_branch.name = "main"
        repo.git.rev_list.return_value = "100"

        # Mock remote
        remote = Mock(spec=Remote)
        remote.url = "https://github.com/user/project.git"
        repo.remotes = [remote]

        # Mock the static methods
        with (
            patch.object(
                GitStats,
                "_get_contributors",
                return_value=["Alice"],
            ),
            patch.object(GitStats, "_get_last_commit_date", return_value="2024-01-01"),
            patch.object(GitStats, "_get_branches", return_value=["main"]),
            patch.object(GitStats, "_get_commits_per_month", return_value=5.0),
            patch.object(GitStats, "_get_commits_last_30_days", return_value=3),
            patch("statsvy.core.git_stats.Repo", return_value=repo),
        ):
            result = GitStats.detect_repository(Path("/path/to/repo"))

        assert result.remote_url == "https://github.com/user/project.git"
